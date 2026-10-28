"""Tests for MCP server configuration."""

import pytest


def test_server_import():
    """Test that the server module can be imported."""
    from app.server import mcp
    assert mcp is not None


def test_server_tool_registered():
    """Test that search_policies_tool function exists."""
    from app.server import search_policies_tool
    assert search_policies_tool is not None
    assert callable(search_policies_tool)


def test_server_tool_signature():
    """Test that the tool has the correct signature."""
    from app.server import search_policies_tool
    import inspect

    sig = inspect.signature(search_policies_tool)
    params = sig.parameters

    # Check required parameters
    assert 'query' in params
    assert 'category' in params
    assert 'status' in params
    assert 'limit' in params

    # Check that query has no default (required)
    assert params['query'].default is inspect.Parameter.empty

    # Check that others have defaults (optional)
    assert params['category'].default is None
    assert params['status'].default is None
    assert params['limit'].default == 10
