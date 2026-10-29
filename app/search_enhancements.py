"""Search enhancements: synonym support, relevance scoring, and ranking."""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from app.models import Policy


# Field weights for relevance scoring
FIELD_WEIGHTS = {
    "title": 3.0,      # Title matches are most important
    "description": 2.0,  # Description matches are important
    "coverage": 1.5,   # Coverage matches are moderately important
    "tags": 1.0,       # Tag matches are least important
}


class SynonymManager:
    """Manages insurance synonym dictionary for query expansion."""

    def __init__(self, synonyms_path: str = "data/synonyms.json"):
        """Load synonym dictionary from JSON file."""
        self.synonyms_path = Path(synonyms_path)
        self.synonym_map: Dict[str, List[str]] = {}
        self._load_synonyms()

    def _load_synonyms(self):
        """Load synonyms from JSON file."""
        if self.synonyms_path.exists():
            with open(self.synonyms_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.synonym_map = data.get("synonyms", {})
        else:
            # Fallback to empty dictionary if file doesn't exist
            self.synonym_map = {}

    def expand_synonyms(self, text: str) -> Set[str]:
        """
        Expand text with synonyms.

        Args:
            text: Input text to expand

        Returns:
            Set of normalized terms including original and synonyms
        """
        terms = normalize_text(text).split()
        expanded_terms = set(terms)

        for term in terms:
            # Check if term is a key in synonym map
            if term in self.synonym_map:
                expanded_terms.update(self.synonym_map[term])

            # Check if term matches any synonym value
            for key, synonyms in self.synonym_map.items():
                if term in synonyms:
                    expanded_terms.add(key)
                    expanded_terms.update(synonyms)

        return expanded_terms


def normalize_text(text: str) -> str:
    """
    Normalize text for search matching.

    Args:
        text: Input text

    Returns:
        Normalized text (lowercase, punctuation removed, extra spaces removed)
    """
    # Convert to lowercase
    text = text.lower()

    # Remove punctuation (keep alphanumeric and spaces)
    text = re.sub(r'[^\w\s]', ' ', text)

    # Remove extra spaces
    text = ' '.join(text.split())

    return text


def calculate_relevance_score(
    policy: Policy,
    query_terms: Set[str],
    synonym_manager: SynonymManager
) -> float:
    """
    Calculate relevance score for a policy based on query terms.

    Args:
        policy: Policy to score
        query_terms: Set of normalized query terms (including synonyms)
        synonym_manager: Synonym manager for expansion

    Returns:
        Relevance score (higher is more relevant)
    """
    score = 0.0

    # Normalize policy fields
    title_normalized = normalize_text(policy.title)
    description_normalized = normalize_text(policy.description)
    coverage_normalized = ' '.join([normalize_text(c) for c in policy.coverage])
    tags_normalized = ' '.join([normalize_text(t) for t in policy.tags])

    # Score title matches
    for term in query_terms:
        if term in title_normalized:
            score += FIELD_WEIGHTS["title"]

    # Score description matches
    for term in query_terms:
        if term in description_normalized:
            score += FIELD_WEIGHTS["description"]

    # Score coverage matches
    for term in query_terms:
        if term in coverage_normalized:
            score += FIELD_WEIGHTS["coverage"]

    # Score tag matches
    for term in query_terms:
        if term in tags_normalized:
            score += FIELD_WEIGHTS["tags"]

    return score


def rank_policies_by_relevance(
    policies: List[Policy],
    query: str,
    synonym_manager: SynonymManager
) -> List[Tuple[Policy, float]]:
    """
    Rank policies by relevance score.

    Args:
        policies: List of policies to rank
        query: Original search query
        synonym_manager: Synonym manager for expansion

    Returns:
        List of (policy, score) tuples sorted by descending score
    """
    # Expand query with synonyms
    query_terms = synonym_manager.expand_synonyms(query)

    # Calculate scores
    scored_policies = []
    for policy in policies:
        score = calculate_relevance_score(policy, query_terms, synonym_manager)
        scored_policies.append((policy, score))

    # Sort by score (descending)
    scored_policies.sort(key=lambda x: x[1], reverse=True)

    return scored_policies
