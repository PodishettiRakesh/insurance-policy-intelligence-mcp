"""Eligibility evaluation service."""

import re
from typing import Any, Dict, List

from app.catalogue import get_catalogue
from app.models import (
    CheckEligibilityRequest,
    EligibilityCheckResult,
    EligibilityCriterionResult,
)


class EligibilityError(Exception):
    """Exception raised for eligibility evaluation errors."""
    pass


def check_eligibility(policy_id: str, applicant_info: Dict[str, Any]) -> EligibilityCheckResult:
    """
    Evaluate whether an applicant meets a policy's eligibility criteria.

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

    # Evaluate each eligibility criterion
    criteria_results = []
    for criterion in policy.eligibility.requirements:
        result = _evaluate_criterion(criterion, request.applicant_info)
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

    return EligibilityCheckResult(
        success=True,
        policy_id=policy.policy_id,
        policy_title=policy.title,
        overall_status=overall_status,
        criteria_results=criteria_results,
        summary=summary
    )


def _evaluate_criterion(criterion: str, applicant_info: Dict[str, Any]) -> EligibilityCriterionResult:
    """
    Evaluate a single eligibility criterion against applicant information.

    Args:
        criterion: The eligibility criterion text
        applicant_info: Dictionary containing applicant information

    Returns:
        EligibilityCriterionResult with evaluation details
    """
    criterion_lower = criterion.lower()

    # Pattern 1: Minimum annual turnover
    turnover_match = re.search(
        r"minimum\s+annual\s+(?:export\s+)?turnover\s+of\s+([a-z]+)\s+([\d.]+)\s*(million|billion|thousand|lakh|crore)?",
        criterion_lower,
        re.IGNORECASE
    )
    if turnover_match:
        return _evaluate_turnover_requirement(
            criterion,
            turnover_match,
            applicant_info
        )

    # Pattern 2: Business registration duration
    registration_match = re.search(
        r"business\s+must\s+be\s+registered\s+for\s+at\s+least\s+(\d+)\s+years?",
        criterion_lower
    )
    if registration_match:
        return _evaluate_registration_requirement(
            criterion,
            int(registration_match.group(1)),
            applicant_info
        )

    # Pattern 3: Export business duration
    export_years_match = re.search(
        r"established\s+export\s+business\s*\(?(\d+)\+\s*years?\)?",
        criterion_lower
    )
    if export_years_match:
        return _evaluate_export_years_requirement(
            criterion,
            int(export_years_match.group(1)),
            applicant_info
        )

    # Pattern 4: Valid export license
    if "valid export license" in criterion_lower or "export license" in criterion_lower:
        return _evaluate_license_requirement(
            criterion,
            "export_license",
            applicant_info
        )

    # Pattern 5: Audited financial statements (check before general financial statements)
    if "audited financial statements" in criterion_lower:
        return _evaluate_document_requirement(
            criterion,
            "audited_financial_statements",
            applicant_info
        )

    # Pattern 6: Financial statements
    if "financial statements" in criterion_lower:
        return _evaluate_document_requirement(
            criterion,
            "financial_statements",
            applicant_info
        )

    # Pattern 7: Buyer credit rating
    if "credit rating" in criterion_lower:
        return _evaluate_credit_rating_requirement(
            criterion,
            applicant_info
        )

    # Pattern 8: Maximum exposure limit
    if "maximum exposure limit" in criterion_lower:
        return _evaluate_exposure_requirement(
            criterion,
            applicant_info
        )

    # Pattern 9: Annual turnover under threshold
    under_turnover_match = re.search(
        r"annual\s+turnover\s+under\s+([a-z]+)\s+([\d.]+)\s*(million|billion|thousand|lakh|crore)?",
        criterion_lower
    )
    if under_turnover_match:
        return _evaluate_under_turnover_requirement(
            criterion,
            under_turnover_match,
            applicant_info
        )

    # Pattern 10: Diverse customer base
    if "diverse customer base" in criterion_lower or "no single buyer" in criterion_lower:
        return _evaluate_customer_diversity_requirement(
            criterion,
            applicant_info
        )

    # Pattern 11: Government contract
    if "government contract" in criterion_lower or "valid government contract" in criterion_lower:
        return _evaluate_document_requirement(
            criterion,
            "government_contract",
            applicant_info
        )

    # Pattern 12: Compliance with regulations
    if "compliance" in criterion_lower:
        return _evaluate_compliance_requirement(
            criterion,
            applicant_info
        )

    # Pattern 13: Multi-country export portfolio
    if "multi-country" in criterion_lower or "both domestic and export" in criterion_lower:
        return _evaluate_multi_region_requirement(
            criterion,
            applicant_info
        )

    # Pattern 14: Existing policyholders only
    if "existing policyholders only" in criterion_lower:
        return _evaluate_existing_policyholder_requirement(
            criterion,
            applicant_info
        )

    # Pattern 15: General document/information requirements
    if "required" in criterion_lower or "must be provided" in criterion_lower:
        return _evaluate_general_requirement(
            criterion,
            applicant_info
        )

    # If no pattern matches, return undetermined
    return EligibilityCriterionResult(
        criterion=criterion,
        status="undetermined",
        reason="This criterion could not be automatically evaluated. Manual review required."
    )


def _evaluate_turnover_requirement(
    criterion: str,
    match: re.Match,
    applicant_info: Dict[str, Any]
) -> EligibilityCriterionResult:
    """Evaluate minimum turnover requirement."""
    currency = match.group(1).upper()
    value = float(match.group(2))
    multiplier = match.group(3)

    # Convert to numeric value
    multiplier_map = {
        "million": 1_000_000,
        "billion": 1_000_000_000,
        "thousand": 1_000,
        "lakh": 100_000,
        "crore": 10_000_000
    }
    threshold = value * multiplier_map.get(multiplier, 1)

    # Check applicant info for turnover
    turnover_fields = [
        "annual_turnover",
        "turnover",
        "revenue",
        "annual_revenue"
    ]

    for field in turnover_fields:
        if field in applicant_info:
            applicant_turnover = applicant_info[field]
            if isinstance(applicant_turnover, (int, float)):
                if applicant_turnover >= threshold:
                    return EligibilityCriterionResult(
                        criterion=criterion,
                        status="passed",
                        reason=f"Applicant's annual turnover ({applicant_turnover:,.0f}) meets the minimum requirement of {threshold:,.0f}"
                    )
                else:
                    return EligibilityCriterionResult(
                        criterion=criterion,
                        status="failed",
                        reason=f"Applicant's annual turnover ({applicant_turnover:,.0f}) is below the minimum requirement of {threshold:,.0f}"
                    )

    return EligibilityCriterionResult(
        criterion=criterion,
        status="undetermined",
        reason="Annual turnover information not provided in applicant data"
    )


def _evaluate_under_turnover_requirement(
    criterion: str,
    match: re.Match,
    applicant_info: Dict[str, Any]
) -> EligibilityCriterionResult:
    """Evaluate turnover under threshold requirement."""
    currency = match.group(1).upper()
    value = float(match.group(2))
    multiplier = match.group(3)

    multiplier_map = {
        "million": 1_000_000,
        "billion": 1_000_000_000,
        "thousand": 1_000,
        "lakh": 100_000,
        "crore": 10_000_000
    }
    threshold = value * multiplier_map.get(multiplier, 1)

    turnover_fields = [
        "annual_turnover",
        "turnover",
        "revenue",
        "annual_revenue"
    ]

    for field in turnover_fields:
        if field in applicant_info:
            applicant_turnover = applicant_info[field]
            if isinstance(applicant_turnover, (int, float)):
                if applicant_turnover < threshold:
                    return EligibilityCriterionResult(
                        criterion=criterion,
                        status="passed",
                        reason=f"Applicant's annual turnover ({applicant_turnover:,.0f}) is under the threshold of {threshold:,.0f}"
                    )
                else:
                    return EligibilityCriterionResult(
                        criterion=criterion,
                        status="failed",
                        reason=f"Applicant's annual turnover ({applicant_turnover:,.0f}) exceeds the threshold of {threshold:,.0f}"
                    )

    return EligibilityCriterionResult(
        criterion=criterion,
        status="undetermined",
        reason="Annual turnover information not provided in applicant data"
    )


def _evaluate_registration_requirement(
    criterion: str,
    required_years: int,
    applicant_info: Dict[str, Any]
) -> EligibilityCriterionResult:
    """Evaluate business registration duration requirement."""
    years_fields = [
        "business_age_years",
        "registration_years",
        "years_in_business",
        "years_registered"
    ]

    for field in years_fields:
        if field in applicant_info:
            years = applicant_info[field]
            if isinstance(years, (int, float)):
                if years >= required_years:
                    return EligibilityCriterionResult(
                        criterion=criterion,
                        status="passed",
                        reason=f"Business has been registered for {years} years, meeting the {required_years} year requirement"
                    )
                else:
                    return EligibilityCriterionResult(
                        criterion=criterion,
                        status="failed",
                        reason=f"Business has been registered for {years} years, which is less than the required {required_years} years"
                    )

    return EligibilityCriterionResult(
        criterion=criterion,
        status="undetermined",
        reason="Business registration duration not provided in applicant data"
    )


def _evaluate_export_years_requirement(
    criterion: str,
    required_years: int,
    applicant_info: Dict[str, Any]
) -> EligibilityCriterionResult:
    """Evaluate export business duration requirement."""
    years_fields = [
        "export_years",
        "years_in_export",
        "export_business_age"
    ]

    for field in years_fields:
        if field in applicant_info:
            years = applicant_info[field]
            if isinstance(years, (int, float)):
                if years >= required_years:
                    return EligibilityCriterionResult(
                        criterion=criterion,
                        status="passed",
                        reason=f"Export business has been established for {years} years, meeting the {required_years}+ year requirement"
                    )
                else:
                    return EligibilityCriterionResult(
                        criterion=criterion,
                        status="failed",
                        reason=f"Export business has been established for {years} years, which is less than the required {required_years}+ years"
                    )

    return EligibilityCriterionResult(
        criterion=criterion,
        status="undetermined",
        reason="Export business duration not provided in applicant data"
    )


def _evaluate_license_requirement(
    criterion: str,
    license_type: str,
    applicant_info: Dict[str, Any]
) -> EligibilityCriterionResult:
    """Evaluate license requirement."""
    if license_type in applicant_info:
        has_license = applicant_info[license_type]
        if isinstance(has_license, bool):
            if has_license:
                return EligibilityCriterionResult(
                    criterion=criterion,
                    status="passed",
                    reason=f"Applicant has a valid {license_type.replace('_', ' ')}"
                )
            else:
                return EligibilityCriterionResult(
                    criterion=criterion,
                    status="failed",
                    reason=f"Applicant does not have a valid {license_type.replace('_', ' ')}"
                )
        elif isinstance(has_license, str) and has_license.lower() in ["yes", "true", "valid"]:
            return EligibilityCriterionResult(
                criterion=criterion,
                status="passed",
                reason=f"Applicant has a valid {license_type.replace('_', ' ')}"
            )

    return EligibilityCriterionResult(
        criterion=criterion,
        status="undetermined",
        reason=f"{license_type.replace('_', ' ')} information not provided in applicant data"
    )


def _evaluate_document_requirement(
    criterion: str,
    document_type: str,
    applicant_info: Dict[str, Any]
) -> EligibilityCriterionResult:
    """Evaluate document requirement."""
    if document_type in applicant_info:
        has_document = applicant_info[document_type]
        if isinstance(has_document, bool):
            if has_document:
                return EligibilityCriterionResult(
                    criterion=criterion,
                    status="passed",
                    reason=f"Applicant has provided {document_type.replace('_', ' ')}"
                )
            else:
                return EligibilityCriterionResult(
                    criterion=criterion,
                    status="failed",
                    reason=f"Applicant has not provided {document_type.replace('_', ' ')}"
                )
        elif isinstance(has_document, str) and has_document.lower() in ["yes", "true", "provided"]:
            return EligibilityCriterionResult(
                criterion=criterion,
                status="passed",
                reason=f"Applicant has provided {document_type.replace('_', ' ')}"
            )

    return EligibilityCriterionResult(
        criterion=criterion,
        status="undetermined",
        reason=f"{document_type.replace('_', ' ')} information not provided in applicant data"
    )


def _evaluate_credit_rating_requirement(
    criterion: str,
    applicant_info: Dict[str, Any]
) -> EligibilityCriterionResult:
    """Evaluate credit rating requirement."""
    rating_fields = [
        "credit_rating",
        "buyer_credit_rating",
        "credit_score"
    ]

    for field in rating_fields:
        if field in applicant_info:
            rating = applicant_info[field]
            if rating and (isinstance(rating, str) and rating.strip()):
                return EligibilityCriterionResult(
                    criterion=criterion,
                    status="passed",
                    reason=f"Applicant has a credit rating assessment: {rating}"
                )

    return EligibilityCriterionResult(
        criterion=criterion,
        status="undetermined",
        reason="Credit rating information not provided in applicant data"
    )


def _evaluate_exposure_requirement(
    criterion: str,
    applicant_info: Dict[str, Any]
) -> EligibilityCriterionResult:
    """Evaluate exposure limit requirement."""
    if "exposure_limit" in applicant_info or "max_exposure" in applicant_info:
        exposure = applicant_info.get("exposure_limit") or applicant_info.get("max_exposure")
        if exposure and (isinstance(exposure, (int, float)) or isinstance(exposure, str) and exposure.strip()):
            return EligibilityCriterionResult(
                criterion=criterion,
                status="passed",
                reason=f"Maximum exposure limit has been defined: {exposure}"
            )

    return EligibilityCriterionResult(
        criterion=criterion,
        status="undetermined",
        reason="Exposure limit information not provided in applicant data"
    )


def _evaluate_customer_diversity_requirement(
    criterion: str,
    applicant_info: Dict[str, Any]
) -> EligibilityCriterionResult:
    """Evaluate customer diversity requirement."""
    if "customer_concentration" in applicant_info:
        concentration = applicant_info["customer_concentration"]
        if isinstance(concentration, (int, float)):
            if concentration <= 30:
                return EligibilityCriterionResult(
                    criterion=criterion,
                    status="passed",
                    reason=f"Customer concentration is {concentration}%, meeting the requirement (no single buyer > 30%)"
                )
            else:
                return EligibilityCriterionResult(
                    criterion=criterion,
                    status="failed",
                    reason=f"Customer concentration is {concentration}%, exceeding the maximum allowed 30%"
                )

    if "largest_buyer_percentage" in applicant_info:
        percentage = applicant_info["largest_buyer_percentage"]
        if isinstance(percentage, (int, float)):
            if percentage <= 30:
                return EligibilityCriterionResult(
                    criterion=criterion,
                    status="passed",
                    reason=f"Largest buyer represents {percentage}% of turnover, meeting the requirement"
                )
            else:
                return EligibilityCriterionResult(
                    criterion=criterion,
                    status="failed",
                    reason=f"Largest buyer represents {percentage}% of turnover, exceeding the maximum allowed 30%"
                )

    return EligibilityCriterionResult(
        criterion=criterion,
        status="undetermined",
        reason="Customer concentration information not provided in applicant data"
    )


def _evaluate_compliance_requirement(
    criterion: str,
    applicant_info: Dict[str, Any]
) -> EligibilityCriterionResult:
    """Evaluate compliance requirement."""
    compliance_fields = [
        "compliance_status",
        "regulatory_compliance",
        "is_compliant"
    ]

    for field in compliance_fields:
        if field in applicant_info:
            compliance = applicant_info[field]
            if isinstance(compliance, bool):
                if compliance:
                    return EligibilityCriterionResult(
                        criterion=criterion,
                        status="passed",
                        reason="Applicant is compliant with required regulations"
                    )
                else:
                    return EligibilityCriterionResult(
                        criterion=criterion,
                        status="failed",
                        reason="Applicant is not compliant with required regulations"
                    )
            elif isinstance(compliance, str) and compliance.lower() in ["yes", "true", "compliant"]:
                return EligibilityCriterionResult(
                    criterion=criterion,
                    status="passed",
                    reason="Applicant is compliant with required regulations"
                )

    return EligibilityCriterionResult(
        criterion=criterion,
        status="undetermined",
        reason="Compliance status information not provided in applicant data"
    )


def _evaluate_multi_region_requirement(
    criterion: str,
    applicant_info: Dict[str, Any]
) -> EligibilityCriterionResult:
    """Evaluate multi-region operations requirement."""
    if "operating_regions" in applicant_info:
        regions = applicant_info["operating_regions"]
        if isinstance(regions, list) and len(regions) >= 2:
            return EligibilityCriterionResult(
                criterion=criterion,
                status="passed",
                reason=f"Applicant operates in {len(regions)} regions, meeting the multi-region requirement"
            )
        elif isinstance(regions, list):
            return EligibilityCriterionResult(
                criterion=criterion,
                status="failed",
                reason=f"Applicant operates in only {len(regions)} region, which does not meet the multi-region requirement"
            )

    if "has_domestic_operations" in applicant_info and "has_export_operations" in applicant_info:
        domestic = applicant_info["has_domestic_operations"]
        export = applicant_info["has_export_operations"]
        if domestic and export:
            return EligibilityCriterionResult(
                criterion=criterion,
                status="passed",
                reason="Applicant has both domestic and export operations"
            )
        else:
            return EligibilityCriterionResult(
                criterion=criterion,
                status="failed",
                reason="Applicant does not have both domestic and export operations"
            )

    return EligibilityCriterionResult(
        criterion=criterion,
        status="undetermined",
        reason="Multi-region operations information not provided in applicant data"
    )


def _evaluate_existing_policyholder_requirement(
    criterion: str,
    applicant_info: Dict[str, Any]
) -> EligibilityCriterionResult:
    """Evaluate existing policyholder requirement."""
    if "is_existing_policyholder" in applicant_info:
        is_existing = applicant_info["is_existing_policyholder"]
        if isinstance(is_existing, bool):
            if is_existing:
                return EligibilityCriterionResult(
                    criterion=criterion,
                    status="passed",
                    reason="Applicant is an existing policyholder"
                )
            else:
                return EligibilityCriterionResult(
                    criterion=criterion,
                    status="failed",
                    reason="Applicant is not an existing policyholder"
                )

    return EligibilityCriterionResult(
        criterion=criterion,
        status="undetermined",
        reason="Existing policyholder status not provided in applicant data"
    )


def _evaluate_general_requirement(
    criterion: str,
    applicant_info: Dict[str, Any]
) -> EligibilityCriterionResult:
    """Evaluate general requirement (buyer info, contract terms, etc.)."""
    # Try to infer relevant field names from the criterion
    criterion_lower = criterion.lower()

    if "buyer information" in criterion_lower or "buyer credit history" in criterion_lower:
        if "buyer_information" in applicant_info or "buyer_credit_history" in applicant_info:
            return EligibilityCriterionResult(
                criterion=criterion,
                status="passed",
                reason="Buyer information has been provided"
            )
        return EligibilityCriterionResult(
            criterion=criterion,
            status="undetermined",
            reason="Buyer information not provided in applicant data"
        )

    if "contract duration" in criterion_lower or "contract terms" in criterion_lower:
        if "contract_duration" in applicant_info or "contract_terms" in applicant_info:
            return EligibilityCriterionResult(
                criterion=criterion,
                status="passed",
                reason="Contract terms have been documented"
            )
        return EligibilityCriterionResult(
            criterion=criterion,
            status="undetermined",
            reason="Contract terms information not provided in applicant data"
        )

    if "project plan" in criterion_lower or "milestones" in criterion_lower:
        if "project_plan" in applicant_info or "milestones" in applicant_info:
            return EligibilityCriterionResult(
                criterion=criterion,
                status="passed",
                reason="Project plan and milestones have been documented"
            )
        return EligibilityCriterionResult(
            criterion=criterion,
            status="undetermined",
            reason="Project plan and milestones information not provided in applicant data"
        )

    if "enhanced due diligence" in criterion_lower or "due diligence" in criterion_lower:
        if "due_diligence_completed" in applicant_info:
            if applicant_info["due_diligence_completed"]:
                return EligibilityCriterionResult(
                    criterion=criterion,
                    status="passed",
                    reason="Enhanced due diligence has been completed"
                )
            return EligibilityCriterionResult(
                criterion=criterion,
                status="failed",
                reason="Enhanced due diligence has not been completed"
            )
        return EligibilityCriterionResult(
            criterion=criterion,
            status="undetermined",
            reason="Due diligence status not provided in applicant data"
        )

    # Default to undetermined for unrecognised general requirements
    return EligibilityCriterionResult(
        criterion=criterion,
        status="undetermined",
        reason="This criterion could not be automatically evaluated. Manual review required."
    )


def _generate_summary(
    overall_status: str,
    passed: int,
    failed: int,
    undetermined: int,
    total: int
) -> str:
    """Generate a human-readable summary of the eligibility check."""
    if total == 0:
        return "No eligibility criteria to evaluate."

    parts = []
    if passed > 0:
        parts.append(f"{passed} passed")
    if failed > 0:
        parts.append(f"{failed} failed")
    if undetermined > 0:
        parts.append(f"{undetermined} undetermined")

    criteria_summary = ", ".join(parts)

    if overall_status == "eligible":
        return f"Eligible: All {total} criteria have been met ({criteria_summary})."
    elif overall_status == "ineligible":
        return f"Ineligible: {failed} of {total} criteria were not met ({criteria_summary})."
    else:  # undetermined
        return f"Undetermined: {passed} of {total} criteria were met, but {undetermined} could not be evaluated ({criteria_summary}). Additional information may be required."
