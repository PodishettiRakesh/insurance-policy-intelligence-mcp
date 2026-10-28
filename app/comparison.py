"""Policy comparison service."""

from typing import Dict, List, Set
from pydantic import ValidationError

from app.catalogue import get_catalogue
from app.models import (
    ComparePoliciesRequest,
    ComparisonResult,
    Policy,
    PolicyComparisonItem,
)


class ComparisonError(Exception):
    """Exception raised for comparison errors."""
    pass


def compare_policies(policy_ids: List[str]) -> ComparisonResult:
    """
    Compare multiple policies side-by-side.

    Args:
        policy_ids: List of policy IDs to compare (2-5 policies)

    Returns:
        ComparisonResult with detailed comparison data

    Raises:
        ComparisonError: If policy IDs are invalid or comparison fails
    """
    # Validate request
    try:
        request = ComparePoliciesRequest(policy_ids=policy_ids)
    except ValidationError as e:
        raise ComparisonError(str(e))

    # Get all policies
    catalogue = get_catalogue()
    catalogue_dict = {p.policy_id: p for p in catalogue}

    # Check all policy IDs exist
    missing_ids = [pid for pid in request.policy_ids if pid not in catalogue_dict]
    if missing_ids:
        raise ComparisonError(f"Policy ID(s) not found: {', '.join(missing_ids)}")

    # Retrieve policies
    policies = [catalogue_dict[pid] for pid in request.policy_ids]

    # Build comparison items
    comparison_items = []
    for policy in policies:
        comparison_items.append(PolicyComparisonItem(
            policy_id=policy.policy_id,
            title=policy.title,
            category=policy.category,
            provider=policy.provider,
            coverage=policy.coverage,
            exclusions=policy.exclusions,
            premium=policy.premium.model_dump(),
            deductible=policy.deductible.model_dump() if policy.deductible else None,
            eligibility=policy.eligibility.model_dump() if policy.eligibility else None
        ))

    # Compare coverage
    coverage_comparison = _compare_lists(
        [p.coverage for p in policies],
        request.policy_ids,
        "coverage"
    )

    # Compare exclusions
    exclusions_comparison = _compare_lists(
        [p.exclusions for p in policies],
        request.policy_ids,
        "exclusions"
    )

    # Compare premiums
    premium_comparison = _compare_premiums(policies, request.policy_ids)

    # Compare deductibles
    deductible_comparison = _compare_deductibles(policies, request.policy_ids)

    # Compare eligibility
    eligibility_comparison = _compare_eligibility(policies, request.policy_ids)

    # Identify missing fields
    missing_fields = _identify_missing_fields(policies, request.policy_ids)

    return ComparisonResult(
        success=True,
        policies=comparison_items,
        coverage_comparison=coverage_comparison,
        exclusions_comparison=exclusions_comparison,
        premium_comparison=premium_comparison,
        deductible_comparison=deductible_comparison,
        eligibility_comparison=eligibility_comparison,
        missing_fields=missing_fields
    )


def _compare_lists(
    lists: List[List[str]],
    policy_ids: List[str],
    field_name: str
) -> Dict[str, any]:
    """Compare lists of strings across policies."""
    # Find common items
    if not lists:
        return {"common": [], "unique_by_policy": {}}

    common = set(lists[0])
    for lst in lists[1:]:
        common.intersection_update(lst)

    # Find unique items per policy
    unique_by_policy = {}
    for i, (lst, pid) in enumerate(zip(lists, policy_ids)):
        unique = set(lst) - common
        unique_by_policy[pid] = list(unique)

    return {
        "common": list(common),
        "unique_by_policy": unique_by_policy,
        "count_by_policy": {pid: len(lst) for pid, lst in zip(policy_ids, lists)}
    }


def _compare_premiums(policies: List[Policy], policy_ids: List[str]) -> Dict[str, any]:
    """Compare premiums across policies."""
    premiums = {}
    currencies = set()

    for policy, pid in zip(policies, policy_ids):
        premiums[pid] = {
            "amount": policy.premium.amount,
            "currency": policy.premium.currency,
            "period": policy.premium.period
        }
        currencies.add(policy.premium.currency)

    return {
        "by_policy": premiums,
        "currencies": list(currencies),
        "same_currency": len(currencies) == 1,
        "note": "Currency comparison not performed - no exchange rate conversion" if len(currencies) > 1 else None
    }


def _compare_deductibles(policies: List[Policy], policy_ids: List[str]) -> Dict[str, any]:
    """Compare deductibles across policies."""
    deductibles = {}
    has_deductible = []
    missing_deductible = []

    for policy, pid in zip(policies, policy_ids):
        if policy.deductible:
            deductibles[pid] = {
                "amount": policy.deductible.amount,
                "currency": policy.deductible.currency
            }
            has_deductible.append(pid)
        else:
            missing_deductible.append(pid)

    return {
        "by_policy": deductibles,
        "has_deductible": has_deductible,
        "missing_deductible": missing_deductible
    }


def _compare_eligibility(policies: List[Policy], policy_ids: List[str]) -> Dict[str, any]:
    """Compare eligibility criteria across policies."""
    eligibility_data = {}
    has_eligibility = []
    missing_eligibility = []

    for policy, pid in zip(policies, policy_ids):
        if policy.eligibility:
            eligibility_data[pid] = policy.eligibility.model_dump()
            has_eligibility.append(pid)
        else:
            missing_eligibility.append(pid)

    # Compare text requirements
    requirements_comparison = {}
    if has_eligibility:
        req_lists = [
            policies[policy_ids.index(pid)].eligibility.requirements or []
            for pid in has_eligibility
        ]
        if req_lists:
            common_reqs = set(req_lists[0])
            for lst in req_lists[1:]:
                common_reqs.intersection_update(lst)

            unique_reqs = {}
            for pid, lst in zip(has_eligibility, req_lists):
                unique_reqs[pid] = list(set(lst) - common_reqs)

            requirements_comparison = {
                "common": list(common_reqs),
                "unique_by_policy": unique_reqs
            }

    return {
        "by_policy": eligibility_data,
        "has_eligibility": has_eligibility,
        "missing_eligibility": missing_eligibility,
        "requirements_comparison": requirements_comparison
    }


def _identify_missing_fields(policies: List[Policy], policy_ids: List[str]) -> Dict[str, List[str]]:
    """Identify which fields are missing for each policy."""
    missing_by_policy = {}

    for policy, pid in zip(policies, policy_ids):
        missing = []
        if not policy.deductible:
            missing.append("deductible")
        if not policy.eligibility:
            missing.append("eligibility")
        if not policy.exclusions:
            missing.append("exclusions")
        if missing:
            missing_by_policy[pid] = missing

    return missing_by_policy
