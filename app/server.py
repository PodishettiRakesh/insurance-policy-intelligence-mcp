"""MCP server for insurance policy search."""

from mcp.server import MCPServer
from typing import Optional

from app.search import search_policies, SearchValidationError


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

        # Convert policies to dict for JSON serialization
        results = [policy.model_dump() for policy in policies]

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


if __name__ == "__main__":
    # Run the server with stdio transport (default)
    mcp.run()
