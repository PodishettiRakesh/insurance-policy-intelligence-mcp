"""Pydantic models for insurance policy data."""

from datetime import date
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class PolicyStatus(str, Enum):
    """Policy status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"


class Premium(BaseModel):
    """Premium details."""
    amount: float = Field(..., gt=0, description="Premium amount")
    currency: str = Field(..., min_length=1, description="Currency code")
    period: str = Field(..., min_length=1, description="Premium period (e.g., annual, monthly)")


class Deductible(BaseModel):
    """Deductible details."""
    amount: float = Field(..., ge=0, description="Deductible amount")
    currency: str = Field(..., min_length=1, description="Currency code")


class Eligibility(BaseModel):
    """Eligibility criteria."""
    vehicle_type: Optional[List[str]] = Field(default=None, description="Applicable vehicle types")
    minimum_entry_age: Optional[int] = Field(default=None, ge=0, description="Minimum entry age")
    requirements: Optional[List[str]] = Field(default=None, description="Additional requirements")


class Policy(BaseModel):
    """Insurance policy model with validation."""

    policy_id: str = Field(..., min_length=1, description="Unique identifier for the policy")
    title: str = Field(..., min_length=1, description="Policy title")
    category: str = Field(..., min_length=1, description="Policy category")
    provider: str = Field(..., min_length=1, description="Insurance provider")
    description: str = Field(..., min_length=1, description="Short summary of the policy")
    coverage: List[str] = Field(..., min_length=1, description="List of coverage items")
    exclusions: List[str] = Field(default_factory=list, description="List of exclusions")
    premium: Premium = Field(..., description="Premium details")
    deductible: Optional[Deductible] = Field(default=None, description="Deductible details")
    eligibility: Optional[Eligibility] = Field(default=None, description="Eligibility criteria")
    effective_date: Optional[date] = Field(default=None, description="Date the policy becomes effective")
    status: PolicyStatus = Field(..., description="Policy status")
    tags: List[str] = Field(default_factory=list, description="Searchable keywords")

    @field_validator("policy_id")
    @classmethod
    def validate_policy_id(cls, v: str) -> str:
        """Validate policy_id is not empty and strip whitespace."""
        if not v or not v.strip():
            raise ValueError("policy_id cannot be empty")
        return v.strip()

    @field_validator("title", "category", "provider", "description")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        """Validate string fields are not empty after stripping."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

    @field_validator("coverage", "exclusions", "tags")
    @classmethod
    def validate_string_lists(cls, v: List[str]) -> List[str]:
        """Validate list fields contain non-empty strings."""
        validated = []
        for item in v:
            if item and item.strip():
                validated.append(item.strip())
        return validated


# Structured comparison models


class CoverageComparison(BaseModel):
    """Structured comparison of coverage items across policies."""
    common_items: List[str] = Field(default_factory=list, description="Coverage items common to all policies")
    unique_by_policy: Dict[str, List[str]] = Field(default_factory=dict, description="Coverage items unique to each policy")
    coverage_counts: Dict[str, int] = Field(default_factory=dict, description="Count of coverage items per policy")


class ExclusionComparison(BaseModel):
    """Structured comparison of exclusion items across policies."""
    common_items: List[str] = Field(default_factory=list, description="Exclusion items common to all policies")
    unique_by_policy: Dict[str, List[str]] = Field(default_factory=dict, description="Exclusion items unique to each policy")
    exclusion_counts: Dict[str, int] = Field(default_factory=dict, description="Count of exclusion items per policy")


class PremiumComparison(BaseModel):
    """Structured comparison of premiums across policies."""
    amounts_by_policy: Dict[str, float] = Field(default_factory=dict, description="Premium amount for each policy")
    currencies: List[str] = Field(default_factory=list, description="Currency codes present")
    same_currency: bool = Field(default=False, description="Whether all premiums use same currency")
    currency_mismatch_warning: Optional[str] = Field(default=None, description="Warning if currencies differ")
    relative_difference: Optional[float] = Field(default=None, description="Relative difference between policies (for 2 policies)")


