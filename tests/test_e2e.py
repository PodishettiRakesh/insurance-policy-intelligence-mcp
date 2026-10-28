"""End-to-end integration tests for the complete MCP server-client flow."""

import pytest
import json
import subprocess
import sys
from pathlib import Path


def get_server_process():
    """Start the MCP server as a subprocess."""
    base_dir = Path(__file__).parent.parent
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

    response_line = proc.stdout.readline()
    if response_line:
        return json.loads(response_line)
    return None


def extract_result_text(response):
    """Extract the actual result text from MCP response format."""
    result = response["result"]
    if isinstance(result, dict) and "content" in result:
        return result["content"][0]["text"]
    return result


def test_e2e_complete_flow():
    """End-to-end test covering the complete client-server flow."""
    proc = get_server_process()

    try:
        # Test 1: Initialize connection
        response = send_jsonrpc_request(proc, "initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "e2e-test-client", "version": "1.0.0"}
        })
        assert response is not None
        assert "result" in response

        # Send initialized notification
        send_jsonrpc_request(proc, "notifications/initialized")

        # Test 2: Discover registered tool
        response = send_jsonrpc_request(proc, "tools/list")
        assert response is not None
        assert "result" in response
        tools = response["result"]["tools"]
        tool_names = [tool.get("name", "") for tool in tools]
        assert "search_policies_tool" in tool_names

        # Test 3: Search for known policy
        response = send_jsonrpc_request(proc, "tools/call", {
            "name": "search_policies_tool",
            "arguments": {
                "query": "domestic",
                "limit": 5
            }
        })
        assert response is not None
        result_text = extract_result_text(response)
        result_data = json.loads(result_text)
        assert result_data["success"] is True
        assert result_data["count"] > 0
        assert len(result_data["results"]) > 0
        # Verify result structure
        assert "policy_id" in result_data["results"][0]
        assert "title" in result_data["results"][0]

        # Test 4: Apply category filter
        response = send_jsonrpc_request(proc, "tools/call", {
            "name": "search_policies_tool",
            "arguments": {
                "query": "insurance",
                "category": "Export Trade Credit",
                "limit": 3
            }
        })
        assert response is not None
        result_text = extract_result_text(response)
        result_data = json.loads(result_text)
        assert result_data["success"] is True
        for result in result_data["results"]:
            assert result["category"] == "Export Trade Credit"

        # Test 5: Apply status filter
        response = send_jsonrpc_request(proc, "tools/call", {
            "name": "search_policies_tool",
            "arguments": {
                "query": "trade",
                "status": "active",
                "limit": 5
            }
        })
        assert response is not None
        result_text = extract_result_text(response)
        result_data = json.loads(result_text)
        assert result_data["success"] is True
        for result in result_data["results"]:
            assert result["status"] == "active"

        # Test 6: Search for nonexistent policy (verify empty result)
        response = send_jsonrpc_request(proc, "tools/call", {
            "name": "search_policies_tool",
            "arguments": {
                "query": "nonexistentxyz123",
                "limit": 5
            }
        })
        assert response is not None
        result_text = extract_result_text(response)
        result_data = json.loads(result_text)
        assert result_data["success"] is True
        assert result_data["count"] == 0
        assert result_data["results"] == []

        # Test 7: Test invalid input handling (empty query)
        response = send_jsonrpc_request(proc, "tools/call", {
            "name": "search_policies_tool",
            "arguments": {
                "query": "",
                "limit": 5
            }
        })
        assert response is not None
        result_text = extract_result_text(response)
        result_data = json.loads(result_text)
        assert result_data["success"] is False
        assert "error" in result_data
        assert "empty" in result_data["error"].lower()

    finally:
        proc.terminate()
        proc.wait()


def test_e2e_combined_filters():
    """End-to-end test with combined category and status filters."""
    proc = get_server_process()

    try:
        # Initialize
        send_jsonrpc_request(proc, "initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "e2e-test-client", "version": "1.0.0"}
        })
        send_jsonrpc_request(proc, "notifications/initialized")

        # Search with combined filters
        response = send_jsonrpc_request(proc, "tools/call", {
            "name": "search_policies_tool",
            "arguments": {
                "query": "credit",
                "category": "Single Buyer",
                "status": "active",
                "limit": 5
            }
        })

        assert response is not None
        result_text = extract_result_text(response)
        result_data = json.loads(result_text)
        assert result_data["success"] is True

        # Verify both filters are applied
        for result in result_data["results"]:
            assert result["category"] == "Single Buyer"
            assert result["status"] == "active"

    finally:
        proc.terminate()
        proc.wait()


def test_e2e_limit_enforcement():
    """End-to-end test to verify result limit is enforced."""
    proc = get_server_process()

    try:
        # Initialize
        send_jsonrpc_request(proc, "initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "e2e-test-client", "version": "1.0.0"}
        })
        send_jsonrpc_request(proc, "notifications/initialized")

        # Search with low limit
        response = send_jsonrpc_request(proc, "tools/call", {
            "name": "search_policies_tool",
            "arguments": {
                "query": "insurance",
                "limit": 2
            }
        })

        assert response is not None
        result_text = extract_result_text(response)
        result_data = json.loads(result_text)
        assert result_data["success"] is True
        assert len(result_data["results"]) <= 2

    finally:
        proc.terminate()
        proc.wait()
