"""Policy search functionality with filtering and validation."""

from typing import List, Optional

from app.catalogue import get_catalogue
from app.models import Policy


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
    Search policies using case-insensitive keyword matching with optional filters.

    Args:
        query: Text to search for (required, must not be empty)
        category: Restrict results to a specific category (optional)
        status: Restrict results to a specific status (optional)
        limit: Maximum number of results to return (default 10, max 50)

    Returns:
        List of matching Policy objects. Empty list if no matches found.

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

    # Normalize query for case-insensitive matching
    query_lower = query.strip().lower()

    # Filter policies
    results = []
    for policy in policies:
        # Apply category filter if provided
        if category and policy.category.lower() != category.lower():
            continue

        # Apply status filter if provided
        if status and policy.status.value.lower() != status.lower():
            continue

        # Check for keyword match in searchable fields
        searchable_text = (
            policy.title.lower() + " " +
            policy.description.lower() + " " +
            " ".join(policy.coverage).lower() + " " +
            " ".join(policy.tags).lower()
        )

        if query_lower in searchable_text:
            results.append(policy)

        # Stop if we've reached the limit
        if len(results) >= limit:
            break

    return results
