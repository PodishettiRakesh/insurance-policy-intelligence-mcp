"""Policy catalogue loader and validation."""

import json
from pathlib import Path
from typing import List

from app.models import Policy


class CatalogueLoadError(Exception):
    """Exception raised when catalogue loading fails."""
    pass


def load_policies(file_path: str = "data/policies.json") -> List[Policy]:
    """
    Load and validate policies from a JSON file.

    Args:
        file_path: Path to the policies JSON file (relative to project root).

    Returns:
        List of validated Policy objects.

    Raises:
        CatalogueLoadError: If the file cannot be read or contains invalid data.
    """
    # Resolve file path relative to this file's directory
    base_dir = Path(__file__).parent.parent
    full_path = base_dir / file_path

    if not full_path.exists():
        raise CatalogueLoadError(f"Policy file not found: {full_path}")

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise CatalogueLoadError(f"Invalid JSON in policy file: {e}")
    except Exception as e:
        raise CatalogueLoadError(f"Error reading policy file: {e}")

    if not isinstance(data, list):
        raise CatalogueLoadError(f"Policy file must contain a list of policies, got {type(data).__name__}")

    policies = []
    validation_errors = []

    for idx, policy_data in enumerate(data):
        try:
            policy = Policy(**policy_data)
            policies.append(policy)
        except Exception as e:
            policy_id = policy_data.get("policy_id", f"index {idx}")
            validation_errors.append(f"Policy {policy_id}: {str(e)}")

    if validation_errors:
        error_msg = f"Failed to validate {len(validation_errors)} policy(s):\n" + "\n".join(validation_errors)
        raise CatalogueLoadError(error_msg)

    if not policies:
        raise CatalogueLoadError("No valid policies found in the catalogue")

    return policies


def get_catalogue() -> List[Policy]:
    """
    Get the policy catalogue (singleton pattern for in-memory loading).

    Returns:
        List of validated Policy objects.
    """
    return load_policies()
