"""Test structured comparison enhancements."""

from app.comparison import compare_policies

def test_structured_comparison():
    """Test the new structured comparison models and features."""
    print("Testing Structured Comparison Enhancements")
    print("=" * 60)

    # Test 1: Compare two domestic policies
    print("\n1. Comparing TCI-DOM-001 and TCI-DOM-002")
    result = compare_policies(['TCI-DOM-001', 'TCI-DOM-002'])

    print(f"   Success: {result.success}")
    print(f"   Summary: {result.summary}")
    print(f"   Coverage common items: {len(result.coverage_comparison.get('common_items', []))}")
    print(f"   Premium amounts: {result.premium_comparison.get('amounts_by_policy', {})}")
    print(f"   Same currency: {result.premium_comparison.get('same_currency', False)}")
    print(f"   Relative difference: {result.premium_comparison.get('relative_difference', None)}")
    print(f"   Has deductible: {result.deductible_comparison.get('has_deductible', [])}")
    print(f"   Missing deductible: {result.deductible_comparison.get('missing_deductible', [])}")

    # Test 2: Compare three policies
    print("\n2. Comparing TCI-DOM-001, TCI-DOM-002, TCI-DOM-003")
    result2 = compare_policies(['TCI-DOM-001', 'TCI-DOM-002', 'TCI-DOM-003'])

    print(f"   Success: {result2.success}")
    print(f"   Summary: {result2.summary}")
    print(f"   Coverage counts: {result2.coverage_comparison.get('coverage_counts', {})}")
    print(f"   Premium amounts: {result2.premium_comparison.get('amounts_by_policy', {})}")

    # Test 3: Check for missing fields
    print("\n3. Checking missing fields identification")
    print(f"   Missing fields: {result.missing_fields}")

    # Test 4: Test fuzzy matching (if there are similar coverage items)
    print("\n4. Checking coverage comparison with fuzzy matching")
    coverage_unique = result.coverage_comparison.get('unique_by_policy', {})
    for pid, items in coverage_unique.items():
        print(f"   {pid} unique coverage items: {len(items)}")

    print("\n" + "=" * 60)
    print("Structured comparison test complete!")

if __name__ == "__main__":
    test_structured_comparison()
