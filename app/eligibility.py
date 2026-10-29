"""Eligibility evaluation service with explicit rule engine."""

from typing import Any, Dict, List

from app.catalogue import get_catalogue
from app.models import (
    CheckEligibilityRequest,
    EligibilityCheckResult,
    EligibilityCriterionResult,
)
from app.rule_parser import parse_criteria_to_rules
from app.rule_engine import RuleEngine
from app.evidence_tracker import EvidenceTracker


class EligibilityError(Exception):
    """Exception raised for eligibility evaluation errors."""
    pass


def check_eligibility(policy_id: str, applicant_info: Dict[str, Any]) -> EligibilityCheckResult:
    """
    Evaluate whether an applicant meets a policy's eligibility criteria using explicit rules.

    Args:
        policy_id: The policy ID to check eligibility for
        applicant_info: Dictionary containing applicant information for evaluation

    Returns:
        EligibilityCheckResult with detailed evaluation results

    Raises:
        EligibilityError: If policy ID is invalid or evaluation fails
    """
    # Validate request
    try:
        request = CheckEligibilityRequest(
            policy_id=policy_id,
            applicant_info=applicant_info
        )
    except Exception as e:
        raise EligibilityError(str(e))

    # Get the policy
    catalogue = get_catalogue()
    catalogue_dict = {p.policy_id: p for p in catalogue}

    if request.policy_id not in catalogue_dict:
        raise EligibilityError(f"Policy ID not found: {request.policy_id}")

    policy = catalogue_dict[request.policy_id]

    # Check if policy has eligibility criteria
    if not policy.eligibility or not policy.eligibility.requirements:
        return EligibilityCheckResult(
            success=True,
            policy_id=policy.policy_id,
            policy_title=policy.title,
            overall_status="undetermined",
            criteria_results=[],
            summary="This policy has no explicit eligibility criteria defined. Eligibility cannot be determined from the available data."
        )

    # Parse criteria into explicit rules
    rules = parse_criteria_to_rules(policy.eligibility.requirements)

    # Evaluate each rule using the rule engine
    rule_engine = RuleEngine()
    criteria_results = []
    for rule in rules:
        result = rule_engine.evaluate_rule(rule, request.applicant_info)
        criteria_results.append(result)

    # Determine overall status
    passed_count = sum(1 for r in criteria_results if r.status == "passed")
    failed_count = sum(1 for r in criteria_results if r.status == "failed")
    undetermined_count = sum(1 for r in criteria_results if r.status == "undetermined")

    if failed_count > 0:
        overall_status = "ineligible"
    elif undetermined_count > 0:
        overall_status = "undetermined"
    else:
        overall_status = "eligible"

    # Generate summary
    summary = _generate_summary(
        overall_status,
        passed_count,
        failed_count,
        undetermined_count,
        len(criteria_results)
    )

    # Add evidence metadata
    evidence_tracker = EvidenceTracker()
    sources = []

    # Add source reference for policy eligibility criteria
    if policy.eligibility and policy.eligibility.requirements:
        sources.append(evidence_tracker.create_source_reference(
            policy_id=policy.policy_id,
            field="eligibility.requirements",
            value=policy.eligibility.requirements,
            display_value=f"{len(policy.eligibility.requirements)} eligibility criteria"
        ))

    evidence_metadata = evidence_tracker.create_evidence_metadata(sources)

    return EligibilityCheckResult(
        success=True,
        policy_id=policy.policy_id,
        policy_title=policy.title,
        overall_status=overall_status,
        criteria_results=criteria_results,
        summary=summary,
        evidence_metadata=evidence_metadata
    )


def _generate_summary(
    overall_status: str,
    passed_count: int,
    failed_count: int,
    undetermined_count: int,
    total_count: int
) -> str:
    """Generate a human-readable summary of the eligibility check."""
    if overall_status == "eligible":
        return f"Eligible: All {total_count} criteria have been met ({passed_count} passed)."
    elif overall_status == "ineligible":
        return f"Ineligible: {failed_count} of {total_count} criteria were not met ({passed_count} passed, {failed_count} failed, {undetermined_count} undetermined)."
    else:  # undetermined
        if passed_count == 0 and undetermined_count == total_count:
            return f"Undetermined: {total_count} criteria could not be evaluated. Additional information may be required."
        elif failed_count == 0:
            return f"Undetermined: {passed_count} of {total_count} criteria were met, but {undetermined_count} could not be evaluated. Additional information may be required."
        else:
            return f"Undetermined: {passed_count} passed, {failed_count} failed, {undetermined_count} undetermined. Review required."
