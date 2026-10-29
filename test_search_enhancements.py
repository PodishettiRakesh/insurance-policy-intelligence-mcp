"""Test search enhancements: synonym support and relevance scoring."""

from app.search import search_policies

def test_search_enhancements():
    """Test the new search features."""
    print("Testing Search Enhancements")
    print("=" * 60)

    # Test 1: Basic search with original functionality
    print("\n1. Basic search: 'domestic'")
    results = search_policies("domestic", limit=5)
    print(f"   Found {len(results)} policies")
    for policy in results:
        print(f"   - {policy.policy_id}: {policy.title}")

    # Test 2: Search with synonym
    print("\n2. Search with synonym: 'local' (should match 'domestic')")
    results = search_policies("local", limit=5)
    print(f"   Found {len(results)} policies")
    for policy in results:
        print(f"   - {policy.policy_id}: {policy.title}")

    # Test 3: Search with synonym
    print("\n3. Search with synonym: 'SME' (should match small business)")
    results = search_policies("SME", limit=5)
    print(f"   Found {len(results)} policies")
    for policy in results:
        print(f"   - {policy.policy_id}: {policy.title}")

    # Test 4: Search with synonym
    print("\n4. Search with synonym: 'export' (should match overseas)")
    results = search_policies("export", limit=5)
    print(f"   Found {len(results)} policies")
    for policy in results:
        print(f"   - {policy.policy_id}: {policy.title}")

    # Test 5: Search with category filter
    print("\n5. Search with category filter: 'domestic' in 'Domestic Trade Credit'")
    results = search_policies("domestic", category="Domestic Trade Credit", limit=5)
    print(f"   Found {len(results)} policies")
    for policy in results:
        print(f"   - {policy.policy_id}: {policy.title}")

    # Test 6: Search for coverage term
    print("\n6. Search for coverage term: 'insolvency'")
    results = search_policies("insolvency", limit=5)
    print(f"   Found {len(results)} policies")
    for policy in results:
        print(f"   - {policy.policy_id}: {policy.title}")

    # Test 7: Search with synonym for coverage
    print("\n7. Search with synonym: 'bankruptcy' (should match 'insolvency')")
    results = search_policies("bankruptcy", limit=5)
    print(f"   Found {len(results)} policies")
    for policy in results:
        print(f"   - {policy.policy_id}: {policy.title}")

    print("\n" + "=" * 60)
    print("Search enhancements test complete!")

if __name__ == "__main__":
    test_search_enhancements()
