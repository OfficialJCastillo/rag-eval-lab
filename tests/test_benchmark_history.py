import json
import sqlite3

from app.evaluation.history import build_history_trends
from app.evaluation.history import initialize_history_db
from app.evaluation.history import list_history_runs
from app.evaluation.history import load_history_run
from app.evaluation.history import record_comparison_run
from app.schemas.models import BenchmarkComparisonResult
from app.schemas.models import BenchmarkResult
from app.schemas.models import StrategySummary


def make_result(run_id: str, retrieval_strategy: str, mrr: float) -> BenchmarkResult:
    return BenchmarkResult(
        run_id=run_id,
        question_count=1,
        average_retrieval_relevance=0.5,
        average_retrieval_hit_rate=1.0,
        average_retrieval_mrr=mrr,
        average_retrieval_ndcg=0.9,
        average_citation_support=1.0,
        average_answer_faithfulness=0.85,
        case_results=[
            {
                "question": "What is tracked?",
                "retrieval_strategy": retrieval_strategy,
                "retrieved_chunk_ids": ["doc-chunk-1"],
            }
        ],
    )


def make_comparison(results: list[BenchmarkResult]) -> BenchmarkComparisonResult:
    return BenchmarkComparisonResult(
        comparison_id="test-comparison",
        strategies=[
            StrategySummary(
                run_id=result.run_id,
                retrieval_strategy=result.case_results[0]["retrieval_strategy"],
                average_retrieval_relevance=result.average_retrieval_relevance,
                average_retrieval_hit_rate=result.average_retrieval_hit_rate,
                average_retrieval_mrr=result.average_retrieval_mrr,
                average_retrieval_ndcg=result.average_retrieval_ndcg,
                average_citation_support=result.average_citation_support,
                average_answer_faithfulness=result.average_answer_faithfulness,
            )
            for result in results
        ],
        metric_deltas={"semantic_retrieval_mrr_delta": -0.1},
    )


def test_initialize_history_db_creates_expected_tables(tmp_path) -> None:
    db_path = tmp_path / "history.sqlite3"

    initialize_history_db(db_path)

    with sqlite3.connect(db_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

    assert "benchmark_runs" in tables
    assert "benchmark_strategy_results" in tables


def test_record_and_load_comparison_history(tmp_path) -> None:
    db_path = tmp_path / "history.sqlite3"
    results = [
        make_result("baseline-keyword-retrieval", "keyword", 0.9),
        make_result("semantic-tfidf-retrieval", "semantic", 0.8),
    ]
    comparison = make_comparison(results)

    run_id = record_comparison_run(
        comparison,
        results,
        db_path=db_path,
        created_at="2026-07-06T12:00:00+00:00",
    )

    rows = list_history_runs(db_path)
    loaded = load_history_run(run_id, db_path)

    assert rows == [
        {
            "id": run_id,
            "comparison_id": "test-comparison",
            "created_at": "2026-07-06T12:00:00+00:00",
            "strategy_count": 2,
        }
    ]
    assert loaded["payload"]["metric_deltas"] == {"semantic_retrieval_mrr_delta": -0.1}
    assert [strategy["retrieval_strategy"] for strategy in loaded["strategies"]] == [
        "keyword",
        "semantic",
    ]
    assert loaded["strategies"][1]["payload"]["run_id"] == "semantic-tfidf-retrieval"


def test_history_payloads_are_valid_json(tmp_path) -> None:
    db_path = tmp_path / "history.sqlite3"
    result = make_result("baseline-keyword-retrieval", "keyword", 0.9)
    comparison = make_comparison([result])

    record_comparison_run(comparison, [result], db_path=db_path)

    with sqlite3.connect(db_path) as connection:
        payloads = [
            row[0]
            for row in connection.execute(
                """
                SELECT payload_json FROM benchmark_runs
                UNION ALL
                SELECT payload_json FROM benchmark_strategy_results
                """
            ).fetchall()
        ]

    assert payloads
    assert all(json.loads(payload) for payload in payloads)


def test_record_comparison_requires_matching_results(tmp_path) -> None:
    db_path = tmp_path / "history.sqlite3"
    result = make_result("baseline-keyword-retrieval", "keyword", 0.9)
    comparison = make_comparison([result])

    try:
        record_comparison_run(comparison, [], db_path=db_path)
    except ValueError as error:
        assert "baseline-keyword-retrieval" in str(error)
    else:
        raise AssertionError("Expected missing benchmark result to fail")


def test_build_history_trends_summarizes_recent_metric_changes(tmp_path) -> None:
    db_path = tmp_path / "history.sqlite3"
    first_results = [
        make_result("baseline-keyword-retrieval", "keyword", 0.9),
        make_result("semantic-tfidf-retrieval", "semantic", 0.8),
    ]
    second_results = [
        make_result("baseline-keyword-retrieval", "keyword", 0.95),
        make_result("semantic-tfidf-retrieval", "semantic", 0.7),
    ]

    record_comparison_run(
        make_comparison(first_results),
        first_results,
        db_path=db_path,
        created_at="2026-07-06T12:00:00+00:00",
    )
    record_comparison_run(
        make_comparison(second_results),
        second_results,
        db_path=db_path,
        created_at="2026-07-06T13:00:00+00:00",
    )

    trends = build_history_trends(db_path)
    by_strategy = {trend["retrieval_strategy"]: trend for trend in trends}

    keyword_mrr_values = [
        point["average_retrieval_mrr"]
        for point in by_strategy["keyword"]["points"]
    ]
    assert keyword_mrr_values == [
        0.9,
        0.95,
    ]
    keyword_mrr_delta = by_strategy["keyword"]["deltas"]["average_retrieval_mrr"]
    semantic_mrr_delta = by_strategy["semantic"]["deltas"]["average_retrieval_mrr"]
    assert round(keyword_mrr_delta, 4) == 0.05
    assert round(semantic_mrr_delta, 4) == -0.1
