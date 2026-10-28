"""Tests for Pydantic policy models."""

import pytest
from datetime import date
from pydantic import ValidationError

from app.models import Policy, PolicyStatus, Premium, Deductible, Eligibility


def test_policy_status_enum():
    """Test PolicyStatus enum values."""
    assert PolicyStatus.ACTIVE == "active"
    assert PolicyStatus.INACTIVE == "inactive"


def test_premium_model_valid():
    """Test Premium model with valid data."""
    premium = Premium(amount=10000, currency="INR", period="annual")
    assert premium.amount == 10000
    assert premium.currency == "INR"
    assert premium.period == "annual"


def test_premium_model_invalid_amount():
    """Test Premium model rejects non-positive amount."""
    with pytest.raises(ValidationError):
        Premium(amount=0, currency="INR", period="annual")

    with pytest.raises(ValidationError):
        Premium(amount=-100, currency="INR", period="annual")


def test_deductible_model_valid():
    """Test Deductible model with valid data."""
    deductible = Deductible(amount=2000, currency="INR")
    assert deductible.amount == 2000
    assert deductible.currency == "INR"


def test_deductible_model_invalid_amount():
    """Test Deductible model rejects negative amount."""
    with pytest.raises(ValidationError):
        Deductible(amount=-100, currency="INR")


def test_eligibility_model_with_vehicle_type():
    """Test Eligibility model with vehicle_type."""
    eligibility = Eligibility(
        vehicle_type=["private car", "suv"],
        requirements=["Vehicle must be registered"]
    )
    assert eligibility.vehicle_type == ["private car", "suv"]
    assert eligibility.requirements == ["Vehicle must be registered"]


def test_eligibility_model_with_age():
    """Test Eligibility model with minimum_entry_age."""
    eligibility = Eligibility(
        minimum_entry_age=18,
        requirements=["Valid ID required"]
    )
    assert eligibility.minimum_entry_age == 18
    assert eligibility.requirements == ["Valid ID required"]


def test_policy_model_valid():
    """Test Policy model with all required fields."""
    policy = Policy(
        policy_id="TEST-001",
        title="Test Policy",
        category="Test Category",
        provider="Test Provider",
        description="Test description",
        coverage=["Coverage item 1", "Coverage item 2"],
        premium=Premium(amount=10000, currency="INR", period="annual"),
        status=PolicyStatus.ACTIVE
    )
    assert policy.policy_id == "TEST-001"
    assert policy.title == "Test Policy"
    assert policy.status == PolicyStatus.ACTIVE


def test_policy_model_missing_required_field():
    """Test Policy model rejects missing required fields."""
    with pytest.raises(ValidationError):
        Policy(
            policy_id="TEST-001",
            title="Test Policy",
            # Missing category, provider, description, coverage, premium, status
        )


def test_policy_model_empty_string_validation():
    """Test Policy model rejects empty strings after stripping."""
    with pytest.raises(ValidationError):
        Policy(
            policy_id="TEST-001",
            title="   ",  # Empty after strip
            category="Test Category",
            provider="Test Provider",
            description="Test description",
            coverage=["Coverage item 1"],
            premium=Premium(amount=10000, currency="INR", period="annual"),
            status=PolicyStatus.ACTIVE
        )


def test_policy_model_tags_validation():
    """Test Policy model validates and cleans tags."""
    policy = Policy(
        policy_id="TEST-001",
        title="Test Policy",
        category="Test Category",
        provider="Test Provider",
        description="Test description",
        coverage=["Coverage item 1"],
        premium=Premium(amount=10000, currency="INR", period="annual"),
        status=PolicyStatus.ACTIVE,
        tags=["tag1", "  tag2  ", "", "tag3"]
    )
    assert policy.tags == ["tag1", "tag2", "tag3"]


def test_policy_model_with_all_optional_fields():
    """Test Policy model with all optional fields."""
    policy = Policy(
        policy_id="TEST-001",
        title="Test Policy",
        category="Test Category",
        provider="Test Provider",
        description="Test description",
        coverage=["Coverage item 1"],
        exclusions=["Exclusion 1"],
        premium=Premium(amount=10000, currency="INR", period="annual"),
        deductible=Deductible(amount=2000, currency="INR"),
        eligibility=Eligibility(requirements=["Requirement 1"]),
        effective_date=date(2026, 1, 1),
        status=PolicyStatus.ACTIVE,
        tags=["tag1", "tag2"]
    )
    assert policy.exclusions == ["Exclusion 1"]
    assert policy.deductible is not None
    assert policy.eligibility is not None
    assert policy.effective_date == date(2026, 1, 1)
    assert policy.tags == ["tag1", "tag2"]


def test_policy_model_string_stripping():
    """Test Policy model strips whitespace from string fields."""
    policy = Policy(
        policy_id="  TEST-001  ",
        title="  Test Policy  ",
        category="  Test Category  ",
        provider="  Test Provider  ",
        description="  Test description  ",
        coverage=["  Coverage item 1  "],
        premium=Premium(amount=10000, currency="INR", period="annual"),
        status=PolicyStatus.ACTIVE
    )
    assert policy.policy_id == "TEST-001"
    assert policy.title == "Test Policy"
    assert policy.category == "Test Category"
    assert policy.provider == "Test Provider"
    assert policy.description == "Test description"
    assert policy.coverage == ["Coverage item 1"]
