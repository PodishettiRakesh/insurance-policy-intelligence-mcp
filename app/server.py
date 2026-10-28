"""MCP server for insurance policy search."""

from mcp.server import MCPServer
from typing import List, Optional

from app.search import search_policies, SearchValidationError
from app.comparison import compare_policies, ComparisonError
from app.eligibility import check_eligibility, EligibilityError


# Initialize MCP server
mcp = MCPServer("Insurance Policy Intelligence")


@mcp.tool()
def search_policies_tool(
    query: str,
    category: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10
) -> str:
    """
    Search insurance policies using keyword matching with optional filters.

    Args:
        query: Text to search for in policy title, description, coverage, and tags
        category: Restrict results to a specific policy category (optional)
        status: Restrict results to active or inactive policies (optional)
        limit: Maximum number of results to return (default 10, max 50)

    Returns:
        JSON string containing matching policies with their details
    """
    try:
        # Call the search function
        policies = search_policies(
            query=query,
            category=category,
            status=status,
            limit=limit
        )

        # Convert policies to dict for JSON serialization with date handling
        results = [policy.model_dump(mode='json') for policy in policies]

        # Return as JSON string
        import json
        return json.dumps({
            "success": True,
            "count": len(results),
            "results": results
        }, indent=2)

    except SearchValidationError as e:
        # Return error message for validation errors
        import json
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)
    except Exception as e:
        # Return error message for unexpected errors
        import json
        return json.dumps({
            "success": False,
            "error": f"An unexpected error occurred: {str(e)}"
        }, indent=2)


@mcp.tool()
def compare_policies_tool(
    policy_ids: List[str]
) -> str:
    """
    Compare multiple insurance policies side-by-side.

    Args:
        policy_ids: List of policy IDs to compare (2-5 policies)

    Returns:
        JSON string containing detailed comparison including coverage,
        exclusions, premiums, deductibles, and eligibility criteria
    """
    try:
        # Call the comparison function
        result = compare_policies(policy_ids=policy_ids)

        # Return as JSON string
        import json
        return json.dumps(result.model_dump(mode='json'), indent=2)

    except ComparisonError as e:
        # Return error message for comparison errors
        import json
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)
    except Exception as e:
        # Return error message for unexpected errors
        import json
        return json.dumps({
            "success": False,
            "error": f"An unexpected error occurred: {str(e)}"
        }, indent=2)


@mcp.tool()
def check_eligibility_tool(
    policy_id: str,
    applicant_info: dict
) -> str:
    """
    Evaluate whether an applicant meets a policy's eligibility criteria.

    Args:
        policy_id: The policy ID to check eligibility for
        applicant_info: Dictionary containing applicant information for evaluation
                        (e.g., annual_turnover, business_age_years, financial_statements, etc.)

    Returns:
        JSON string containing detailed eligibility evaluation with:
        - overall_status: 'eligible', 'ineligible', or 'undetermined'
        - criteria_results: List of individual criterion evaluations
        - summary: Human-readable summary of the evaluation
    """
    try:
        # Call the eligibility check function
        result = check_eligibility(policy_id=policy_id, applicant_info=applicant_info)

        # Return as JSON string
        import json
        return json.dumps(result.model_dump(mode='json'), indent=2)

    except EligibilityError as e:
        # Return error message for eligibility errors
        import json
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)
    except Exception as e:
        # Return error message for unexpected errors
        import json
        return json.dumps({
            "success": False,
            "error": f"An unexpected error occurred: {str(e)}"
        }, indent=2)


if __name__ == "__main__":
    # Run the server with stdio transport (default)
    mcp.run()
