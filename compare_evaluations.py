"""Compare evaluation results between baseline and current run."""

import json
from pathlib import Path
from datetime import datetime


def load_results(filepath: str) -> dict:
    """Load evaluation results from JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def compare_metrics(baseline: dict, current: dict) -> dict:
    """Compare metrics between baseline and current results."""
    comparison = {
        "search": {},
        "comparison": {},
        "eligibility": {},
        "agent": {},
        "overall": {}
    }

    # Search metrics
    baseline_search_avg = baseline.get("search_evaluation", {}).get("average_metrics", {})
    current_search_avg = current.get("search_evaluation", {}).get("average_metrics", {})

    baseline_precision_5 = baseline_search_avg.get("precision_at_k", {}).get("5", 0)
    current_precision_5 = current_search_avg.get("precision_at_k", {}).get("5", 0)
    delta_p5 = current_precision_5 - baseline_precision_5
    delta_p5_pct = (delta_p5 / baseline_precision_5 * 100) if baseline_precision_5 > 0 else 0

    baseline_precision_10 = baseline_search_avg.get("precision_at_k", {}).get("10", 0)
    current_precision_10 = current_search_avg.get("precision_at_k", {}).get("10", 0)
    delta_p10 = current_precision_10 - baseline_precision_10
    delta_p10_pct = (delta_p10 / baseline_precision_10 * 100) if baseline_precision_10 > 0 else 0

    baseline_recall_5 = baseline_search_avg.get("recall_at_k", {}).get("5", 0)
    current_recall_5 = current_search_avg.get("recall_at_k", {}).get("5", 0)
    delta_r5 = current_recall_5 - baseline_recall_5
    delta_r5_pct = (delta_r5 / baseline_recall_5 * 100) if baseline_recall_5 > 0 else 0

    baseline_recall_10 = baseline_search_avg.get("recall_at_k", {}).get("10", 0)
    current_recall_10 = current_search_avg.get("recall_at_k", {}).get("10", 0)
    delta_r10 = current_recall_10 - baseline_recall_10
    delta_r10_pct = (delta_r10 / baseline_recall_10 * 100) if baseline_recall_10 > 0 else 0

    baseline_mrr = baseline_search_avg.get("mrr", 0)
    current_mrr = current_search_avg.get("mrr", 0)
    delta_mrr = current_mrr - baseline_mrr
    delta_mrr_pct = (delta_mrr / baseline_mrr * 100) if baseline_mrr > 0 else 0

    comparison["search"]["precision_at_5"] = {
        "baseline": baseline_precision_5,
        "current": current_precision_5,
        "delta": delta_p5,
        "delta_pct": delta_p5_pct
    }
    comparison["search"]["precision_at_10"] = {
        "baseline": baseline_precision_10,
        "current": current_precision_10,
        "delta": delta_p10,
        "delta_pct": delta_p10_pct
    }
    comparison["search"]["recall_at_5"] = {
        "baseline": baseline_recall_5,
        "current": current_recall_5,
        "delta": delta_r5,
        "delta_pct": delta_r5_pct
    }
    comparison["search"]["recall_at_10"] = {
        "baseline": baseline_recall_10,
        "current": current_recall_10,
        "delta": delta_r10,
        "delta_pct": delta_r10_pct
    }
    comparison["search"]["mrr"] = {
        "baseline": baseline_mrr,
        "current": current_mrr,
        "delta": delta_mrr,
        "delta_pct": delta_mrr_pct
    }

    # Comparison metrics
    baseline_comp_success = baseline.get("comparison_evaluation", {}).get("successful", 0)
    baseline_comp_total = baseline.get("comparison_evaluation", {}).get("total_queries", 1)
    baseline_comp_rate = baseline_comp_success / baseline_comp_total if baseline_comp_total > 0 else 0

    current_comp_success = current.get("comparison_evaluation", {}).get("successful", 0)
    current_comp_total = current.get("comparison_evaluation", {}).get("total_queries", 1)
    current_comp_rate = current_comp_success / current_comp_total if current_comp_total > 0 else 0

    comparison["comparison"]["success_rate"] = {
        "baseline": baseline_comp_rate,
        "current": current_comp_rate,
        "delta": current_comp_rate - baseline_comp_rate
    }

    # Eligibility metrics
    baseline_elig_success = baseline.get("eligibility_evaluation", {}).get("successful", 0)
    baseline_elig_total = baseline.get("eligibility_evaluation", {}).get("total_queries", 1)
    baseline_elig_rate = baseline_elig_success / baseline_elig_total if baseline_elig_total > 0 else 0

    current_elig_success = current.get("eligibility_evaluation", {}).get("successful", 0)
    current_elig_total = current.get("eligibility_evaluation", {}).get("total_queries", 1)
    current_elig_rate = current_elig_success / current_elig_total if current_elig_total > 0 else 0

    baseline_elig_correctness = baseline.get("eligibility_evaluation", {}).get("correctness_rate", 0)
    current_elig_correctness = current.get("eligibility_evaluation", {}).get("correctness_rate", 0)

    comparison["eligibility"]["success_rate"] = {
        "baseline": baseline_elig_rate,
        "current": current_elig_rate,
        "delta": current_elig_rate - baseline_elig_rate
    }
    comparison["eligibility"]["correctness_rate"] = {
        "baseline": baseline_elig_correctness,
        "current": current_elig_correctness,
        "delta": current_elig_correctness - baseline_elig_correctness
    }

    # Overall metrics
    baseline_overall_success = baseline.get("overall_metrics", {}).get("successful_queries", 0)
    baseline_overall_total = baseline.get("overall_metrics", {}).get("total_queries", 1)
    baseline_overall_rate = baseline_overall_success / baseline_overall_total if baseline_overall_total > 0 else 0

    current_overall_success = current.get("overall_metrics", {}).get("successful_queries", 0)
    current_overall_total = current.get("overall_metrics", {}).get("total_queries", 1)
    current_overall_rate = current_overall_success / current_overall_total if current_overall_total > 0 else 0

    comparison["overall"]["success_rate"] = {
        "baseline": baseline_overall_rate,
        "current": current_overall_rate,
        "delta": current_overall_rate - baseline_overall_rate
    }

    return comparison


def print_comparison_report(comparison: dict):
    """Print a human-readable comparison report."""
    print("=" * 80)
    print("EVALUATION COMPARISON REPORT")
    print("=" * 80)

    # Search metrics
    print("\nSEARCH METRICS")
    print("-" * 80)
    search_metrics = comparison["search"]
    for metric, data in search_metrics.items():
        delta_str = f"+{data['delta']:.3f}" if data['delta'] >= 0 else f"{data['delta']:.3f}"
        delta_pct_str = f"+{data['delta_pct']:.1f}%" if data['delta_pct'] >= 0 else f"{data['delta_pct']:.1f}%"
        print(f"{metric:20s}: {data['baseline']:.3f} -> {data['current']:.3f} ({delta_str}, {delta_pct_str})")

    # Comparison metrics
    print("\nCOMPARISON METRICS")
    print("-" * 80)
    comp_metrics = comparison["comparison"]
    for metric, data in comp_metrics.items():
        delta_str = f"+{data['delta']:.3f}" if data['delta'] >= 0 else f"{data['delta']:.3f}"
        print(f"{metric:20s}: {data['baseline']:.3f} -> {data['current']:.3f} ({delta_str})")

    # Eligibility metrics
    print("\nELIGIBILITY METRICS")
    print("-" * 80)
    elig_metrics = comparison["eligibility"]
    for metric, data in elig_metrics.items():
        delta_str = f"+{data['delta']:.3f}" if data['delta'] >= 0 else f"{data['delta']:.3f}"
        print(f"{metric:20s}: {data['baseline']:.3f} -> {data['current']:.3f} ({delta_str})")

    # Overall metrics
    print("\nOVERALL METRICS")
    print("-" * 80)
    overall_metrics = comparison["overall"]
    for metric, data in overall_metrics.items():
        delta_str = f"+{data['delta']:.3f}" if data['delta'] >= 0 else f"{data['delta']:.3f}"
        print(f"{metric:20s}: {data['baseline']:.3f} -> {data['current']:.3f} ({delta_str})")

    print("\n" + "=" * 80)


def main():
    """Main comparison function."""
    # Load baseline (Stage 4.1)
    baseline = load_results("evaluation/baseline_results.json")

    # Load most recent evaluation
    evaluation_dir = Path("evaluation")
    result_files = sorted([f for f in evaluation_dir.glob("results_*.json")])
    latest_file = result_files[-1]
    current = load_results(str(latest_file))

    print(f"Comparing baseline with: {latest_file.name}")

    # Compare metrics
    comparison = compare_metrics(baseline, current)

    # Print report
    print_comparison_report(comparison)

    # Save comparison
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    comparison_file = f"evaluation/comparison_{timestamp}.json"
    with open(comparison_file, 'w') as f:
        json.dump(comparison, f, indent=2)

    print(f"\nComparison saved to: {comparison_file}")


if __name__ == "__main__":
    main()
