"""Evidence tracking and source reference management."""

from typing import Any, Dict, List
from app.models import (
    SourceReference,
    Evidence,
    EvidenceMetadata,
    Policy,
)


class EvidenceTracker:
    """Track evidence and source references for factual claims."""

    def __init__(self):
        """Initialize the evidence tracker."""
        self.evidence_list: List[Evidence] = []

    def create_source_reference(
        self,
        policy_id: str,
        field: str,
        value: Any,
        display_value: str = None
    ) -> SourceReference:
        """
        Create a source reference for a policy field.

        Args:
            policy_id: Policy ID
            field: Field name
            value: Actual value from source
            display_value: Human-readable display value

        Returns:
            SourceReference object
        """
        if display_value is None:
            display_value = str(value)

        return SourceReference(
            policy_id=policy_id,
            field=field,
            value=value,
            display_value=display_value
        )

    def extract_policy_sources(self, policy: Policy) -> List[SourceReference]:
        """
        Extract source references from a policy object.

        Args:
            policy: Policy object

        Returns:
            List of SourceReference objects for key fields
        """
        sources = []

        # Premium reference
        sources.append(self.create_source_reference(
            policy_id=policy.policy_id,
            field="premium",
            value=policy.premium.model_dump(),
            display_value=f"{policy.premium.amount} {policy.premium.currency} ({policy.premium.period})"
        ))

        # Deductible reference (if present)
        if policy.deductible:
            sources.append(self.create_source_reference(
                policy_id=policy.policy_id,
                field="deductible",
                value=policy.deductible.model_dump(),
                display_value=f"{policy.deductible.amount} {policy.deductible.currency}"
            ))

        # Coverage reference
        sources.append(self.create_source_reference(
            policy_id=policy.policy_id,
            field="coverage",
            value=policy.coverage,
            display_value=f"{len(policy.coverage)} coverage items"
        ))

        # Exclusions reference (if present)
        if policy.exclusions:
            sources.append(self.create_source_reference(
                policy_id=policy.policy_id,
                field="exclusions",
                value=policy.exclusions,
                display_value=f"{len(policy.exclusions)} exclusion items"
            ))

        # Category reference
        sources.append(self.create_source_reference(
            policy_id=policy.policy_id,
            field="category",
            value=policy.category,
            display_value=policy.category
        ))

        # Provider reference
        sources.append(self.create_source_reference(
            policy_id=policy.policy_id,
            field="provider",
            value=policy.provider,
            display_value=policy.provider
        ))

        return sources

    def add_evidence(
        self,
        claim: str,
        sources: List[SourceReference],
        is_supported: bool = True,
        confidence: float = 1.0
    ) -> Evidence:
        """
        Add evidence for a factual claim.

        Args:
            claim: The factual claim
            sources: Source references supporting the claim
            is_supported: Whether the claim is supported
            confidence: Confidence in the evidence (0.0 to 1.0)

        Returns:
            Evidence object
        """
        evidence = Evidence(
            claim=claim,
            sources=sources,
            is_supported=is_supported,
            confidence=confidence
        )
        self.evidence_list.append(evidence)
        return evidence

    def verify_claim_against_sources(
        self,
        claim: str,
        policy_id: str,
        field: str,
        expected_value: Any,
        actual_value: Any
    ) -> Evidence:
        """
        Verify a claim against actual policy data.

        Args:
            claim: The claim to verify
            policy_id: Policy ID
            field: Field name
            expected_value: Expected value in the claim
            actual_value: Actual value from policy data

        Returns:
            Evidence object with verification result
        """
        source = self.create_source_reference(
            policy_id=policy_id,
            field=field,
            value=actual_value
        )

        is_supported = expected_value == actual_value
        confidence = 1.0 if is_supported else 0.0

        return self.add_evidence(
            claim=claim,
            sources=[source],
            is_supported=is_supported,
            confidence=confidence
        )

    def create_evidence_metadata(self, sources: List[SourceReference]) -> EvidenceMetadata:
        """
        Create evidence metadata from source references.

        Args:
            sources: List of source references

        Returns:
            EvidenceMetadata object
        """
        return EvidenceMetadata(
            has_evidence=len(sources) > 0,
            sources=sources
        )

    def format_citation(self, source: SourceReference) -> str:
        """
        Format a source reference as a citation string.

        Args:
            source: SourceReference object

        Returns:
            Formatted citation string (e.g., "[TCI-DOM-001:premium]")
        """
        return f"[{source.policy_id}:{source.field}]"

    def format_citations(self, sources: List[SourceReference]) -> str:
        """
        Format multiple source references as citation strings.

        Args:
            sources: List of SourceReference objects

        Returns:
            Formatted citation string (e.g., "[TCI-DOM-001:premium, TCI-DOM-002:premium]")
        """
        if not sources:
            return ""

        citations = [self.format_citation(s) for s in sources]
        return ", ".join(citations)
