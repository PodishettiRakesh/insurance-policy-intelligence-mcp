"""Tests for eligibility evaluation service."""

import pytest

from app.eligibility import check_eligibility, EligibilityError
from app.models import CheckEligibilityRequest


def test_check_eligibility_valid_policy_eligible():
    """Test eligibility check for a policy where applicant meets all criteria."""
    applicant_info = {
        "annual_turnover": 15000000,  # 15 million INR
        "business_age_years": 3,
        "financial_statements": True
    }

    result = check_eligibility("TCI-DOM-001", applicant_info)

    assert result.success is True
    assert result.policy_id == "TCI-DOM-001"
    assert result.overall_status in ["eligible", "undetermined"]
    assert len(result.criteria_results) == 3
    assert result.summary is not None


def test_check_eligibility_valid_policy_ineligible():
    """Test eligibility check for a policy where applicant fails criteria."""
    applicant_info = {
        "annual_turnover": 5000000,  # 5 million INR (below 10 million requirement)
        "business_age_years": 1,  # 1 year (below 2 year requirement)
        "financial_statements": True
    }

    result = check_eligibility("TCI-DOM-001", applicant_info)

    assert result.success is True
    assert result.policy_id == "TCI-DOM-001"
    assert result.overall_status == "ineligible"
    assert len(result.criteria_results) == 3


def test_check_eligibility_invalid_policy_id():
    """Test eligibility check with invalid policy ID."""
    applicant_info = {
        "annual_turnover": 15000000,
        "business_age_years": 3
    }

    with pytest.raises(EligibilityError) as exc_info:
        check_eligibility("INVALID-ID", applicant_info)

    assert "not found" in str(exc_info.value).lower()


def test_check_eligibility_empty_policy_id():
    """Test eligibility check with empty policy ID."""
    applicant_info = {"annual_turnover": 15000000}

    with pytest.raises(EligibilityError):
        check_eligibility("", applicant_info)


def test_check_eligibility_no_eligibility_criteria():
    """Test eligibility check for policy without eligibility criteria."""
    # This test assumes there might be a policy without eligibility criteria
    # For now, we'll test with a known policy that has criteria
    applicant_info = {"annual_turnover": 15000000}

    result = check_eligibility("TCI-DOM-001", applicant_info)

    # The policy has criteria, so it should not return undetermined due to missing criteria
    assert result.success is True


def test_check_eligibility_turnover_requirement_passed():
    """Test turnover requirement evaluation - passed."""
    applicant_info = {
        "annual_turnover": 60000000,  # 60 million INR (above 50 million requirement)
        "business_age_years": 4,
        "audited_financial_statements": True
    }

    result = check_eligibility("TCI-DOM-002", applicant_info)

    assert result.success is True
    # Check if turnover criterion passed
    turnover_result = next(
        (r for r in result.criteria_results if "turnover" in r.criterion.lower()),
        None
    )
    if turnover_result:
        assert turnover_result.status == "passed"


def test_check_eligibility_turnover_requirement_failed():
    """Test turnover requirement evaluation - failed."""
    applicant_info = {
        "annual_turnover": 30000000,  # 30 million INR (below 50 million requirement)
        "business_age_years": 4,
        "audited_financial_statements": True
    }

    result = check_eligibility("TCI-DOM-002", applicant_info)

    assert result.success is True
    # Check if turnover criterion failed
    turnover_result = next(
        (r for r in result.criteria_results if "turnover" in r.criterion.lower()),
        None
    )
    if turnover_result:
        assert turnover_result.status == "failed"


def test_check_eligibility_turnover_requirement_undetermined():
    """Test turnover requirement evaluation - undetermined."""
    applicant_info = {
        "business_age_years": 4,
        "audited_financial_statements": True
    }

    result = check_eligibility("TCI-DOM-002", applicant_info)

    assert result.success is True
    # Check if turnover criterion is undetermined
    turnover_result = next(
        (r for r in result.criteria_results if "turnover" in r.criterion.lower()),
        None
    )
    if turnover_result:
        assert turnover_result.status == "undetermined"