class DeductibleComparison(BaseModel):
    """Structured comparison of deductibles across policies."""
    has_deductible: List[str] = Field(default_factory=list, description="Policies that have a deductible")
    missing_deductible: List[str] = Field(default_factory=list, description="Policies without deductible information")
    amounts_by_policy: Dict[str, float] = Field(default_factory=dict, description="Deductible amount for each policy")


class EligibilityComparison(BaseModel):
    """Structured comparison of eligibility criteria across policies."""
    has_eligibility: List[str] = Field(default_factory=list, description="Policies with eligibility criteria")
    missing_eligibility: List[str] = Field(default_factory=list, description="Policies without eligibility information")
    requirements_by_policy: Dict[str, List[str]] = Field(default_factory=dict, description="Eligibility requirements per policy")
    common_requirements: List[str] = Field(default_factory=list, description="Requirements common to all policies")
    unique_requirements_by_policy: Dict[str, List[str]] = Field(default_factory=dict, description="Requirements unique to each policy")


# Legacy comparison models (kept for backward compatibility)


class ComparePoliciesRequest(BaseModel):
    """Request model for comparing policies."""
    policy_ids: List[str] = Field(..., min_length=2, max_length=5, description="List of policy IDs to compare (2-5 policies)")

    @field_validator("policy_ids")
    @classmethod
    def validate_policy_ids(cls, v: List[str]) -> List[str]:
        """Validate policy IDs are non-empty and unique."""
        validated = []
        seen = set()
        for policy_id in v:
            if not policy_id or not policy_id.strip():
                raise ValueError("Policy ID cannot be empty")
            policy_id = policy_id.strip()
            if policy_id in seen:
                raise ValueError(f"Duplicate policy ID: {policy_id}")
            seen.add(policy_id)
            validated.append(policy_id)
        return validated


class PolicyComparisonItem(BaseModel):
    """Single policy data for comparison."""
    policy_id: str
    title: str
    category: str
    provider: str
    coverage: List[str]
    exclusions: List[str]
    premium: Dict[str, Any]
    deductible: Optional[Dict[str, Any]]
    eligibility: Optional[Dict[str, Any]]


class ComparisonResult(BaseModel):
    """Result of policy comparison."""
    success: bool
    policies: List[PolicyComparisonItem]
    coverage_comparison: Dict[str, Any]
    exclusions_comparison: Dict[str, Any]
    premium_comparison: Dict[str, Any]
    deductible_comparison: Dict[str, Any]
    eligibility_comparison: Dict[str, Any]
    missing_fields: Dict[str, List[str]]
    summary: str = Field(default="", description="Human-readable summary of the comparison")
    error: Optional[str] = None


# Eligibility check models


class CheckEligibilityRequest(BaseModel):
    """Request model for checking eligibility."""
    policy_id: str = Field(..., min_length=1, description="Policy ID to check eligibility for")
    applicant_info: Dict[str, Any] = Field(..., description="Applicant information for eligibility evaluation")

    @field_validator("policy_id")
    @classmethod
    def validate_policy_id(cls, v: str) -> str:
        """Validate policy_id is not empty and strip whitespace."""
        if not v or not v.strip():
            raise ValueError("policy_id cannot be empty")
        return v.strip()


class EligibilityCriterionResult(BaseModel):
    """Result for a single eligibility criterion evaluation."""
    criterion: str = Field(..., description="The eligibility criterion text")
    status: str = Field(..., description="Status: 'passed', 'failed', or 'undetermined'")
    reason: Optional[str] = Field(default=None, description="Explanation of the result")


class EligibilityCheckResult(BaseModel):
    """Result of eligibility check."""
    success: bool
    policy_id: str
    policy_title: str
    overall_status: str = Field(..., description="Overall status: 'eligible', 'ineligible', or 'undetermined'")
    criteria_results: List[EligibilityCriterionResult] = Field(..., description="Results for each eligibility criterion")
    summary: str = Field(..., description="Human-readable summary of the eligibility check")
    error: Optional[str] = None


