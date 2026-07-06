from pathlib import Path
import json

from scripts.render_benchmark_report_html import render_html


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "results"
COMPARISON_PATH = RESULTS_DIR / "retrieval-backend-comparison.json"
REPORT_PATH = RESULTS_DIR / "benchmark-report.md"
HTML_REPORT_PATH = RESULTS_DIR / "benchmark-report.html"

EXPECTED_STRATEGIES = [
    "keyword",
    "semantic",
    "embedding",
    "embedding_strong",
    "embedding_strong_rerank",
]

METRIC_FLOORS = {
    "average_retrieval_hit_rate": 0.90,
    "average_retrieval_mrr": 0.80,
    "average_retrieval_ndcg": 0.85,
    "average_citation_support": 0.95,
    "average_answer_faithfulness": 0.80,
}

TOLERANCE = 0.0001


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_committed_benchmark_snapshot_stays_above_metric_floors() -> None:
    comparison = load_json(COMPARISON_PATH)
    strategies = comparison["strategies"]

    assert [strategy["retrieval_strategy"] for strategy in strategies] == EXPECTED_STRATEGIES

    for strategy in strategies:
        for metric, floor in METRIC_FLOORS.items():
            assert strategy[metric] >= floor, f"{strategy['retrieval_strategy']} {metric} regressed"


def test_comparison_summary_matches_per_strategy_artifacts() -> None:
    comparison = load_json(COMPARISON_PATH)

    for strategy in comparison["strategies"]:
        run_artifact = load_json(RESULTS_DIR / f"{strategy['run_id']}.json")

        assert run_artifact["question_count"] == 12
        assert len(run_artifact["case_results"]) == run_artifact["question_count"]

        for metric in METRIC_FLOORS:
            assert abs(strategy[metric] - run_artifact[metric]) <= TOLERANCE


def test_rerank_pipeline_preserves_keyword_rank_quality() -> None:
    comparison = load_json(COMPARISON_PATH)
    by_strategy = {strategy["retrieval_strategy"]: strategy for strategy in comparison["strategies"]}

    keyword = by_strategy["keyword"]
    dense = by_strategy["embedding_strong"]
    rerank = by_strategy["embedding_strong_rerank"]

    assert dense["average_retrieval_mrr"] < keyword["average_retrieval_mrr"]
    assert dense["average_retrieval_ndcg"] < keyword["average_retrieval_ndcg"]
    assert rerank["average_retrieval_mrr"] >= keyword["average_retrieval_mrr"] - TOLERANCE
    assert rerank["average_retrieval_ndcg"] >= keyword["average_retrieval_ndcg"] - TOLERANCE


def test_rendered_report_matches_comparison_snapshot_table() -> None:
    comparison = load_json(COMPARISON_PATH)
    report = REPORT_PATH.read_text(encoding="utf-8")

    for strategy in comparison["strategies"]:
        expected_row = (
            "| `{}` | {:.4f} | {:.4f} | {:.4f} | {:.4f} |".format(
                strategy["retrieval_strategy"],
                strategy["average_retrieval_hit_rate"],
                strategy["average_retrieval_mrr"],
                strategy["average_retrieval_ndcg"],
                strategy["average_answer_faithfulness"],
            )
        )
        assert expected_row in report


def test_rendered_html_report_matches_comparison_snapshot() -> None:
    comparison = load_json(COMPARISON_PATH)
    report = HTML_REPORT_PATH.read_text(encoding="utf-8")

    assert report == render_html(comparison)
    assert 'src="../docs/benchmark-snapshot.svg"' in report

    for strategy in comparison["strategies"]:
        assert f"<code>{strategy['retrieval_strategy']}</code>" in report
        for metric in METRIC_FLOORS:
            if metric == "average_citation_support":
                continue
            assert f"{strategy[metric]:.4f}" in report


def test_html_report_includes_metric_deltas() -> None:
    comparison = load_json(COMPARISON_PATH)
    report = HTML_REPORT_PATH.read_text(encoding="utf-8")

    for key, value in comparison["metric_deltas"].items():
        if not key.endswith(("retrieval_hit_rate_delta", "retrieval_mrr_delta", "retrieval_ndcg_delta", "answer_faithfulness_delta")):
            continue
        expected = f"+{value:.4f}" if value > 0 else f"{value:.4f}"
        assert expected in report
