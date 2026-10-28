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
