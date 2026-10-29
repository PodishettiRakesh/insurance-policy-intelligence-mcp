"""Test eligibility enhancements: explicit rules and deterministic evaluation."""

from app.eligibility import check_eligibility

def test_eligibility_enhancements():
    """Test the new rule-based eligibility evaluation."""
    print("Testing Eligibility Enhancements")
    print("=" * 60)

    # Test 1: Check eligibility with sufficient information
    print("\n1. Check eligibility with sufficient information")
    applicant_info = {
        "annual_turnover": 15000000,
        "business_age_years": 3,
        "financial_statements": True
    }
    result = check_eligibility("TCI-DOM-001", applicant_info)
    print(f"   Policy: {result.policy_title}")
    print(f"   Overall Status: {result.overall_status}")
    print(f"   Criteria evaluated: {len(result.criteria_results)}")
    for cr in result.criteria_results:
        print(f"   - {cr.status}: {cr.reason}")

    # Test 2: Check eligibility with insufficient turnover
    print("\n2. Check eligibility with insufficient turnover")
    applicant_info = {
        "annual_turnover": 5000000,
        "business_age_years": 3,
        "financial_statements": True
    }
    result = check_eligibility("TCI-DOM-001", applicant_info)
    print(f"   Policy: {result.policy_title}")
    print(f"   Overall Status: {result.overall_status}")
    for cr in result.criteria_results:
        print(f"   - {cr.status}: {cr.reason}")

    # Test 3: Check eligibility with missing information
    print("\n3. Check eligibility with missing information")
    applicant_info = {
        "financial_statements": True
    }
    result = check_eligibility("TCI-DOM-001", applicant_info)
    print(f"   Policy: {result.policy_title}")
    print(f"   Overall Status: {result.overall_status}")
    for cr in result.criteria_results:
        print(f"   - {cr.status}: {cr.reason}")

    # Test 4: Check eligibility for SME policy (under turnover threshold)
    print("\n4. Check eligibility for SME policy (under turnover threshold)")
    applicant_info = {
        "annual_turnover": 8000000,
        "business_age_years": 2,
        "financial_statements": True
    }
    result = check_eligibility("TCI-DOM-003", applicant_info)
    print(f"   Policy: {result.policy_title}")
    print(f"   Overall Status: {result.overall_status}")
    for cr in result.criteria_results:
        print(f"   - {cr.status}: {cr.reason}")

    # Test 5: Check eligibility for export policy with export years
    print("\n5. Check eligibility for export policy with export years")
    applicant_info = {
        "annual_turnover": 20000000,
        "export_years": 5,
        "export_license": True,
        "audited_financial_statements": True
    }
    result = check_eligibility("TCI-EXP-001", applicant_info)
    print(f"   Policy: {result.policy_title}")
    print(f"   Overall Status: {result.overall_status}")
    for cr in result.criteria_results:
        print(f"   - {cr.status}: {cr.reason}")

    print("\n" + "=" * 60)
    print("Eligibility enhancements test complete!")

if __name__ == "__main__":
    test_eligibility_enhancements()