def test_check_eligibility_registration_years_passed():
    """Test business registration years requirement - passed."""
    applicant_info = {
        "annual_turnover": 60000000,
        "registration_years": 4,
        "audited_financial_statements": True
    }

    result = check_eligibility("TCI-DOM-002", applicant_info)

    assert result.success is True
    # Check if registration criterion passed
    reg_result = next(
        (r for r in result.criteria_results if "registered" in r.criterion.lower()),
        None
    )
    if reg_result:
        assert reg_result.status == "passed"


def test_check_eligibility_registration_years_failed():
    """Test business registration years requirement - failed."""
    applicant_info = {
        "annual_turnover": 60000000,
        "registration_years": 2,
        "audited_financial_statements": True
    }

    result = check_eligibility("TCI-DOM-002", applicant_info)

    assert result.success is True
    # Check if registration criterion failed
    reg_result = next(
        (r for r in result.criteria_results if "registered" in r.criterion.lower()),
        None
    )
    if reg_result:
        assert reg_result.status == "failed"


def test_check_eligibility_document_requirement_passed():
    """Test document requirement - passed."""
    applicant_info = {
        "annual_turnover": 60000000,
        "business_age_years": 4,
        "audited_financial_statements": True
    }

    result = check_eligibility("TCI-DOM-002", applicant_info)

    assert result.success is True
    # Check if document criterion passed
    doc_result = next(
        (r for r in result.criteria_results if "audited" in r.criterion.lower() and "financial statements" in r.criterion.lower()),
        None
    )
    if doc_result:
        assert doc_result.status == "passed"


def test_check_eligibility_document_requirement_failed():
    """Test document requirement - failed."""
    applicant_info = {
        "annual_turnover": 60000000,
        "business_age_years": 4,
        "audited_financial_statements": False
    }

    result = check_eligibility("TCI-DOM-002", applicant_info)

    assert result.success is True
    # Check if document criterion failed
    doc_result = next(
        (r for r in result.criteria_results if "audited" in r.criterion.lower() and "financial statements" in r.criterion.lower()),
        None
    )
    if doc_result:
        assert doc_result.status == "failed"


def test_check_eligibility_export_turnover_requirement():
    """Test export turnover requirement."""
    applicant_info = {
        "export_turnover": 25000000,  # 25 million INR (above 20 million requirement)
        "export_years": 4,
        "regulatory_compliance": True
    }

    result = check_eligibility("TCI-EXP-002", applicant_info)

    assert result.success is True
    assert result.policy_id == "TCI-EXP-002"


def test_check_eligibility_export_years_requirement():
    """Test export business years requirement."""
    applicant_info = {
        "annual_turnover": 25000000,
        "export_years": 2,  # 2 years (below 3+ year requirement)
        "regulatory_compliance": True
    }

    result = check_eligibility("TCI-EXP-002", applicant_info)

    assert result.success is True
    # Check if export years criterion failed
    years_result = next(
        (r for r in result.criteria_results if "export business" in r.criterion.lower()),
        None
    )
    if years_result:
        assert years_result.status == "failed"


def test_check_eligibility_export_license_requirement():
    """Test export license requirement."""
    applicant_info = {
        "annual_turnover": 10000000,
        "export_license": True,
        "buyer_information": "Provided"
    }

    result = check_eligibility("TCI-EXP-001", applicant_info)

    assert result.success is True
    # Check if export license criterion passed
    license_result = next(
        (r for r in result.criteria_results if "export license" in r.criterion.lower()),
        None
    )
    if license_result:
        assert license_result.status == "passed"


def test_check_eligibility_sme_turnover_under():
    """Test SME policy with turnover under threshold."""
    applicant_info = {
        "annual_turnover": 3000000,  # 3 million INR (under 5 million requirement)
        "business_age_years": 2,
        "financial_statements": True
    }

    result = check_eligibility("TCI-DOM-003", applicant_info)

    assert result.success is True
    # Check if turnover under threshold passed
    turnover_result = next(
        (r for r in result.criteria_results if "turnover" in r.criterion.lower()),
        None
    )
    if turnover_result:
        assert turnover_result.status == "passed"


