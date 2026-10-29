"""Parse eligibility criteria into explicit rule objects."""

import re
from typing import List, Union
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
    RuleType,
)


def parse_criterion_to_rule(criterion: str) -> EligibilityRule:
    """
    Parse a text criterion into an explicit rule object.

    Args:
        criterion: The eligibility criterion text

    Returns:
        An EligibilityRule subclass representing the parsed rule
    """
    criterion_lower = criterion.lower()

    # Pattern 1: Minimum annual turnover
    turnover_match = re.search(
        r"minimum\s+annual\s+(?:export\s+)?turnover\s+of\s+([a-z]+)\s+([\d.]+)\s*(million|billion|thousand|lakh|crore)?",
        criterion_lower,
        re.IGNORECASE
    )
    if turnover_match:
        currency = turnover_match.group(1).upper()
        value = float(turnover_match.group(2))
        multiplier = turnover_match.group(3)

        multiplier_map = {
            "million": 1_000_000,
            "billion": 1_000_000_000,
            "thousand": 1_000,
            "lakh": 100_000,
            "crore": 10_000_000
        }
        threshold = value * multiplier_map.get(multiplier, 1)

        return MinimumTurnoverRule(
            rule_type=RuleType.MINIMUM_TURNOVER,
            original_text=criterion,
            description=f"Minimum annual turnover of {currency} {threshold:,.0f}",
            required_fields=["annual_turnover", "turnover", "revenue", "annual_revenue"],
            threshold=threshold,
            currency=currency
        )

    # Pattern 2: Maximum annual turnover (under threshold)
    under_turnover_match = re.search(
        r"annual\s+turnover\s+under\s+([a-z]+)\s+([\d.]+)\s*(million|billion|thousand|lakh|crore)?",
        criterion_lower
    )
    if under_turnover_match:
        currency = under_turnover_match.group(1).upper()
        value = float(under_turnover_match.group(2))
        multiplier = under_turnover_match.group(3)

        multiplier_map = {
            "million": 1_000_000,
            "billion": 1_000_000_000,
            "thousand": 1_000,
            "lakh": 100_000,
            "crore": 10_000_000
        }
        threshold = value * multiplier_map.get(multiplier, 1)

        return MaximumTurnoverRule(
            rule_type=RuleType.MAXIMUM_TURNOVER,
            original_text=criterion,
            description=f"Annual turnover under {currency} {threshold:,.0f}",
            required_fields=["annual_turnover", "turnover", "revenue", "annual_revenue"],
            threshold=threshold,
            currency=currency
        )

    # Pattern 3: Business registration duration
    registration_match = re.search(
        r"business\s+must\s+be\s+registered\s+for\s+at\s+least\s+(\d+)\s+years?",
        criterion_lower
    )
    if registration_match:
        years = int(registration_match.group(1))
        return MinimumYearsRule(
            rule_type=RuleType.MINIMUM_YEARS,
            original_text=criterion,
            description=f"Business must be registered for at least {years} years",
            required_fields=["business_age_years", "registration_years", "years_in_business", "years_registered"],
            years=years,
            years_type="business_age"
        )

    # Pattern 4: Export business duration
    export_years_match = re.search(
        r"established\s+export\s+business\s*\(?(\d+)\+\s*years?\)?",
        criterion_lower
    )
    if export_years_match:
        years = int(export_years_match.group(1))
        return MinimumYearsRule(
            rule_type=RuleType.MINIMUM_YEARS,
            original_text=criterion,
            description=f"Established export business ({years}+ years)",
            required_fields=["export_years", "years_in_export", "export_business_age"],
            years=years,
            years_type="export_years"
        )

    # Pattern 5: Valid export license
    if "valid export license" in criterion_lower or "export license" in criterion_lower:
        return LicenseRequiredRule(
            rule_type=RuleType.LICENSE_REQUIRED,
            original_text=criterion,
            description="Valid export license required",
            required_fields=["export_license"],
            license_type="export_license"
        )

    # Pattern 6: Audited financial statements
    if "audited financial statements" in criterion_lower:
        return DocumentRequiredRule(
            rule_type=RuleType.DOCUMENT_REQUIRED,
            original_text=criterion,
            description="Audited financial statements required",
            required_fields=["audited_financial_statements"],
            document_type="audited_financial_statements"
        )

    # Pattern 7: Financial statements
    if "financial statements" in criterion_lower:
        return DocumentRequiredRule(
            rule_type=RuleType.DOCUMENT_REQUIRED,
            original_text=criterion,
            description="Financial statements required",
            required_fields=["financial_statements"],
            document_type="financial_statements"
        )

    # Pattern 8: Credit rating
    if "credit rating" in criterion_lower:
        return CreditRatingRule(
            rule_type=RuleType.CREDIT_RATING,
            original_text=criterion,
            description="Credit rating assessment required",
            required_fields=["credit_rating", "buyer_credit_rating", "credit_score"]
        )

    # Pattern 9: Maximum exposure limit
    if "maximum exposure limit" in criterion_lower:
        return ExposureLimitRule(
            rule_type=RuleType.EXPOSURE_LIMIT,
            original_text=criterion,
            description="Maximum exposure limit required",
            required_fields=["exposure_limit", "max_exposure"]
        )

    # Pattern 10: Customer diversity / no single buyer
    if "diverse customer base" in criterion_lower or "no single buyer" in criterion_lower:
        return CustomerDiversityRule(
            rule_type=RuleType.CUSTOMER_DIVERSITY,
            original_text=criterion,
            description="Diverse customer base (no single buyer > 30%)",
            required_fields=["customer_concentration", "largest_buyer_percentage"],
            max_single_buyer_percentage=30.0
        )

    # Pattern 11: Government contract
    if "government contract" in criterion_lower or "valid government contract" in criterion_lower:
        return DocumentRequiredRule(
            rule_type=RuleType.DOCUMENT_REQUIRED,
            original_text=criterion,
            description="Valid government contract required",
            required_fields=["government_contract"],
            document_type="government_contract"
        )

    # Pattern 12: Compliance
    if "compliance" in criterion_lower:
        return ComplianceRule(
            rule_type=RuleType.COMPLIANCE,
            original_text=criterion,
            description="Compliance with regulations required",
            required_fields=["compliance_status", "regulatory_compliance"],
            compliance_type="regulatory"
        )

    # Pattern 13: Multi-country / multi-region
    if "multi-country" in criterion_lower or "both domestic and export" in criterion_lower:
        return MultiRegionRule(
            rule_type=RuleType.MULTI_REGION,
            original_text=criterion,
            description="Multi-country or multi-region business required",
            required_fields=["operating_regions", "export_countries", "has_domestic_and_export"]
        )

    # Pattern 14: Existing policyholder only
    if "existing policyholders only" in criterion_lower:
        return ExistingPolicyholderRule(
            rule_type=RuleType.EXISTING_POLICYHOLDER,
            original_text=criterion,
            description="Only existing policyholders eligible",
            required_fields=["is_existing_policyholder", "policy_number"]
        )

    # Pattern 15: General requirements (fallback)
    if "required" in criterion_lower or "must be provided" in criterion_lower:
        return DocumentRequiredRule(
            rule_type=RuleType.DOCUMENT_REQUIRED,
            original_text=criterion,
            description=f"Requirement: {criterion}",
            required_fields=[],
            document_type="general"
        )

    # If no pattern matches, return unknown rule
    return UnknownRule(
        rule_type=RuleType.UNKNOWN,
        original_text=criterion,
        description="Unknown rule type - requires manual review",
        required_fields=[]
    )


def parse_criteria_to_rules(criteria_list: List[str]) -> List[EligibilityRule]:
    """
    Parse a list of criteria into rule objects.

    Args:
        criteria_list: List of eligibility criterion strings

    Returns:
        List of EligibilityRule objects
    """
    rules = []
    for criterion in criteria_list:
        rule = parse_criterion_to_rule(criterion)
        rules.append(rule)
    return rules
