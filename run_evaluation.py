"""Run evaluation and save timestamped results."""

from datetime import datetime
from tests.evaluation.evaluator import EvaluationRunner

def main():
    """Run the evaluation."""
    print("=" * 60)
    print("Insurance Policy Intelligence - Evaluation")
    print("=" * 60)

    # Initialize evaluation runner
    runner = EvaluationRunner("data/evaluation_dataset.json")

    # Run full evaluation
    results = runner.run_full_evaluation()

    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_path = f"evaluation/results_{timestamp}.json"

    # Save results with timestamp
    runner.save_results(results, output_path)

    # Print summary
    print("\n" + "=" * 60)
    print("BASELINE EVALUATION SUMMARY")
    print("=" * 60)

    print(f"\nDataset: {results['dataset_metadata']['total_questions']} questions")
    print(f"  - Search: {results['dataset_metadata']['by_category']['search']}")
    print(f"  - Compare: {results['dataset_metadata']['by_category']['compare']}")
    print(f"  - Eligibility: {results['dataset_metadata']['by_category']['eligibility']}")
    print(f"  - Ambiguous: {results['dataset_metadata']['by_category']['ambiguous']}")
    print(f"  - Unsupported: {results['dataset_metadata']['by_category']['unsupported']}")

    print(f"\nSearch Metrics:")
    search_metrics = results['search_evaluation']['average_metrics']
    print(f"  - Precision@5: {search_metrics['precision_at_k'].get(5, 0):.3f}")
    print(f"  - Precision@10: {search_metrics['precision_at_k'].get(10, 0):.3f}")
    print(f"  - Recall@5: {search_metrics['recall_at_k'].get(5, 0):.3f}")
    print(f"  - Recall@10: {search_metrics['recall_at_k'].get(10, 0):.3f}")
    print(f"  - MRR: {search_metrics['mrr']:.3f}")
    print(f"  - Success Rate: {results['search_evaluation']['successful']}/{results['search_evaluation']['total_queries']}")

    print(f"\nComparison Metrics:")
    print(f"  - Success Rate: {results['comparison_evaluation']['successful']}/{results['comparison_evaluation']['total_queries']}")

    print(f"\nEligibility Metrics:")
    print(f"  - Success Rate: {results['eligibility_evaluation']['successful']}/{results['eligibility_evaluation']['total_queries']}")
    print(f"  - Correctness Rate: {results['eligibility_evaluation']['correctness_rate']:.3f}")

    print(f"\nAgent Metrics:")
    print(f"  - Success Rate: {results['agent_evaluation']['successful']}/{results['agent_evaluation']['total_queries']}")
    print(f"  - Groundedness Score: {results['agent_evaluation']['groundedness_score']:.3f}")

    print(f"\nOverall Metrics:")
    overall = results['overall_metrics']
    print(f"  - Total Queries: {overall['total_queries']}")
    print(f"  - Successful: {overall['successful_queries']}")
    print(f"  - Failed: {overall['failed_queries']}")
    print(f"  - Success Rate: {overall['success_rate']:.3f}")

    print("\n" + "=" * 60)
    print("[X] Baseline evaluation complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
