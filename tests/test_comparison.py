"""Tests for policy comparison service."""

import pytest

from app.comparison import compare_policies, ComparisonError
from app.models import ComparePoliciesRequest


def test_compare_policies_valid_two_policies():
    """Test comparing two valid policies."""
    result = compare_policies(["TCI-DOM-001", "TCI-DOM-002"])

    assert result.success is True
    assert len(result.policies) == 2
    assert result.policies[0].policy_id == "TCI-DOM-001"
    assert result.policies[1].policy_id == "TCI-DOM-002"
    assert "coverage_comparison" in result.model_dump()
    assert "exclusions_comparison" in result.model_dump()
    assert "premium_comparison" in result.model_dump()
    assert "deductible_comparison" in result.model_dump()
    assert "eligibility_comparison" in result.model_dump()


def test_compare_policies_three_policies():
    """Test comparing three policies."""
    result = compare_policies(["TCI-DOM-001", "TCI-DOM-002", "TCI-DOM-003"])

    assert result.success is True
    assert len(result.policies) == 3


def test_compare_policies_invalid_policy_id():
    """Test comparison with invalid policy ID."""
    with pytest.raises(ComparisonError) as exc_info:
        compare_policies(["TCI-DOM-001", "INVALID-ID"])

    assert "not found" in str(exc_info.value).lower()


def test_compare_policies_duplicate_ids():
    """Test comparison with duplicate policy IDs."""
    with pytest.raises(ComparisonError) as exc_info:
        compare_policies(["TCI-DOM-001", "TCI-DOM-001"])

    assert "duplicate" in str(exc_info.value).lower()


def test_compare_policies_empty_policy_id():
    """Test comparison with empty policy ID."""
    with pytest.raises(ComparisonError):
        compare_policies(["TCI-DOM-001", ""])


def test_compare_policies_too_few_ids():
    """Test comparison with less than 2 policy IDs."""
    with pytest.raises(Exception):
        compare_policies(["TCI-DOM-001"])


def test_compare_policies_too_many_ids():
    """Test comparison with more than 5 policy IDs."""
    with pytest.raises(Exception):
        compare_policies(["TCI-DOM-001", "TCI-DOM-002", "TCI-DOM-003", "TCI-EXP-001", "TCI-EXP-002", "TCI-EXP-003"])


def test_compare_policies_coverage_comparison():
    """Test coverage comparison logic."""
    result = compare_policies(["TCI-DOM-001", "TCI-DOM-002"])

    coverage_comp = result.coverage_comparison
    assert "common" in coverage_comp
    assert "unique_by_policy" in coverage_comp
    assert "count_by_policy" in coverage_comp
    assert len(coverage_comp["count_by_policy"]) == 2


def test_compare_policies_exclusions_comparison():
    """Test exclusions comparison logic."""
    result = compare_policies(["TCI-DOM-001", "TCI-DOM-002"])

    exclusions_comp = result.exclusions_comparison
    assert "common" in exclusions_comp
    assert "unique_by_policy" in exclusions_comp
    assert "count_by_policy" in exclusions_comp


def test_compare_policies_premium_comparison():
    """Test premium comparison logic."""
    result = compare_policies(["TCI-DOM-001", "TCI-DOM-002"])

    premium_comp = result.premium_comparison
    assert "by_policy" in premium_comp
    assert "currencies" in premium_comp
    assert "same_currency" in premium_comp
    assert len(premium_comp["by_policy"]) == 2


def test_compare_policies_deductible_comparison():
    """Test deductible comparison logic."""
    result = compare_policies(["TCI-DOM-001", "TCI-DOM-002"])

    deductible_comp = result.deductible_comparison
    assert "by_policy" in deductible_comp
    assert "has_deductible" in deductible_comp
    assert "missing_deductible" in deductible_comp
    # Both policies should have deductibles
    assert len(deductible_comp["has_deductible"]) == 2


def test_compare_policies_eligibility_comparison():
    """Test eligibility comparison logic."""
    result = compare_policies(["TCI-DOM-001", "TCI-DOM-002"])

    eligibility_comp = result.eligibility_comparison
    assert "by_policy" in eligibility_comp
    assert "has_eligibility" in eligibility_comp
    assert "missing_eligibility" in eligibility_comp
    assert "requirements_comparison" in eligibility_comp


def test_compare_policies_missing_fields():
    """Test identification of missing fields."""
    result = compare_policies(["TCI-DOM-001", "TCI-DOM-002"])

    missing_fields = result.missing_fields
    # Both policies have all fields, so should be empty or not contain common fields
    assert isinstance(missing_fields, dict)


def test_compare_policies_request_validation():
    """Test ComparePoliciesRequest validation."""
    # Valid request
    request = ComparePoliciesRequest(policy_ids=["TCI-DOM-001", "TCI-DOM-002"])
    assert len(request.policy_ids) == 2

    # Invalid: empty list
    with pytest.raises(Exception):
        ComparePoliciesRequest(policy_ids=[])

    # Invalid: too many
    with pytest.raises(Exception):
        ComparePoliciesRequest(policy_ids=["1", "2", "3", "4", "5", "6"])


def test_compare_policies_different_categories():
    """Test comparing policies from different categories."""
    result = compare_policies(["TCI-DOM-001", "TCI-EXP-001"])

    assert result.success is True
    assert result.policies[0].category == "Domestic Trade Credit"
    assert result.policies[1].category == "Export Trade Credit"


def test_compare_policies_five_policies():
    """Test comparing the maximum allowed number of policies (5)."""
    result = compare_policies([
        "TCI-DOM-001",
        "TCI-DOM-002",
        "TCI-EXP-001",
        "TCI-SB-001",
        "TCI-WT-001"
    ])

    assert result.success is True
    assert len(result.policies) == 5
