"""Policy comparison service."""

from typing import Dict, List, Set
from pydantic import ValidationError

from app.catalogue import get_catalogue
from app.models import (
    ComparePoliciesRequest,
    ComparisonResult,
    Policy,
    PolicyComparisonItem,
    CoverageComparison,
    ExclusionComparison,
    PremiumComparison,
    DeductibleComparison,
    EligibilityComparison,
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
    coverage_comparison = _compare_coverage(
        [p.coverage for p in policies],
        request.policy_ids
    )

    # Compare exclusions
    exclusions_comparison = _compare_exclusions(
        [p.exclusions for p in policies],
        request.policy_ids
    )

    # Compare premiums
    premium_comparison = _compare_premiums(policies, request.policy_ids)

    # Compare deductibles
    deductible_comparison = _compare_deductibles(policies, request.policy_ids)

    # Compare eligibility
    eligibility_comparison = _compare_eligibility(policies, request.policy_ids)

    # Identify missing fields
    missing_fields = _identify_missing_fields(policies, request.policy_ids)

    # Generate summary
    summary = _generate_comparison_summary(
        policies,
        request.policy_ids,
        coverage_comparison,
        premium_comparison,
        deductible_comparison
    )

    return ComparisonResult(
        success=True,
        policies=comparison_items,
        coverage_comparison=coverage_comparison.model_dump(),
        exclusions_comparison=exclusions_comparison.model_dump(),
        premium_comparison=premium_comparison.model_dump(),
        deductible_comparison=deductible_comparison.model_dump(),
        eligibility_comparison=eligibility_comparison.model_dump(),
        missing_fields=missing_fields,
        summary=summary
    )


def _normalize_text(text: str) -> str:
    """Normalize text for comparison (lowercase, strip, remove extra spaces)."""
    return " ".join(text.lower().strip().split())


def _fuzzy_match(item1: str, item2: str, threshold: float = 0.8) -> bool:
    """
    Check if two strings are similar using simple fuzzy matching.

    Args:
        item1: First string
        item2: Second string
        threshold: Similarity threshold (0.0 to 1.0)

    Returns:
        True if strings are similar enough
    """
    # Normalize both
    norm1 = _normalize_text(item1)
    norm2 = _normalize_text(item2)

    # Exact match
    if norm1 == norm2:
        return True

    # Check if one is substring of the other
    if norm1 in norm2 or norm2 in norm1:
        return True

    # Simple word overlap
    words1 = set(norm1.split())
    words2 = set(norm2.split())

    if not words1 or not words2:
        return False

    intersection = words1.intersection(words2)
    union = words1.union(words2)

    similarity = len(intersection) / len(union) if union else 0
    return similarity >= threshold


def _compare_coverage(
    coverage_lists: List[List[str]],
    policy_ids: List[str]
) -> CoverageComparison:
    """Compare coverage items across policies with fuzzy matching."""
    if not coverage_lists:
        return CoverageComparison()

    # Normalize all coverage items
    normalized_lists = [[_normalize_text(item) for item in lst] for lst in coverage_lists]

    # Find common items (exact match)
    common_exact = set(normalized_lists[0])
    for lst in normalized_lists[1:]:
        common_exact.intersection_update(lst)

    # Find fuzzy common items
    common_fuzzy = set(common_exact)
    for i, lst in enumerate(normalized_lists):
        for item in lst:
            if item not in common_exact:
                # Check if fuzzy matches any item in common_exact
                for common_item in common_exact:
                    if _fuzzy_match(item, common_item):
                        common_fuzzy.add(f"{item} (similar to {common_item})")
                        break

    # Combine exact and fuzzy common items
    all_common = list(common_exact) + list(common_fuzzy)

    # Find unique items per policy
    unique_by_policy = {}
    for i, (lst, pid) in enumerate(zip(coverage_lists, policy_ids)):
        norm_lst = [_normalize_text(item) for item in lst]
        unique = set(norm_lst) - common_exact
        unique_by_policy[pid] = [coverage_lists[i][j] for j, item in enumerate(norm_lst) if item in unique]

    return CoverageComparison(
        common_items=all_common,
        unique_by_policy=unique_by_policy,
        coverage_counts={pid: len(lst) for pid, lst in zip(policy_ids, coverage_lists)}
    )


def _compare_exclusions(
    exclusion_lists: List[List[str]],
    policy_ids: List[str]
) -> ExclusionComparison:
    """Compare exclusion items across policies with fuzzy matching."""
    if not exclusion_lists:
        return ExclusionComparison()

    # Normalize all exclusion items
    normalized_lists = [[_normalize_text(item) for item in lst] for lst in exclusion_lists]

    # Find common items (exact match)
    common_exact = set(normalized_lists[0])
    for lst in normalized_lists[1:]:
        common_exact.intersection_update(lst)

    # Find fuzzy common items
    common_fuzzy = set(common_exact)
    for i, lst in enumerate(normalized_lists):
        for item in lst:
            if item not in common_exact:
                # Check if fuzzy matches any item in common_exact
                for common_item in common_exact:
                    if _fuzzy_match(item, common_item):
                        common_fuzzy.add(f"{item} (similar to {common_item})")
                        break

    # Combine exact and fuzzy common items
    all_common = list(common_exact) + list(common_fuzzy)

    # Find unique items per policy
    unique_by_policy = {}
    for i, (lst, pid) in enumerate(zip(exclusion_lists, policy_ids)):
        norm_lst = [_normalize_text(item) for item in lst]
        unique = set(norm_lst) - common_exact
        unique_by_policy[pid] = [exclusion_lists[i][j] for j, item in enumerate(norm_lst) if item in unique]

    return ExclusionComparison(
        common_items=all_common,
        unique_by_policy=unique_by_policy,
        exclusion_counts={pid: len(lst) for pid, lst in zip(policy_ids, exclusion_lists)}
    )


def _compare_premiums(policies: List[Policy], policy_ids: List[str]) -> PremiumComparison:
    """Compare premiums across policies with enhanced analysis."""
    amounts_by_policy = {}
    currencies = set()

    for policy, pid in zip(policies, policy_ids):
        amounts_by_policy[pid] = policy.premium.amount
        currencies.add(policy.premium.currency)

    # Calculate relative difference for 2 policies
    relative_difference = None
    if len(policies) == 2:
        amounts = list(amounts_by_policy.values())
        if amounts[0] > 0:
            relative_difference = abs(amounts[1] - amounts[0]) / amounts[0]

    # Currency mismatch warning
    currency_mismatch_warning = None
    if len(currencies) > 1:
        currency_mismatch_warning = f"Policies use different currencies: {', '.join(currencies)}. Exchange rate conversion not performed."

    return PremiumComparison(
        amounts_by_policy=amounts_by_policy,
        currencies=list(currencies),
        same_currency=len(currencies) == 1,
        currency_mismatch_warning=currency_mismatch_warning,
        relative_difference=relative_difference
    )


def _compare_deductibles(policies: List[Policy], policy_ids: List[str]) -> DeductibleComparison:
    """Compare deductibles across policies with structured output."""
    has_deductible = []
    missing_deductible = []
    amounts_by_policy = {}

    for policy, pid in zip(policies, policy_ids):
        if policy.deductible:
            has_deductible.append(pid)
            amounts_by_policy[pid] = policy.deductible.amount
        else:
            missing_deductible.append(pid)

    return DeductibleComparison(
        has_deductible=has_deductible,
        missing_deductible=missing_deductible,
        amounts_by_policy=amounts_by_policy
    )


def _compare_eligibility(policies: List[Policy], policy_ids: List[str]) -> EligibilityComparison:
    """Compare eligibility criteria across policies with structured output."""
    has_eligibility = []
    missing_eligibility = []
    requirements_by_policy = {}

    for policy, pid in zip(policies, policy_ids):
        if policy.eligibility:
            has_eligibility.append(pid)
            requirements_by_policy[pid] = policy.eligibility.requirements or []
        else:
            missing_eligibility.append(pid)

    # Compare text requirements
    common_requirements = []
    unique_requirements_by_policy = {}

    if has_eligibility:
        req_lists = [requirements_by_policy[pid] for pid in has_eligibility]
        if req_lists:
            common_reqs = set(req_lists[0])
            for lst in req_lists[1:]:
                common_reqs.intersection_update(lst)

            common_requirements = list(common_reqs)

            for pid, lst in zip(has_eligibility, req_lists):
                unique_requirements_by_policy[pid] = list(set(lst) - common_reqs)

    return EligibilityComparison(
        has_eligibility=has_eligibility,
        missing_eligibility=missing_eligibility,
        requirements_by_policy=requirements_by_policy,
        common_requirements=common_requirements,
        unique_requirements_by_policy=unique_requirements_by_policy
    )


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


def _generate_comparison_summary(
    policies: List[Policy],
    policy_ids: List[str],
    coverage_comparison: CoverageComparison,
    premium_comparison: PremiumComparison,
    deductible_comparison: DeductibleComparison
) -> str:
    """Generate a human-readable summary of the comparison."""
    summary_parts = []

    # Premium comparison
    if len(policies) == 2:
        pid1, pid2 = policy_ids[0], policy_ids[1]
        prem1 = premium_comparison.amounts_by_policy.get(pid1, 0)
        prem2 = premium_comparison.amounts_by_policy.get(pid2, 0)

        if prem1 > 0 and prem2 > 0:
            if prem1 < prem2:
                cheaper = pid1
                more_expensive = pid2
                diff_pct = ((prem2 - prem1) / prem1) * 100
            else:
                cheaper = pid2
                more_expensive = pid1
                diff_pct = ((prem1 - prem2) / prem2) * 100

            summary_parts.append(
                f"Premium: {cheaper} is {diff_pct:.1f}% cheaper than {more_expensive}."
            )

    # Coverage summary
    common_count = len(coverage_comparison.common_items)
    if common_count > 0:
        summary_parts.append(
            f"Coverage: {common_count} items common across all policies."
        )

    # Deductible summary
    if deductible_comparison.has_deductible:
        if len(deductible_comparison.has_deductible) == len(policies):
            summary_parts.append("All policies have deductible information.")
        else:
            missing = len(deductible_comparison.missing_deductible)
            summary_parts.append(f"{missing} policy(ies) missing deductible information.")

    return " ".join(summary_parts) if summary_parts else "Comparison complete."
