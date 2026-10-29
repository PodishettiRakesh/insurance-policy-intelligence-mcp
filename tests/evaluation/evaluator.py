"""Evaluation framework for insurance policy intelligence system."""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path

from app.search import search_policies
from app.comparison import compare_policies
from app.eligibility import check_eligibility

# Lazy import for agent to avoid dependency issues
InsurancePolicyAgent = None


class EvaluationMetrics:
    """Container for evaluation metrics."""

    def __init__(self):
        self.precision_at_k = {}
        self.recall_at_k = {}
        self.mrr = 0.0
        self.answer_correctness = 0.0
        self.groundedness_score = 0.0
        self.total_queries = 0
        self.successful_queries = 0
        self.failed_queries = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "precision_at_k": self.precision_at_k,
            "recall_at_k": self.recall_at_k,
            "mrr": self.mrr,
            "answer_correctness": self.answer_correctness,
            "groundedness_score": self.groundedness_score,
            "total_queries": self.total_queries,
            "successful_queries": self.successful_queries,
            "failed_queries": self.failed_queries,
            "success_rate": self.successful_queries / self.total_queries if self.total_queries > 0 else 0.0
        }


class EvaluationRunner:
    """
    Runner for evaluating the insurance policy intelligence system.

    Executes evaluation queries, calculates metrics, and generates reports.
    """

    def __init__(self, dataset_path: str = "data/evaluation_dataset.json"):
        """
        Initialize the evaluation runner.

        Args:
            dataset_path: Path to the evaluation dataset JSON file
        """
        self.dataset_path = Path(dataset_path)
        self.dataset = self._load_dataset()
        self.metrics = EvaluationMetrics()

    def _load_dataset(self) -> Dict[str, Any]:
        """Load the evaluation dataset from JSON file."""
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Evaluation dataset not found: {self.dataset_path}")

        with open(self.dataset_path, 'r') as f:
            data = json.load(f)

        return data

    def calculate_precision_at_k(
        self,
        retrieved: List[str],
        relevant: List[str],
        k: int
    ) -> float:
        """
        Calculate Precision@K metric.

        Args:
            retrieved: List of retrieved policy IDs
            relevant: List of relevant policy IDs (ground truth)
            k: The K value for precision calculation

        Returns:
            Precision@K score (0.0 to 1.0)
        """
        if not retrieved or k <= 0:
            return 0.0

        retrieved_at_k = retrieved[:k]
        relevant_set = set(relevant)

        if not relevant_set:
            return 0.0

        relevant_retrieved = len([pid for pid in retrieved_at_k if pid in relevant_set])
        return relevant_retrieved / len(retrieved_at_k)

    def calculate_recall_at_k(
        self,
        retrieved: List[str],
        relevant: List[str],
        k: int
    ) -> float:
        """
        Calculate Recall@K metric.

        Args:
            retrieved: List of retrieved policy IDs
            relevant: List of relevant policy IDs (ground truth)
            k: The K value for recall calculation

        Returns:
            Recall@K score (0.0 to 1.0)
        """
        if not relevant:
            return 0.0

        retrieved_at_k = retrieved[:k]
        relevant_set = set(relevant)

        relevant_retrieved = len([pid for pid in retrieved_at_k if pid in relevant_set])
        return relevant_retrieved / len(relevant)

    def calculate_mrr(
        self,
        retrieved: List[str],
        relevant: List[str]
    ) -> float:
        """
        Calculate Mean Reciprocal Rank (MRR).

        Args:
            retrieved: List of retrieved policy IDs
            relevant: List of relevant policy IDs (ground truth)

        Returns:
            MRR score (0.0 to 1.0)
        """
        if not retrieved or not relevant:
            return 0.0

        relevant_set = set(relevant)

        for i, pid in enumerate(retrieved):
            if pid in relevant_set:
                return 1.0 / (i + 1)

        return 0.0

    def run_search_evaluation(self, k_values: List[int] = [5, 10]) -> Dict[str, Any]:
        """
        Run evaluation on search queries using the agent.

        Args:
            k_values: List of K values for Precision@K and Recall@K

        Returns:
            Dictionary with search evaluation results
        """
        # Lazy import for agent
        global InsurancePolicyAgent
        if InsurancePolicyAgent is None:
            try:
                from app.agent import InsurancePolicyAgent
            except ImportError:
                # Fallback to direct search if agent unavailable
                return self._run_search_evaluation_direct(k_values)

        agent = InsurancePolicyAgent()
        search_queries = [q for q in self.dataset["questions"] if q["category"] == "search"]
        results = []

        total_precision = {k: 0.0 for k in k_values}
        total_recall = {k: 0.0 for k in k_values}
        total_mrr = 0.0
        successful = 0

        for query in search_queries:
            try:
                # Execute agent for search
                agent_result = agent.run(query["query"])
                tool_results = agent_result["tool_results"]

                # Extract search results from tool results
                retrieved_ids = []
                for tr in tool_results:
                    if tr["tool"] == "search_policies" and tr["result"].get("success"):
                        retrieved_ids = [p["policy_id"] for p in tr["result"]["results"]]
                        break

                relevant_ids = query["expected_policies"]

                # Calculate metrics
                query_metrics = {
                    "query_id": query["query_id"],
                    "query": query["query"],
                    "retrieved": retrieved_ids,
                    "relevant": relevant_ids,
                    "count": len(retrieved_ids)
                }

                for k in k_values:
                    p_at_k = self.calculate_precision_at_k(retrieved_ids, relevant_ids, k)
                    r_at_k = self.calculate_recall_at_k(retrieved_ids, relevant_ids, k)
                    query_metrics[f"precision_at_{k}"] = p_at_k
                    query_metrics[f"recall_at_{k}"] = r_at_k
                    total_precision[k] += p_at_k
                    total_recall[k] += r_at_k

                mrr = self.calculate_mrr(retrieved_ids, relevant_ids)
                query_metrics["mrr"] = mrr
                total_mrr += mrr

                results.append(query_metrics)
                successful += 1

            except Exception as e:
                results.append({
                    "query_id": query["query_id"],
                    "query": query["query"],
                    "error": str(e)
                })

        # Calculate averages
        if successful > 0:
            for k in k_values:
                self.metrics.precision_at_k[k] = total_precision[k] / successful
                self.metrics.recall_at_k[k] = total_recall[k] / successful
            self.metrics.mrr = total_mrr / successful

        return {
            "category": "search",
            "total_queries": len(search_queries),
            "successful": successful,
            "failed": len(search_queries) - successful,
            "results": results,
            "average_metrics": {
                "precision_at_k": self.metrics.precision_at_k,
                "recall_at_k": self.metrics.recall_at_k,
                "mrr": self.metrics.mrr
            }
        }

    def _run_search_evaluation_direct(self, k_values: List[int] = [5, 10]) -> Dict[str, Any]:
        """
        Fallback: Run search evaluation with direct search_policies calls.
        Uses simplified keyword-based queries.
        """
        search_queries = [q for q in self.dataset["questions"] if q["category"] == "search"]
        results = []

        total_precision = {k: 0.0 for k in k_values}
        total_recall = {k: 0.0 for k in k_values}
        total_mrr = 0.0
        successful = 0

        for query in search_queries:
            try:
                # Extract simple keywords from query
                simple_query = self._extract_search_keywords(query["query"])

                # Execute search
                policies = search_policies(
                    query=simple_query,
                    limit=10
                )
                retrieved_ids = [p.policy_id for p in policies]
                relevant_ids = query["expected_policies"]

                # Calculate metrics
                query_metrics = {
                    "query_id": query["query_id"],
                    "query": query["query"],
                    "simple_query": simple_query,
                    "retrieved": retrieved_ids,
                    "relevant": relevant_ids,
                    "count": len(retrieved_ids)
                }

                for k in k_values:
                    p_at_k = self.calculate_precision_at_k(retrieved_ids, relevant_ids, k)
                    r_at_k = self.calculate_recall_at_k(retrieved_ids, relevant_ids, k)
                    query_metrics[f"precision_at_{k}"] = p_at_k
                    query_metrics[f"recall_at_{k}"] = r_at_k
                    total_precision[k] += p_at_k
                    total_recall[k] += r_at_k

                mrr = self.calculate_mrr(retrieved_ids, relevant_ids)
                query_metrics["mrr"] = mrr
                total_mrr += mrr

                results.append(query_metrics)
                successful += 1

            except Exception as e:
                results.append({
                    "query_id": query["query_id"],
                    "query": query["query"],
                    "error": str(e)
                })

        # Calculate averages
        if successful > 0:
            for k in k_values:
                self.metrics.precision_at_k[k] = total_precision[k] / successful
                self.metrics.recall_at_k[k] = total_recall[k] / successful
            self.metrics.mrr = total_mrr / successful

        return {
            "category": "search",
            "total_queries": len(search_queries),
            "successful": successful,
            "failed": len(search_queries) - successful,
            "results": results,
            "average_metrics": {
                "precision_at_k": self.metrics.precision_at_k,
                "recall_at_k": self.metrics.recall_at_k,
                "mrr": self.metrics.mrr
            },
            "note": "Used direct search with keyword extraction (agent unavailable)"
        }

    def _extract_search_keywords(self, query: str) -> str:
        """Extract simple keywords from natural language query."""
        query_lower = query.lower()

        # Extract key terms
        keywords = []

        if "domestic" in query_lower:
            keywords.append("domestic")
        if "export" in query_lower:
            keywords.append("export")
        if "single buyer" in query_lower:
            keywords.append("single buyer")
        if "whole turnover" in query_lower:
            keywords.append("whole turnover")
        if "sme" in query_lower:
            keywords.append("sme")
        if "trade credit" in query_lower:
            keywords.append("trade credit")
        if "bad debt" in query_lower:
            keywords.append("bad debt")
        if "insolvency" in query_lower:
            keywords.append("insolvency")
        if "buyer" in query_lower:
            keywords.append("buyer")

        return " ".join(keywords) if keywords else "credit"

    def run_comparison_evaluation(self) -> Dict[str, Any]:
        """
        Run evaluation on comparison queries.

        Returns:
            Dictionary with comparison evaluation results
        """
        compare_queries = [q for q in self.dataset["questions"] if q["category"] == "compare"]
        results = []
        successful = 0

        for query in compare_queries:
            try:
                # Execute comparison
                comparison = compare_policies(policy_ids=query["expected_policies"])
                relevant_ids = query["expected_policies"]
                compared_ids = [p.policy_id for p in comparison.policies]

                # Check if all expected policies were compared
                all_compared = set(relevant_ids) == set(compared_ids)

                results.append({
                    "query_id": query["query_id"],
                    "query": query["query"],
                    "expected": relevant_ids,
                    "compared": compared_ids,
                    "success": comparison.success,
                    "all_expected_compared": all_compared
                })

                if comparison.success and all_compared:
                    successful += 1

            except Exception as e:
                results.append({
                    "query_id": query["query_id"],
                    "query": query["query"],
                    "error": str(e)
                })

        return {
            "category": "compare",
            "total_queries": len(compare_queries),
            "successful": successful,
            "failed": len(compare_queries) - successful,
            "results": results
        }

    def run_eligibility_evaluation(self) -> Dict[str, Any]:
        """
        Run evaluation on eligibility queries.

        Returns:
            Dictionary with eligibility evaluation results
        """
        eligibility_queries = [q for q in self.dataset["questions"] if q["category"] == "eligibility"]
        results = []
        successful = 0
        correct_status = 0

        for query in eligibility_queries:
            try:
                # Execute eligibility check
                eligibility = check_eligibility(
                    policy_id=query["expected_policies"][0],
                    applicant_info=query.get("applicant_info", {})
                )

                expected_status = query.get("expected_status", "")
                actual_status = eligibility.overall_status

                # Check if status matches expected
                status_match = expected_status == actual_status

                results.append({
                    "query_id": query["query_id"],
                    "query": query["query"],
                    "policy_id": query["expected_policies"][0],
                    "expected_status": expected_status,
                    "actual_status": actual_status,
                    "status_match": status_match,
                    "success": eligibility.success
                })

                if eligibility.success:
                    successful += 1
                    if status_match:
                        correct_status += 1

            except Exception as e:
                results.append({
                    "query_id": query["query_id"],
                    "query": query["query"],
                    "error": str(e)
                })

        # Calculate correctness rate
        correctness_rate = correct_status / successful if successful > 0 else 0.0

        return {
            "category": "eligibility",
            "total_queries": len(eligibility_queries),
            "successful": successful,
            "failed": len(eligibility_queries) - successful,
            "correct_status": correct_status,
            "correctness_rate": correctness_rate,
            "results": results
        }

    def run_agent_evaluation(self) -> Dict[str, Any]:
        """
        Run evaluation on full agent workflow.

        Returns:
            Dictionary with agent evaluation results
        """
        # Lazy import to avoid dependency issues
        global InsurancePolicyAgent
        if InsurancePolicyAgent is None:
            try:
                from app.agent import InsurancePolicyAgent
            except ImportError:
                # Agent evaluation not available, return empty results
                return {
                    "category": "agent",
                    "total_queries": 0,
                    "successful": 0,
                    "failed": 0,
                    "grounded_count": 0,
                    "groundedness_score": 0.0,
                    "results": [],
                    "note": "Agent evaluation skipped due to missing dependencies"
                }

        agent = InsurancePolicyAgent()
        results = []
        successful = 0
        grounded_count = 0

        for query in self.dataset["questions"]:
            # Skip unsupported queries for agent workflow
            if query["category"] == "unsupported":
                continue

            try:
                # Execute agent
                agent_result = agent.run(query["query"])
                answer = agent_result["answer"]

                # Check if answer contains policy ID citations
                has_citations = any(f"[{pid}]" in answer for pid in query["expected_policies"])
                if has_citations:
                    grounded_count += 1

                # For search queries, check if relevant policies are mentioned
                if query["category"] == "search":
                    all_mentioned = all(f"[{pid}]" in answer for pid in query["expected_policies"])
                else:
                    all_mentioned = True  # For non-search, just check if it ran successfully

                results.append({
                    "query_id": query["query_id"],
                    "query": query["query"],
                    "category": query["category"],
                    "answer": answer,
                    "has_citations": has_citations,
                    "all_policies_mentioned": all_mentioned if query["category"] == "search" else None
                })

                if all_mentioned:
                    successful += 1

            except Exception as e:
                results.append({
                    "query_id": query["query_id"],
                    "query": query["query"],
                    "error": str(e)
                })

        # Calculate groundedness
        total_agent_queries = len([r for r in results if "error" not in r])
        groundedness = grounded_count / total_agent_queries if total_agent_queries > 0 else 0.0

        return {
            "category": "agent",
            "total_queries": len(self.dataset["questions"]) - len([q for q in self.dataset["questions"] if q["category"] == "unsupported"]),
            "successful": successful,
            "failed": len(results) - successful,
            "grounded_count": grounded_count,
            "groundedness_score": groundedness,
            "results": results
        }

    def run_full_evaluation(self) -> Dict[str, Any]:
        """
        Run complete evaluation across all categories.

        Returns:
            Dictionary with all evaluation results
        """
        print("Running full evaluation...")

        # Update metrics
        self.metrics.total_queries = len(self.dataset["questions"])

        # Run search evaluation
        print("\n1. Running search evaluation...")
        search_results = self.run_search_evaluation()
        self.metrics.successful_queries += search_results["successful"]
        self.metrics.failed_queries += search_results["failed"]

        # Run comparison evaluation
        print("\n2. Running comparison evaluation...")
        comparison_results = self.run_comparison_evaluation()
        self.metrics.successful_queries += comparison_results["successful"]
        self.metrics.failed_queries += comparison_results["failed"]

        # Run eligibility evaluation
        print("\n3. Running eligibility evaluation...")
        eligibility_results = self.run_eligibility_evaluation()
        self.metrics.successful_queries += eligibility_results["successful"]
        self.metrics.failed_queries += eligibility_results["failed"]
        self.metrics.answer_correctness = eligibility_results["correctness_rate"]

        # Run agent evaluation
        print("\n4. Running agent evaluation...")
        agent_results = self.run_agent_evaluation()
        self.metrics.groundedness_score = agent_results["groundedness_score"]

        # Compile final results
        final_results = {
            "dataset_metadata": self.dataset["metadata"],
            "search_evaluation": search_results,
            "comparison_evaluation": comparison_results,
            "eligibility_evaluation": eligibility_results,
            "agent_evaluation": agent_results,
            "overall_metrics": self.metrics.to_dict()
        }

        print("\n[X] Evaluation complete!")
        return final_results

    def save_results(self, results: Dict[str, Any], output_path: str = "evaluation/baseline_results.json"):
        """
        Save evaluation results to JSON file.

        Args:
            results: Evaluation results dictionary
            output_path: Path to save results
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\nResults saved to: {output_file}")
