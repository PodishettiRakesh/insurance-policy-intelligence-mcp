"""Test source references and evidence tracking."""

from app.comparison import compare_policies
from app.eligibility import check_eligibility
from app.evidence_tracker import EvidenceTracker

def test_source_references():
    """Test source reference tracking in tool results."""
    print("Testing Source References and Evidence Tracking")
    print("=" * 60)

    # Test 1: Comparison with evidence metadata
    print("\n1. Test comparison with evidence metadata")
    result = compare_policies(['TCI-DOM-001', 'TCI-DOM-002'])
    print(f"   Success: {result.success}")
    print(f"   Has evidence: {result.evidence_metadata.has_evidence}")
    print(f"   Number of sources: {len(result.evidence_metadata.sources)}")
    for source in result.evidence_metadata.sources[:5]:
        print(f"   - [{source.policy_id}:{source.field}] = {source.display_value}")

    # Test 2: Eligibility with evidence metadata
    print("\n2. Test eligibility with evidence metadata")
    applicant_info = {
        "annual_turnover": 15000000,
        "business_age_years": 3,
        "financial_statements": True
    }
    result = check_eligibility("TCI-DOM-001", applicant_info)
    print(f"   Success: {result.success}")
    print(f"   Has evidence: {result.evidence_metadata.has_evidence}")
    print(f"   Number of sources: {len(result.evidence_metadata.sources)}")
    for source in result.evidence_metadata.sources:
        print(f"   - [{source.policy_id}:{source.field}] = {source.display_value}")

    # Test 3: Evidence tracker citation formatting
    print("\n3. Test evidence tracker citation formatting")
    tracker = EvidenceTracker()
    source = tracker.create_source_reference(
        policy_id="TCI-DOM-001",
        field="premium",
        value=25000,
        display_value="25000 INR"
    )
    citation = tracker.format_citation(source)
    print(f"   Citation: {citation}")

    # Test 4: Multiple sources citation
    print("\n4. Test multiple sources citation")
    sources = [
        tracker.create_source_reference("TCI-DOM-001", "premium", 25000, "25000 INR"),
        tracker.create_source_reference("TCI-DOM-002", "premium", 45000, "45000 INR"),
    ]
    citations = tracker.format_citations(sources)
    print(f"   Citations: {citations}")

    print("\n" + "=" * 60)
    print("Source references test complete!")

if __name__ == "__main__":
    test_source_references()
