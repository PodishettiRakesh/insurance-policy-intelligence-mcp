"""MCP client integration layer for connecting to the insurance policy MCP server."""

import json
import subprocess
import sys
from typing import Any, Dict, List, Optional
from pathlib import Path


class MCPClientError(Exception):
    """Exception raised for MCP client errors."""
    pass


class MCPClient:
    """
    Client wrapper for connecting to the MCP server and invoking tools.

    This client manages the subprocess lifecycle and handles JSON-RPC communication
    with the MCP server via stdio transport.
    """

    def __init__(self, server_path: Optional[str] = None):
        """
        Initialize the MCP client.

        Args:
            server_path: Path to the MCP server module (default: app.server)
        """
        self.base_dir = Path(__file__).parent.parent
        self.server_path = server_path or "app.server"
        self.process: Optional[subprocess.Popen] = None
        self._initialized = False

    def __enter__(self):
        """Context manager entry - start the server and initialize connection."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close the connection."""
        self.close()

    def connect(self):
        """
        Start the MCP server process and initialize the connection.

        Raises:
            MCPClientError: If server fails to start or initialize
        """
        if self.process is not None:
            return  # Already connected

        # Start the MCP server as a subprocess with stdio transport
        try:
            self.process = subprocess.Popen(
                [sys.executable, "-m", self.server_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.base_dir)
            )
        except Exception as e:
            raise MCPClientError(f"Failed to start MCP server: {e}")

        # Initialize the connection
        try:
            response = self._send_request("initialize", {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {
                    "name": "langgraph-agent",
                    "version": "1.0.0"
                }
            })

            if response is None or "error" in response:
                raise MCPClientError(f"Failed to initialize MCP server: {response}")

            # Send initialized notification
            self._send_notification("notifications/initialized")
            self._initialized = True

        except Exception as e:
            self.close()
            raise MCPClientError(f"Failed to initialize MCP connection: {e}")

    def close(self):
        """Close the MCP server connection and cleanup subprocess."""
        if self.process is not None:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            finally:
                self.process = None
                self._initialized = False

    def _send_request(self, method: str, params: Optional[Dict] = None) -> Dict:
        """
        Send a JSON-RPC request to the MCP server.

        Args:
            method: JSON-RPC method name
            params: Optional parameters for the request

        Returns:
            Response dictionary from the server

        Raises:
            MCPClientError: If request fails or returns an error
        """
        if self.process is None:
            raise MCPClientError("MCP server is not connected")

        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method
        }
        if params:
            request["params"] = params

        request_str = json.dumps(request) + "\n"

        try:
            self.process.stdin.write(request_str)
            self.process.stdin.flush()

            response_line = self.process.stdout.readline()
            if not response_line:
                raise MCPClientError("No response from MCP server")

            response = json.loads(response_line)

            if "error" in response:
                raise MCPClientError(f"MCP server error: {response['error']}")

            return response

        except json.JSONDecodeError as e:
            raise MCPClientError(f"Failed to parse MCP response: {e}")
        except Exception as e:
            raise MCPClientError(f"Failed to send request to MCP server: {e}")

    def _send_notification(self, method: str, params: Optional[Dict] = None):
        """
        Send a JSON-RPC notification (no response expected).

        Args:
            method: JSON-RPC method name
            params: Optional parameters for the notification
        """
        if self.process is None:
            raise MCPClientError("MCP server is not connected")

        request = {
            "jsonrpc": "2.0",
            "method": method
        }
        if params:
            request["params"] = params

        request_str = json.dumps(request) + "\n"

        try:
            self.process.stdin.write(request_str)
            self.process.stdin.flush()
        except Exception as e:
            raise MCPClientError(f"Failed to send notification to MCP server: {e}")

    def _extract_result_text(self, response: Dict) -> str:
        """
        Extract the actual result text from MCP response format.

        Args:
            response: Response dictionary from MCP server

        Returns:
            Result text as string
        """
        result = response.get("result", {})
        if isinstance(result, dict) and "content" in result:
            # MCP standard format with content array
            content = result["content"]
            if isinstance(content, list) and len(content) > 0:
                return content[0].get("text", "")
        return str(result)

    def list_tools(self) -> List[Dict]:
        """
        List all available tools from the MCP server.

        Returns:
            List of tool dictionaries with name, description, and inputSchema

        Raises:
            MCPClientError: If listing tools fails
        """
        response = self._send_request("tools/list")
        return response.get("result", {}).get("tools", [])

    def search_policies(
        self,
        query: str,
        category: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Search insurance policies using keyword matching with optional filters.

        Args:
            query: Text to search for in policy title, description, coverage, and tags
            category: Restrict results to a specific policy category (optional)
            status: Restrict results to active or inactive policies (optional)
            limit: Maximum number of results to return (default 10, max 50)

        Returns:
            Dictionary with search results:
            {
                "success": bool,
                "count": int,
                "results": List[Dict]  # Policy details
            }

        Raises:
            MCPClientError: If search fails
        """
        response = self._send_request("tools/call", {
            "name": "search_policies_tool",
            "arguments": {
                "query": query,
                "category": category,
                "status": status,
                "limit": limit
            }
        })

        result_text = self._extract_result_text(response)
        return json.loads(result_text)

    def compare_policies(self, policy_ids: List[str]) -> Dict[str, Any]:
        """
        Compare multiple insurance policies side-by-side.

        Args:
            policy_ids: List of policy IDs to compare (2-5 policies)

        Returns:
            Dictionary with comparison results:
            {
                "success": bool,
                "policies": List[Dict],
                "coverage_comparison": Dict,
                "exclusions_comparison": Dict,
                "premium_comparison": Dict,
                "deductible_comparison": Dict,
                "eligibility_comparison": Dict,
                "missing_fields": Dict
            }

        Raises:
            MCPClientError: If comparison fails
        """
        response = self._send_request("tools/call", {
            "name": "compare_policies_tool",
            "arguments": {
                "policy_ids": policy_ids
            }
        })

        result_text = self._extract_result_text(response)
        return json.loads(result_text)

    def check_eligibility(
        self,
        policy_id: str,
        applicant_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate whether an applicant meets a policy's eligibility criteria.

        Args:
            policy_id: The policy ID to check eligibility for
            applicant_info: Dictionary containing applicant information for evaluation
                            (e.g., annual_turnover, business_age_years, financial_statements, etc.)

        Returns:
            Dictionary with eligibility evaluation:
            {
                "success": bool,
                "policy_id": str,
                "policy_title": str,
                "overall_status": str,  # 'eligible', 'ineligible', or 'undetermined'
                "criteria_results": List[Dict],
                "summary": str
            }

        Raises:
            MCPClientError: If eligibility check fails
        """
        response = self._send_request("tools/call", {
            "name": "check_eligibility_tool",
            "arguments": {
                "policy_id": policy_id,
                "applicant_info": applicant_info
            }
        })

        result_text = self._extract_result_text(response)
        return json.loads(result_text)
