"""Policy search functionality with filtering and validation."""

from typing import List, Optional

from app.catalogue import get_catalogue
from app.models import Policy
from app.search_enhancements import (
    SynonymManager,
    rank_policies_by_relevance,
    normalize_text,
)


class SearchValidationError(Exception):
    """Exception raised for invalid search parameters."""
    pass


def search_policies(
    query: str,
    category: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10
) -> List[Policy]:
    """
    Search policies using relevance scoring with synonym support and optional filters.

    Args:
        query: Text to search for (required, must not be empty)
        category: Restrict results to a specific category (optional)
        status: Restrict results to a specific status (optional)
        limit: Maximum number of results to return (default 10, max 50)

    Returns:
        List of matching Policy objects ranked by relevance. Empty list if no matches found.

    Raises:
        SearchValidationError: If query is empty or limit is invalid.
    """
    # Validate query
    if not query or not query.strip():
        raise SearchValidationError("Query cannot be empty")

    # Validate limit
    if limit <= 0:
        raise SearchValidationError("Limit must be positive")
    if limit > 50:
        raise SearchValidationError("Limit cannot exceed 50")

    # Get all policies
    policies = get_catalogue()

    # Initialize synonym manager
    synonym_manager = SynonymManager()

    # Normalize query
    query_normalized = normalize_text(query.strip())

    # Filter policies by category and status first
    filtered_policies = []
    for policy in policies:
        # Apply category filter if provided
        if category and policy.category.lower() != category.lower():
            continue

        # Apply status filter if provided
        if status and policy.status.value.lower() != status.lower():
            continue

        filtered_policies.append(policy)

    # Rank policies by relevance
    scored_policies = rank_policies_by_relevance(
        filtered_policies,
        query_normalized,
        synonym_manager
    )

    # Filter out policies with zero score (no matches)
    matching_policies = [
        (policy, score) for policy, score in scored_policies if score > 0
    ]

    # Return top N policies (without scores)
    results = [policy for policy, score in matching_policies[:limit]]

    return results