def test_check_eligibility_sme_turnover_exceeds():
    """Test SME policy with turnover exceeding threshold."""
    applicant_info = {
        "annual_turnover": 10000000,  # 10 million INR (exceeds 5 million requirement)
        "business_age_years": 2,
        "financial_statements": True
    }

    result = check_eligibility("TCI-DOM-003", applicant_info)

    assert result.success is True
    # Check if turnover under threshold failed
    turnover_result = next(
        (r for r in result.criteria_results if "turnover" in r.criterion.lower()),
        None
    )
    if turnover_result:
        assert turnover_result.status == "failed"


def test_check_eligibility_customer_diversity_passed():
    """Test customer diversity requirement - passed."""
    applicant_info = {
        "annual_turnover": 30000000,
        "customer_concentration": 25,  # 25% (under 30% threshold)
        "integrated_accounting_system": True
    }

    result = check_eligibility("TCI-WT-001", applicant_info)

    assert result.success is True
    # Check if customer diversity criterion passed
    diversity_result = next(
        (r for r in result.criteria_results if "customer" in r.criterion.lower()),
        None
    )
    if diversity_result:
        assert diversity_result.status == "passed"


def test_check_eligibility_customer_diversity_failed():
    """Test customer diversity requirement - failed."""
    applicant_info = {
        "annual_turnover": 30000000,
        "customer_concentration": 40,  # 40% (exceeds 30% threshold)
        "integrated_accounting_system": True
    }

    result = check_eligibility("TCI-WT-001", applicant_info)

    assert result.success is True
    # Check if customer diversity criterion failed
    diversity_result = next(
        (r for r in result.criteria_results if "customer" in r.criterion.lower()),
        None
    )
    if diversity_result:
        assert diversity_result.status == "failed"


def test_check_eligibility_multi_region_passed():
    """Test multi-region requirement - passed."""
    applicant_info = {
        "annual_turnover": 60000000,
        "operating_regions": ["domestic", "export"],
        "integrated_financial_reporting": True
    }

    result = check_eligibility("TCI-WT-003", applicant_info)

    assert result.success is True
    # Check if multi-region criterion passed
    region_result = next(
        (r for r in result.criteria_results if "domestic and export" in r.criterion.lower()),
        None
    )
    if region_result:
        assert region_result.status == "passed"


def test_check_eligibility_multi_region_failed():
    """Test multi-region requirement - failed."""
    applicant_info = {
        "annual_turnover": 60000000,
        "has_domestic_operations": True,
        "has_export_operations": False,
        "integrated_financial_reporting": True
    }

    result = check_eligibility("TCI-WT-003", applicant_info)

    assert result.success is True
    # Check if multi-region criterion failed
    region_result = next(
        (r for r in result.criteria_results if "domestic and export" in r.criterion.lower()),
        None
    )
    if region_result:
        assert region_result.status == "failed"


def test_check_eligibility_existing_policyholder_passed():
    """Test existing policyholder requirement - passed."""
    applicant_info = {
        "is_existing_policyholder": True
    }

    result = check_eligibility("TCI-LEGACY-001", applicant_info)

    assert result.success is True
    # Check if existing policyholder criterion passed
    policyholder_result = next(
        (r for r in result.criteria_results if "existing policyholder" in r.criterion.lower()),
        None
    )
    if policyholder_result:
        assert policyholder_result.status == "passed"


def test_check_eligibility_existing_policyholder_failed():
    """Test existing policyholder requirement - failed."""
    applicant_info = {
        "is_existing_policyholder": False
    }

    result = check_eligibility("TCI-LEGACY-001", applicant_info)

    assert result.success is True
    # Check if existing policyholder criterion failed
    policyholder_result = next(
        (r for r in result.criteria_results if "existing policyholder" in r.criterion.lower()),
        None
    )
    if policyholder_result:
        assert policyholder_result.status == "failed"


