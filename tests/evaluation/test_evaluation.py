"""Tests for evaluation framework."""

import json
import pytest
from pathlib import Path

from tests.evaluation.evaluator import EvaluationRunner, EvaluationMetrics


class TestEvaluationMetrics:
    """Tests for EvaluationMetrics class."""

    def test_metrics_initialization(self):
        """Test that metrics initialize with correct defaults."""
        metrics = EvaluationMetrics()
        assert metrics.precision_at_k == {}
        assert metrics.recall_at_k == {}
        assert metrics.mrr == 0.0
        assert metrics.answer_correctness == 0.0
        assert metrics.groundedness_score == 0.0
        assert metrics.total_queries == 0
        assert metrics.successful_queries == 0
        assert metrics.failed_queries == 0

    def test_metrics_to_dict(self):
        """Test converting metrics to dictionary."""
        metrics = EvaluationMetrics()
        metrics.total_queries = 10
        metrics.successful_queries = 8
        metrics.failed_queries = 2
        metrics.mrr = 0.75

        metrics_dict = metrics.to_dict()
        assert metrics_dict["total_queries"] == 10
        assert metrics_dict["successful_queries"] == 8
        assert metrics_dict["failed_queries"] == 2
        assert metrics_dict["mrr"] == 0.75
        assert metrics_dict["success_rate"] == 0.8


class TestEvaluationRunner:
    """Tests for EvaluationRunner class."""

    def test_dataset_loading(self):
        """Test loading evaluation dataset."""
        runner = EvaluationRunner("data/evaluation_dataset.json")
        assert runner.dataset is not None
        assert "questions" in runner.dataset
        assert "metadata" in runner.dataset
        assert len(runner.dataset["questions"]) > 0

    def test_dataset_structure(self):
        """Test that dataset has required fields."""
        runner = EvaluationRunner("data/evaluation_dataset.json")
        questions = runner.dataset["questions"]

        for question in questions:
            assert "query_id" in question
            assert "query" in question
            assert "expected_policies" in question
            assert "expected_outcome" in question
            assert "category" in question
            assert "difficulty" in question

    def test_calculate_precision_at_k(self):
        """Test Precision@K calculation."""
        runner = EvaluationRunner("data/evaluation_dataset.json")

        # Test case 1: Perfect precision
        result = runner.calculate_precision_at_k(
            retrieved=["TCI-DOM-001", "TCI-DOM-002", "TCI-DOM-003"],
            relevant=["TCI-DOM-001", "TCI-DOM-002"],
            k=5
        )
        assert result == 1.0

        # Test case 2: Partial precision
        result = runner.calculate_precision_at_k(
            retrieved=["TCI-DOM-001", "TCI-EXP-001", "TCI-SB-001"],
            relevant=["TCI-DOM-001", "TCI-DOM-002"],
            k=5
        )
        assert result == 0.2  # 1 out of 5

        # Test case 3: Empty retrieved
        result = runner.calculate_precision_at_k(
            retrieved=[],
            relevant=["TCI-DOM-001"],
            k=5
        )
        assert result == 0.0

    def test_calculate_recall_at_k(self):
        """Test Recall@K calculation."""
        runner = EvaluationRunner("data/evaluation_dataset.json")

        # Test case 1: Perfect recall
        result = runner.calculate_recall_at_k(
            retrieved=["TCI-DOM-001", "TCI-DOM-002"],
            relevant=["TCI-DOM-001", "TCI-DOM-002"],
            k=5
        )
        assert result == 1.0

        # Test case 2: Partial recall
        result = runner.calculate_recall_at_k(
            retrieved=["TCI-DOM-001"],
            relevant=["TCI-DOM-001", "TCI-DOM-002", "TCI-DOM-003"],
            k=5
        )
        assert result == 1.0 / 3.0

        # Test case 3: Empty relevant
        result = runner.calculate_recall_at_k(
            retrieved=["TCI-DOM-001"],
            relevant=[],
            k=5
        )
        assert result == 0.0

    def test_calculate_mrr(self):
        """Test MRR calculation."""
        runner = EvaluationRunner("data/evaluation_dataset.json")

        # Test case 1: First result is relevant
        result = runner.calculate_mrr(
            retrieved=["TCI-DOM-001", "TCI-DOM-002", "TCI-DOM-003"],
            relevant=["TCI-DOM-001"]
        )
        assert result == 1.0

        # Test case 2: Second result is relevant
        result = runner.calculate_mrr(
            retrieved=["TCI-EXP-001", "TCI-DOM-001", "TCI-DOM-002"],
            relevant=["TCI-DOM-001"]
        )
        assert result == 0.5

        # Test case 3: No relevant results
        result = runner.calculate_mrr(
            retrieved=["TCI-EXP-001", "TCI-EXP-002"],
            relevant=["TCI-DOM-001"]
        )
        assert result == 0.0

    def test_dataset_category_counts(self):
        """Test that dataset has correct category distribution."""
        runner = EvaluationRunner("data/evaluation_dataset.json")
        metadata = runner.dataset["metadata"]

        assert metadata["total_questions"] == 30
        assert metadata["by_category"]["search"] == 10
        assert metadata["by_category"]["compare"] == 5
        assert metadata["by_category"]["eligibility"] == 8
        assert metadata["by_category"]["ambiguous"] == 3
        assert metadata["by_category"]["unsupported"] == 4

    def test_dataset_difficulty_counts(self):
        """Test that dataset has correct difficulty distribution."""
        runner = EvaluationRunner("data/evaluation_dataset.json")
        metadata = runner.dataset["metadata"]

        assert metadata["by_difficulty"]["easy"] == 8
        assert metadata["by_difficulty"]["medium"] == 16
        assert metadata["by_difficulty"]["hard"] == 6


class TestEvaluationIntegration:
    """Integration tests for evaluation framework."""

    def test_search_evaluation_runs(self):
        """Test that search evaluation can execute without errors."""
        runner = EvaluationRunner("data/evaluation_dataset.json")
        results = runner.run_search_evaluation()

        assert results["category"] == "search"
        assert results["total_queries"] > 0
        assert "results" in results
        assert "average_metrics" in results

    def test_comparison_evaluation_runs(self):
        """Test that comparison evaluation can execute without errors."""
        runner = EvaluationRunner("data/evaluation_dataset.json")
        results = runner.run_comparison_evaluation()

        assert results["category"] == "compare"
        assert results["total_queries"] > 0
        assert "results" in results

    def test_eligibility_evaluation_runs(self):
        """Test that eligibility evaluation can execute without errors."""
        runner = EvaluationRunner("data/evaluation_dataset.json")
        results = runner.run_eligibility_evaluation()

        assert results["category"] == "eligibility"
        assert results["total_queries"] > 0
        assert "results" in results
        assert "correctness_rate" in results

    def test_save_results(self, tmp_path):
        """Test saving evaluation results to file."""
        runner = EvaluationRunner("data/evaluation_dataset.json")
        test_results = {
            "test": "data",
            "metrics": {"precision": 0.8}
        }

        output_file = tmp_path / "test_results.json"
        runner.save_results(test_results, str(output_file))

        assert output_file.exists()
        with open(output_file, 'r') as f:
            saved_data = json.load(f)
        assert saved_data["test"] == "data"
