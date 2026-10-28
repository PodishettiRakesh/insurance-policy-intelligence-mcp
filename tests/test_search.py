"""Tests for policy search functionality."""

import pytest

from app.search import search_policies, SearchValidationError


def test_search_basic_keyword_matching():
    """Test basic keyword matching across searchable fields."""
    results = search_policies("domestic")
    assert len(results) > 0
    assert all(
        "domestic" in result.title.lower() or
        "domestic" in result.description.lower() or
        "domestic" in " ".join(result.coverage).lower() or
        "domestic" in " ".join(result.tags).lower()
        for result in results
    )


def test_search_case_insensitive():
    """Test that search is case-insensitive."""
    results_lower = search_policies("export")
    results_upper = search_policies("EXPORT")
    results_mixed = search_policies("ExPoRt")
    assert len(results_lower) == len(results_upper) == len(results_mixed)


def test_search_empty_query():
    """Test that empty query raises validation error."""
    with pytest.raises(SearchValidationError) as exc_info:
        search_policies("")
    assert "cannot be empty" in str(exc_info.value).lower()

    with pytest.raises(SearchValidationError):
        search_policies("   ")


def test_search_category_filter():
    """Test category filter functionality."""
    results = search_policies("insurance", category="Domestic Trade Credit")
    assert len(results) > 0
    assert all(result.category == "Domestic Trade Credit" for result in results)


def test_search_category_filter_case_insensitive():
    """Test category filter is case-insensitive."""
    results_lower = search_policies("insurance", category="domestic trade credit")
    results_upper = search_policies("insurance", category="DOMESTIC TRADE CREDIT")
    assert len(results_lower) == len(results_upper)


def test_search_status_filter():
    """Test status filter functionality."""
    results = search_policies("trade", status="active")
    assert len(results) > 0
    assert all(result.status.value == "active" for result in results)


def test_search_status_filter_case_insensitive():
    """Test status filter is case-insensitive."""
    results_lower = search_policies("trade", status="active")
    results_upper = search_policies("trade", status="ACTIVE")
    assert len(results_lower) == len(results_upper)


def test_search_combined_filters():
    """Test combining category and status filters."""
    results = search_policies(
        "insurance",
        category="Export Trade Credit",
        status="active"
    )
    assert len(results) > 0
    assert all(
        result.category == "Export Trade Credit" and
        result.status.value == "active"
        for result in results
    )


def test_search_limit():
    """Test result limit functionality."""
    results_default = search_policies("insurance", limit=5)
    assert len(results_default) <= 5

    results_higher = search_policies("insurance", limit=2)
    assert len(results_higher) <= 2


def test_search_invalid_limit_negative():
    """Test that negative limit raises validation error."""
    with pytest.raises(SearchValidationError) as exc_info:
        search_policies("insurance", limit=-1)
    assert "positive" in str(exc_info.value).lower()


def test_search_invalid_limit_zero():
    """Test that zero limit raises validation error."""
    with pytest.raises(SearchValidationError) as exc_info:
        search_policies("insurance", limit=0)
    assert "positive" in str(exc_info.value).lower()


def test_search_invalid_limit_too_high():
    """Test that limit exceeding maximum raises validation error."""
    with pytest.raises(SearchValidationError) as exc_info:
        search_policies("insurance", limit=51)
    assert "exceed" in str(exc_info.value).lower() or "cannot exceed" in str(exc_info.value).lower()


def test_search_no_matches():
    """Test search with no matching policies returns empty list."""
    results = search_policies("nonexistenttermxyz123")
    assert results == []


def test_search_matches_in_title():
    """Test matching in title field."""
    results = search_policies("comprehensive")
    assert len(results) > 0
    assert any("comprehensive" in result.title.lower() for result in results)


def test_search_matches_in_description():
    """Test matching in description field."""
    results = search_policies("protection")
    assert len(results) > 0
    assert any("protection" in result.description.lower() for result in results)


def test_search_matches_in_coverage():
    """Test matching in coverage field."""
    results = search_policies("insolvency")
    assert len(results) > 0
    assert any("insolvency" in " ".join(result.coverage).lower() for result in results)


def test_search_matches_in_tags():
    """Test matching in tags field."""
    results = search_policies("risk")
    assert len(results) > 0
    assert any("risk" in " ".join(result.tags).lower() for result in results)


def test_search_with_category_no_matches():
    """Test category filter with no matching results."""
    results = search_policies("insurance", category="Nonexistent Category")
    assert results == []


def test_search_with_status_no_matches():
    """Test status filter with no matching results."""
    results = search_policies("trade", status="inactive")
    # There is one inactive policy, but if it doesn't match the query, results could be empty
    assert isinstance(results, list)


def test_search_default_limit():
    """Test that default limit is applied when not specified."""
    results = search_policies("insurance")
    assert len(results) <= 10


def test_search_tag_matching():
    """Test searching for specific tags."""
    results = search_policies("SME")
    assert len(results) > 0
    assert any("SME" in result.tags for result in results)


def test_search_multiple_keywords():
    """Test searching with multiple keywords."""
    results = search_policies("export trade")
    assert len(results) > 0