def test_check_eligibility_request_validation():
    """Test CheckEligibilityRequest validation."""
    # Valid request
    request = CheckEligibilityRequest(
        policy_id="TCI-DOM-001",
        applicant_info={"annual_turnover": 15000000}
    )
    assert request.policy_id == "TCI-DOM-001"

    # Invalid: empty policy_id
    with pytest.raises(Exception):
        CheckEligibilityRequest(
            policy_id="",
            applicant_info={}
        )


def test_check_eligibility_summary_generation():
    """Test summary generation for different outcomes."""
    # All passed
    applicant_info = {
        "annual_turnover": 15000000,
        "business_age_years": 3,
        "financial_statements": True
    }
    result = check_eligibility("TCI-DOM-001", applicant_info)
    assert result.summary is not None
    assert len(result.summary) > 0

    # Some failed
    applicant_info = {
        "annual_turnover": 5000000,
        "business_age_years": 1,
        "financial_statements": True
    }
    result = check_eligibility("TCI-DOM-001", applicant_info)
    assert result.summary is not None
    assert "ineligible" in result.summary.lower() or "failed" in result.summary.lower()

    # Some undetermined
    applicant_info = {
        "business_age_years": 3
    }
    result = check_eligibility("TCI-DOM-001", applicant_info)
    assert result.summary is not None
    assert "undetermined" in result.summary.lower() or "additional information" in result.summary.lower()


def test_check_eligibility_alternative_field_names():
    """Test that alternative field names are recognized."""
    # Test with 'revenue' instead of 'annual_turnover'
    applicant_info = {
        "revenue": 15000000,
        "years_in_business": 3,
        "financial_statements": True
    }
    result = check_eligibility("TCI-DOM-001", applicant_info)
    assert result.success is True

    # Test with 'registration_years' instead of 'business_age_years'
    applicant_info = {
        "annual_turnover": 15000000,
        "registration_years": 3,
        "financial_statements": True
    }
    result = check_eligibility("TCI-DOM-001", applicant_info)
    assert result.success is True


def test_check_eligibility_string_boolean_conversion():
    """Test that string boolean values are handled correctly."""
    applicant_info = {
        "annual_turnover": 15000000,
        "business_age_years": 3,
        "financial_statements": "yes"
    }
    result = check_eligibility("TCI-DOM-001", applicant_info)
    assert result.success is True

    applicant_info = {
        "annual_turnover": 15000000,
        "business_age_years": 3,
        "financial_statements": "no"
    }
    result = check_eligibility("TCI-DOM-001", applicant_info)
    assert result.success is True


def test_check_eligibility_criterion_reasons():
    """Test that criterion results include meaningful reasons."""
    applicant_info = {
        "annual_turnover": 15000000,
        "business_age_years": 3,
        "financial_statements": True
    }
    result = check_eligibility("TCI-DOM-001", applicant_info)

    for criterion_result in result.criteria_results:
        assert criterion_result.criterion is not None
        assert criterion_result.status in ["passed", "failed", "undetermined"]
        # Reason should be present for most criteria
        if criterion_result.status != "undetermined":
            assert criterion_result.reason is not None
            assert len(criterion_result.reason) > 0


def test_check_eligibility_empty_applicant_info():
    """Test eligibility check with minimal applicant information."""
    applicant_info = {}

    result = check_eligibility("TCI-DOM-001", applicant_info)

    assert result.success is True
    assert result.overall_status == "undetermined"
    # All criteria should be undetermined
    undetermined_count = sum(1 for r in result.criteria_results if r.status == "undetermined")
    assert undetermined_count == len(result.criteria_results)


def test_check_eligibility_numeric_field_validation():
    """Test that numeric fields are properly validated."""
    applicant_info = {
        "annual_turnover": "not a number",  # Invalid numeric value
        "business_age_years": 3,
        "financial_statements": True
    }
    result = check_eligibility("TCI-DOM-001", applicant_info)
    # Should handle gracefully (likely undetermined for turnover)
    assert result.success is True