# Explicit eligibility rule models


class RuleType(str, Enum):
    """Enumeration of supported eligibility rule types."""
    MINIMUM_TURNOVER = "minimum_turnover"
    MAXIMUM_TURNOVER = "maximum_turnover"
    MINIMUM_YEARS = "minimum_years"
    DOCUMENT_REQUIRED = "document_required"
    LICENSE_REQUIRED = "license_required"
    CREDIT_RATING = "credit_rating"
    EXPOSURE_LIMIT = "exposure_limit"
    CUSTOMER_DIVERSITY = "customer_diversity"
    COMPLIANCE = "compliance"
    MULTI_REGION = "multi_region"
    EXISTING_POLICYHOLDER = "existing_policyholder"
    UNKNOWN = "unknown"


class EligibilityRule(BaseModel):
    """Base model for an explicit eligibility rule."""
    rule_type: RuleType = Field(..., description="Type of the rule")
    original_text: str = Field(..., description="Original criterion text from policy")
    description: str = Field(..., description="Human-readable description of the rule")
    required_fields: List[str] = Field(..., description="Applicant fields required to evaluate this rule")


class MinimumTurnoverRule(EligibilityRule):
    """Rule for minimum annual turnover requirement."""
    rule_type: RuleType = RuleType.MINIMUM_TURNOVER
    threshold: float = Field(..., description="Minimum required turnover amount")
    currency: str = Field(default="INR", description="Currency of the threshold")


class MaximumTurnoverRule(EligibilityRule):
    """Rule for maximum annual turnover requirement."""
    rule_type: RuleType = RuleType.MAXIMUM_TURNOVER
    threshold: float = Field(..., description="Maximum allowed turnover amount")
    currency: str = Field(default="INR", description="Currency of the threshold")


class MinimumYearsRule(EligibilityRule):
    """Rule for minimum years requirement (registration, export, etc.)."""
    rule_type: RuleType = RuleType.MINIMUM_YEARS
    years: int = Field(..., description="Minimum required years")
    years_type: str = Field(..., description="Type of years (e.g., 'business_age', 'export_years')")


class DocumentRequiredRule(EligibilityRule):
    """Rule for required document."""
    rule_type: RuleType = RuleType.DOCUMENT_REQUIRED
    document_type: str = Field(..., description="Type of document required")


class LicenseRequiredRule(EligibilityRule):
    """Rule for required license."""
    rule_type: RuleType = RuleType.LICENSE_REQUIRED
    license_type: str = Field(..., description="Type of license required")


class CreditRatingRule(EligibilityRule):
    """Rule for credit rating requirement."""
    rule_type: RuleType = RuleType.CREDIT_RATING


class ExposureLimitRule(EligibilityRule):
    """Rule for exposure limit requirement."""
    rule_type: RuleType = RuleType.EXPOSURE_LIMIT


class CustomerDiversityRule(EligibilityRule):
    """Rule for customer diversity requirement."""
    rule_type: RuleType = RuleType.CUSTOMER_DIVERSITY
    max_single_buyer_percentage: float = Field(default=30.0, description="Maximum percentage any single buyer can represent")


class ComplianceRule(EligibilityRule):
    """Rule for compliance requirement."""
    rule_type: RuleType = RuleType.COMPLIANCE
    compliance_type: Optional[str] = Field(default=None, description="Type of compliance required")


class MultiRegionRule(EligibilityRule):
    """Rule for multi-region/multi-country requirement."""
    rule_type: RuleType = RuleType.MULTI_REGION


class ExistingPolicyholderRule(EligibilityRule):
    """Rule for existing policyholder requirement."""
    rule_type: RuleType = RuleType.EXISTING_POLICYHOLDER


class UnknownRule(EligibilityRule):
    """Rule that could not be parsed (requires manual review)."""
    rule_type: RuleType = RuleType.UNKNOWN
