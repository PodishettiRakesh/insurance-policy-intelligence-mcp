"""Tests for policy catalogue loading."""

import json
import pytest
from pathlib import Path

from app.catalogue import load_policies, CatalogueLoadError


def test_load_policies_success():
    """Test successful loading of policies from JSON file."""
    policies = load_policies()
    assert len(policies) > 0
    assert all(policy.policy_id for policy in policies)
    assert all(policy.title for policy in policies)


def test_load_policies_all_valid():
    """Test that all loaded policies are valid Policy objects."""
    policies = load_policies()
    for policy in policies:
        assert policy.policy_id is not None
        assert policy.title is not None
        assert policy.category is not None
        assert policy.provider is not None
        assert policy.description is not None
        assert len(policy.coverage) > 0
        assert policy.premium is not None
        assert policy.status in ["active", "inactive"]


def test_load_policies_file_not_found():
    """Test error handling when policy file doesn't exist."""
    with pytest.raises(CatalogueLoadError) as exc_info:
        load_policies("nonexistent/policies.json")
    assert "not found" in str(exc_info.value).lower()


def test_load_policies_invalid_json(tmp_path):
    """Test error handling for invalid JSON."""
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("{ invalid json }")

    with pytest.raises(CatalogueLoadError) as exc_info:
        load_policies(str(invalid_file))
    assert "invalid json" in str(exc_info.value).lower()


def test_load_policies_not_a_list(tmp_path):
    """Test error handling when JSON doesn't contain a list."""
    not_list_file = tmp_path / "not_list.json"
    not_list_file.write_text('{"policy": "data"}')

    with pytest.raises(CatalogueLoadError) as exc_info:
        load_policies(str(not_list_file))
    assert "list" in str(exc_info.value).lower()


def test_load_policies_invalid_policy_data(tmp_path):
    """Test error handling for invalid policy data."""
    invalid_policies_file = tmp_path / "invalid_policies.json"
    invalid_policies_file.write_text(json.dumps([
        {
            "policy_id": "VALID-001",
            "title": "Valid Policy",
            "category": "Test",
            "provider": "Test Provider",
            "description": "Test",
            "coverage": ["Coverage"],
            "premium": {"amount": 1000, "currency": "INR", "period": "annual"},
            "status": "active"
        },
        {
            "policy_id": "INVALID-001",
            # Missing required fields
            "title": "Invalid Policy"
        }
    ]))

    with pytest.raises(CatalogueLoadError) as exc_info:
        load_policies(str(invalid_policies_file))
    assert "validation" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()


def test_load_policies_empty_list(tmp_path):
    """Test error handling for empty policy list."""
    empty_file = tmp_path / "empty.json"
    empty_file.write_text("[]")

    with pytest.raises(CatalogueLoadError) as exc_info:
        load_policies(str(empty_file))
    assert "no valid policies" in str(exc_info.value).lower()


def test_get_catalogue():
    """Test get_catalogue function returns policies."""
    from app.catalogue import get_catalogue
    policies = get_catalogue()
    assert len(policies) > 0
    assert isinstance(policies, list)
