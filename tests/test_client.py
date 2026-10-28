"""Tests for MCP client connecting to server."""

import pytest
import json
import subprocess
import sys
from pathlib import Path


def get_server_process():
    """Start the MCP server as a subprocess."""
    base_dir = Path(__file__).parent.parent
    server_path = base_dir / "app" / "server.py"

    # Start server with stdio transport
    proc = subprocess.Popen(
        [sys.executable, "-m", "app.server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(base_dir)
    )
    return proc


def send_jsonrpc_request(proc, method, params=None):
    """Send a JSON-RPC request to the server."""
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method
    }
    if params:
        request["params"] = params

    request_str = json.dumps(request) + "\n"
    proc.stdin.write(request_str)
    proc.stdin.flush()

    # Read response
    response_line = proc.stdout.readline()
    if response_line:
        return json.loads(response_line)
    return None


def test_client_initialize():
    """Test client can initialize connection to server."""
    proc = get_server_process()

    try:
        # Send initialize request
        response = send_jsonrpc_request(proc, "initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        })

        assert response is not None
        assert "result" in response or "error" not in response
    finally:
        proc.terminate()
        proc.wait()


def test_client_list_tools():
    """Test client can list available tools."""
    proc = get_server_process()

    try:
        # Initialize first
        send_jsonrpc_request(proc, "initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        })

        # Send initialized notification
        send_jsonrpc_request(proc, "notifications/initialized")

        # List tools
        response = send_jsonrpc_request(proc, "tools/list")

        assert response is not None
        assert "result" in response
        assert "tools" in response["result"]
        assert len(response["result"]["tools"]) > 0

        # Check that search_policies_tool is in the list
        tool_names = [tool.get("name", "") for tool in response["result"]["tools"]]
        assert "search_policies_tool" in tool_names
    finally:
        proc.terminate()
        proc.wait()


def test_client_tool_schema():
    """Test client can inspect tool schema."""
    proc = get_server_process()

    try:
        # Initialize
        send_jsonrpc_request(proc, "initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        })
        send_jsonrpc_request(proc, "notifications/initialized")

        # List tools
        response = send_jsonrpc_request(proc, "tools/list")

        # Find search_policies_tool
        tools = response["result"]["tools"]
        search_tool = next((t for t in tools if t.get("name") == "search_policies_tool"), None)

        assert search_tool is not None
        assert "description" in search_tool
        assert "inputSchema" in search_tool

        # Check input schema has required fields
        input_schema = search_tool["inputSchema"]
        assert "properties" in input_schema
        assert "query" in input_schema["properties"]
        assert "category" in input_schema["properties"]
        assert "status" in input_schema["properties"]
        assert "limit" in input_schema["properties"]
    finally:
        proc.terminate()
        proc.wait()


def test_client_invoke_search_tool():
    """Test client can invoke search_policies_tool with a query."""
    proc = get_server_process()

    try:
        # Initialize
        send_jsonrpc_request(proc, "initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        })
        send_jsonrpc_request(proc, "notifications/initialized")

        # Invoke search tool
        response = send_jsonrpc_request(proc, "tools/call", {
            "name": "search_policies_tool",
            "arguments": {
                "query": "domestic",
                "limit": 5
            }
        })

        assert response is not None
        assert "result" in response

        # Extract the actual result text from MCP response format
        result = response["result"]
        if isinstance(result, dict) and "content" in result:
            result_text = result["content"][0]["text"]
        else:
            result_text = result

        # Parse the JSON result
        result_data = json.loads(result_text)
        assert result_data["success"] is True
        assert "count" in result_data
        assert "results" in result_data
        assert result_data["count"] > 0
        assert len(result_data["results"]) > 0

        # Verify result structure
        first_result = result_data["results"][0]
        assert "policy_id" in first_result
        assert "title" in first_result
        assert "category" in first_result
    finally:
        proc.terminate()
        proc.wait()


def test_client_invoke_search_with_filters():
    """Test client can invoke search with category and status filters."""
    proc = get_server_process()

    try:
        # Initialize
        send_jsonrpc_request(proc, "initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        })
        send_jsonrpc_request(proc, "notifications/initialized")

        # Invoke search with filters
        response = send_jsonrpc_request(proc, "tools/call", {
            "name": "search_policies_tool",
            "arguments": {
                "query": "insurance",
                "category": "Domestic Trade Credit",
                "status": "active",
                "limit": 3
            }
        })

        assert response is not None
        assert "result" in response

        # Extract the actual result text from MCP response format
        result = response["result"]
        if isinstance(result, dict) and "content" in result:
            result_text = result["content"][0]["text"]
        else:
            result_text = result

        result_data = json.loads(result_text)
        assert result_data["success"] is True

        # Verify filters are applied
        for result in result_data["results"]:
            assert result["category"] == "Domestic Trade Credit"
            assert result["status"] == "active"
    finally:
        proc.terminate()
        proc.wait()


def test_client_invoke_search_invalid_query():
    """Test client handles invalid query (empty string)."""
    proc = get_server_process()

    try:
        # Initialize
        send_jsonrpc_request(proc, "initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        })
        send_jsonrpc_request(proc, "notifications/initialized")

        # Invoke with empty query
        response = send_jsonrpc_request(proc, "tools/call", {
            "name": "search_policies_tool",
            "arguments": {
                "query": "",
                "limit": 5
            }
        })

        assert response is not None
        assert "result" in response

        # Extract the actual result text from MCP response format
        result = response["result"]
        if isinstance(result, dict) and "content" in result:
            result_text = result["content"][0]["text"]
        else:
            result_text = result

        result_data = json.loads(result_text)
        assert result_data["success"] is False
        assert "error" in result_data
        assert "empty" in result_data["error"].lower()
    finally:
        proc.terminate()
        proc.wait()


def test_client_invoke_search_no_matches():
    """Test client handles search with no matching results."""
    proc = get_server_process()

    try:
        # Initialize
        send_jsonrpc_request(proc, "initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        })
        send_jsonrpc_request(proc, "notifications/initialized")

        # Invoke with nonexistent query
        response = send_jsonrpc_request(proc, "tools/call", {
            "name": "search_policies_tool",
            "arguments": {
                "query": "nonexistentxyz123",
                "limit": 5
            }
        })

        assert response is not None
        assert "result" in response

        # Extract the actual result text from MCP response format
        result = response["result"]
        if isinstance(result, dict) and "content" in result:
            result_text = result["content"][0]["text"]
        else:
            result_text = result

        result_data = json.loads(result_text)
        assert result_data["success"] is True
        assert result_data["count"] == 0
        assert result_data["results"] == []
    finally:
        proc.terminate()
        proc.wait()
