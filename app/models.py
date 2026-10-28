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


# Comparison models


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
