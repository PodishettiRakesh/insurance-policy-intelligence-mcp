"""Deterministic rule engine for evaluating eligibility rules."""

from typing import Dict, Any
from app.models import (
    EligibilityRule,
    MinimumTurnoverRule,
    MaximumTurnoverRule,
    MinimumYearsRule,
    DocumentRequiredRule,
    LicenseRequiredRule,
    CreditRatingRule,
    ExposureLimitRule,
    CustomerDiversityRule,
    ComplianceRule,
    MultiRegionRule,
    ExistingPolicyholderRule,
    UnknownRule,
    EligibilityCriterionResult,
)


class RuleEngine:
    """Deterministic rule engine for evaluating eligibility rules."""

    def evaluate_rule(
        self,
        rule: EligibilityRule,
        applicant_info: Dict[str, Any]
    ) -> EligibilityCriterionResult:
        """
        Evaluate a single rule against applicant information.

        Args:
            rule: The eligibility rule to evaluate
            applicant_info: Dictionary containing applicant information

        Returns:
            EligibilityCriterionResult with evaluation details
        """
        # Dispatch to specific rule evaluator based on rule type
        if isinstance(rule, MinimumTurnoverRule):
            return self._evaluate_minimum_turnover(rule, applicant_info)
        elif isinstance(rule, MaximumTurnoverRule):
            return self._evaluate_maximum_turnover(rule, applicant_info)
        elif isinstance(rule, MinimumYearsRule):
            return self._evaluate_minimum_years(rule, applicant_info)
        elif isinstance(rule, DocumentRequiredRule):
            return self._evaluate_document_required(rule, applicant_info)
        elif isinstance(rule, LicenseRequiredRule):
            return self._evaluate_license_required(rule, applicant_info)
        elif isinstance(rule, CreditRatingRule):
            return self._evaluate_credit_rating(rule, applicant_info)
        elif isinstance(rule, ExposureLimitRule):
            return self._evaluate_exposure_limit(rule, applicant_info)
        elif isinstance(rule, CustomerDiversityRule):
            return self._evaluate_customer_diversity(rule, applicant_info)
        elif isinstance(rule, ComplianceRule):
            return self._evaluate_compliance(rule, applicant_info)
        elif isinstance(rule, MultiRegionRule):
            return self._evaluate_multi_region(rule, applicant_info)
        elif isinstance(rule, ExistingPolicyholderRule):
            return self._evaluate_existing_policyholder(rule, applicant_info)
        elif isinstance(rule, UnknownRule):
            return self._evaluate_unknown(rule, applicant_info)
        else:
            return EligibilityCriterionResult(
                criterion=rule.original_text,
                status="undetermined",
                reason=f"Unsupported rule type: {rule.rule_type}"
            )

    def _evaluate_minimum_turnover(
        self,
        rule: MinimumTurnoverRule,
        applicant_info: Dict[str, Any]
    ) -> EligibilityCriterionResult:
        """Evaluate minimum turnover rule."""
        # Check for turnover in any of the required fields
        for field in rule.required_fields:
            if field in applicant_info:
                value = applicant_info[field]
                if isinstance(value, (int, float)):
                    if value >= rule.threshold:
                        return EligibilityCriterionResult(
                            criterion=rule.original_text,
                            status="passed",
                            reason=f"Applicant's annual turnover ({value:,.0f} {rule.currency}) meets the minimum requirement of {rule.threshold:,.0f} {rule.currency}"
                        )
                    else:
                        return EligibilityCriterionResult(
                            criterion=rule.original_text,
                            status="failed",
                            reason=f"Applicant's annual turnover ({value:,.0f} {rule.currency}) is below the minimum requirement of {rule.threshold:,.0f} {rule.currency}"
                        )

        return EligibilityCriterionResult(
            criterion=rule.original_text,
            status="undetermined",
            reason=f"Required field not provided: {', '.join(rule.required_fields)}"
        )

    def _evaluate_maximum_turnover(
        self,
        rule: MaximumTurnoverRule,
        applicant_info: Dict[str, Any]
    ) -> EligibilityCriterionResult:
        """Evaluate maximum turnover rule."""
        for field in rule.required_fields:
            if field in applicant_info:
                value = applicant_info[field]
                if isinstance(value, (int, float)):
                    if value < rule.threshold:
                        return EligibilityCriterionResult(
                            criterion=rule.original_text,
                            status="passed",
                            reason=f"Applicant's annual turnover ({value:,.0f} {rule.currency}) is under the threshold of {rule.threshold:,.0f} {rule.currency}"
                        )
                    else:
                        return EligibilityCriterionResult(
                            criterion=rule.original_text,
                            status="failed",
                            reason=f"Applicant's annual turnover ({value:,.0f} {rule.currency}) exceeds the threshold of {rule.threshold:,.0f} {rule.currency}"
                        )

        return EligibilityCriterionResult(
            criterion=rule.original_text,
            status="undetermined",
            reason=f"Required field not provided: {', '.join(rule.required_fields)}"
        )

    def _evaluate_minimum_years(
        self,
        rule: MinimumYearsRule,
        applicant_info: Dict[str, Any]
    ) -> EligibilityCriterionResult:
        """Evaluate minimum years rule."""
        for field in rule.required_fields:
            if field in applicant_info:
                value = applicant_info[field]
                if isinstance(value, (int, float)):
                    if value >= rule.years:
                        return EligibilityCriterionResult(
                            criterion=rule.original_text,
                            status="passed",
                            reason=f"Applicant meets the {rule.years_type} requirement ({value} years >= {rule.years} years)"
                        )
                    else:
                        return EligibilityCriterionResult(
                            criterion=rule.original_text,
                            status="failed",
                            reason=f"Applicant does not meet the {rule.years_type} requirement ({value} years < {rule.years} years)"
                        )

        return EligibilityCriterionResult(
            criterion=rule.original_text,
            status="undetermined",
            reason=f"Required field not provided: {', '.join(rule.required_fields)}"
        )

    def _evaluate_document_required(
        self,
        rule: DocumentRequiredRule,
        applicant_info: Dict[str, Any]
    ) -> EligibilityCriterionResult:
        """Evaluate document required rule."""
        if rule.document_type in applicant_info:
            value = applicant_info[rule.document_type]
            if isinstance(value, bool):
                if value:
                    return EligibilityCriterionResult(
                        criterion=rule.original_text,
                        status="passed",
                        reason=f"Applicant has provided {rule.document_type.replace('_', ' ')}"
                    )
                else:
                    return EligibilityCriterionResult(
                        criterion=rule.original_text,
                        status="failed",
                        reason=f"Applicant has not provided {rule.document_type.replace('_', ' ')}"
                    )
            elif isinstance(value, str) and value.lower() in ["yes", "true", "provided", "valid"]:
                return EligibilityCriterionResult(
                    criterion=rule.original_text,
                    status="passed",
                    reason=f"Applicant has provided {rule.document_type.replace('_', ' ')}"
                )

        return EligibilityCriterionResult(
            criterion=rule.original_text,
            status="undetermined",
            reason=f"Required field not provided: {rule.document_type}"
        )

    def _evaluate_license_required(
        self,
        rule: LicenseRequiredRule,
        applicant_info: Dict[str, Any]
    ) -> EligibilityCriterionResult:
        """Evaluate license required rule."""
        if rule.license_type in applicant_info:
            value = applicant_info[rule.license_type]
            if isinstance(value, bool):
                if value:
                    return EligibilityCriterionResult(
                        criterion=rule.original_text,
                        status="passed",
                        reason=f"Applicant has a valid {rule.license_type.replace('_', ' ')}"
                    )
                else:
                    return EligibilityCriterionResult(
                        criterion=rule.original_text,
                        status="failed",
                        reason=f"Applicant does not have a valid {rule.license_type.replace('_', ' ')}"
                    )
            elif isinstance(value, str) and value.lower() in ["yes", "true", "valid"]:
                return EligibilityCriterionResult(
                    criterion=rule.original_text,
                    status="passed",
                    reason=f"Applicant has a valid {rule.license_type.replace('_', ' ')}"
                )

        return EligibilityCriterionResult(
            criterion=rule.original_text,
            status="undetermined",
            reason=f"Required field not provided: {rule.license_type}"
        )

    def _evaluate_credit_rating(
        self,
        rule: CreditRatingRule,
        applicant_info: Dict[str, Any]
    ) -> EligibilityCriterionResult:
        """Evaluate credit rating rule."""
        for field in rule.required_fields:
            if field in applicant_info:
                value = applicant_info[field]
                if value and (isinstance(value, str) and value.strip()):
                    return EligibilityCriterionResult(
                        criterion=rule.original_text,
                        status="passed",
                        reason=f"Applicant has a credit rating assessment: {value}"
                    )

        return EligibilityCriterionResult(
            criterion=rule.original_text,
            status="undetermined",
            reason=f"Required field not provided: {', '.join(rule.required_fields)}"
        )

    def _evaluate_exposure_limit(
        self,
        rule: ExposureLimitRule,
        applicant_info: Dict[str, Any]
    ) -> EligibilityCriterionResult:
        """Evaluate exposure limit rule."""
        for field in rule.required_fields:
            if field in applicant_info:
                value = applicant_info[field]
                if value and (isinstance(value, (int, float)) or isinstance(value, str) and value.strip()):
                    return EligibilityCriterionResult(
                        criterion=rule.original_text,
                        status="passed",
                        reason=f"Maximum exposure limit has been defined: {value}"
                    )

        return EligibilityCriterionResult(
            criterion=rule.original_text,
            status="undetermined",
            reason=f"Required field not provided: {', '.join(rule.required_fields)}"
        )

    def _evaluate_customer_diversity(
        self,
        rule: CustomerDiversityRule,
        applicant_info: Dict[str, Any]
    ) -> EligibilityCriterionResult:
        """Evaluate customer diversity rule."""
        for field in rule.required_fields:
            if field in applicant_info:
                value = applicant_info[field]
                if isinstance(value, (int, float)):
                    if value <= rule.max_single_buyer_percentage:
                        return EligibilityCriterionResult(
                            criterion=rule.original_text,
                            status="passed",
                            reason=f"Customer concentration is {value}%, meeting the requirement (no single buyer > {rule.max_single_buyer_percentage}%)"
                        )
                    else:
                        return EligibilityCriterionResult(
                            criterion=rule.original_text,
                            status="failed",
                            reason=f"Customer concentration is {value}%, exceeding the maximum allowed {rule.max_single_buyer_percentage}%"
                        )

        return EligibilityCriterionResult(
            criterion=rule.original_text,
            status="undetermined",
            reason=f"Required field not provided: {', '.join(rule.required_fields)}"
        )

    def _evaluate_compliance(
        self,
        rule: ComplianceRule,
        applicant_info: Dict[str, Any]
    ) -> EligibilityCriterionResult:
        """Evaluate compliance rule."""
        for field in rule.required_fields:
            if field in applicant_info:
                value = applicant_info[field]
                if value and (isinstance(value, str) and value.strip().lower() in ["compliant", "yes", "true"]):
                    return EligibilityCriterionResult(
                        criterion=rule.original_text,
                        status="passed",
                        reason=f"Applicant is compliant with {rule.compliance_type} regulations"
                    )

        return EligibilityCriterionResult(
            criterion=rule.original_text,
            status="undetermined",
            reason=f"Required field not provided: {', '.join(rule.required_fields)}"
        )

    def _evaluate_multi_region(
        self,
        rule: MultiRegionRule,
        applicant_info: Dict[str, Any]
    ) -> EligibilityCriterionResult:
        """Evaluate multi-region rule."""
        for field in rule.required_fields:
            if field in applicant_info:
                value = applicant_info[field]
                if isinstance(value, bool) and value:
                    return EligibilityCriterionResult(
                        criterion=rule.original_text,
                        status="passed",
                        reason=f"Applicant meets multi-region requirement"
                    )
                elif isinstance(value, str) and value.lower() in ["yes", "true", "both"]:
                    return EligibilityCriterionResult(
                        criterion=rule.original_text,
                        status="passed",
                        reason=f"Applicant meets multi-region requirement"
                    )

        return EligibilityCriterionResult(
            criterion=rule.original_text,
            status="undetermined",
            reason=f"Required field not provided: {', '.join(rule.required_fields)}"
        )

    def _evaluate_existing_policyholder(
        self,
        rule: ExistingPolicyholderRule,
        applicant_info: Dict[str, Any]
    ) -> EligibilityCriterionResult:
        """Evaluate existing policyholder rule."""
        for field in rule.required_fields:
            if field in applicant_info:
                value = applicant_info[field]
                if isinstance(value, bool) and value:
                    return EligibilityCriterionResult(
                        criterion=rule.original_text,
                        status="passed",
                        reason=f"Applicant is an existing policyholder"
                    )
                elif isinstance(value, str) and value.strip():
                    return EligibilityCriterionResult(
                        criterion=rule.original_text,
                        status="passed",
                        reason=f"Applicant is an existing policyholder (policy: {value})"
                    )

        return EligibilityCriterionResult(
            criterion=rule.original_text,
            status="undetermined",
            reason=f"Required field not provided: {', '.join(rule.required_fields)}"
        )

    def _evaluate_unknown(
        self,
        rule: UnknownRule,
        applicant_info: Dict[str, Any]
    ) -> EligibilityCriterionResult:
        """Evaluate unknown rule (always undetermined)."""
        return EligibilityCriterionResult(
            criterion=rule.original_text,
            status="undetermined",
            reason="This rule type is not supported for automatic evaluation. Manual review required."
        )
