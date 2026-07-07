from __future__ import annotations

from datetime import UTC
from datetime import datetime
from pathlib import Path
import json
import sqlite3

from app.schemas.models import BenchmarkComparisonResult
from app.schemas.models import BenchmarkResult


DEFAULT_HISTORY_PATH = Path("results") / "benchmark-history.sqlite3"
TREND_METRICS = [
    "average_retrieval_hit_rate",
    "average_retrieval_mrr",
    "average_retrieval_ndcg",
    "average_answer_faithfulness",
]


def initialize_history_db(db_path: Path = DEFAULT_HISTORY_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS benchmark_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comparison_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                strategy_count INTEGER NOT NULL,
                payload_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS benchmark_strategy_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                benchmark_run_id INTEGER NOT NULL REFERENCES benchmark_runs(id) ON DELETE CASCADE,
                run_id TEXT NOT NULL,
                retrieval_strategy TEXT NOT NULL,
                average_retrieval_relevance REAL NOT NULL,
                average_retrieval_hit_rate REAL NOT NULL,
                average_retrieval_mrr REAL NOT NULL,
                average_retrieval_ndcg REAL NOT NULL,
                average_citation_support REAL NOT NULL,
                average_answer_faithfulness REAL NOT NULL,
                payload_json TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_benchmark_runs_created_at
                ON benchmark_runs(created_at);
            CREATE INDEX IF NOT EXISTS idx_benchmark_strategy_results_run
                ON benchmark_strategy_results(run_id, retrieval_strategy);
            """
        )


def record_comparison_run(
    comparison: BenchmarkComparisonResult,
    results: list[BenchmarkResult],
    db_path: Path = DEFAULT_HISTORY_PATH,
    created_at: str | None = None,
) -> int:
    initialize_history_db(db_path)
    timestamp = created_at or datetime.now(UTC).isoformat(timespec="seconds")
    result_by_run_id = {result.run_id: result for result in results}

    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        cursor = connection.execute(
            """
            INSERT INTO benchmark_runs (
                comparison_id,
                created_at,
                strategy_count,
                payload_json
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                comparison.comparison_id,
                timestamp,
                len(comparison.strategies),
                comparison.model_dump_json(),
            ),
        )
        benchmark_run_id = int(cursor.lastrowid)

        for strategy in comparison.strategies:
            try:
                result = result_by_run_id[strategy.run_id]
            except KeyError as error:
                raise ValueError(
                    f"Missing benchmark result for strategy run {strategy.run_id}"
                ) from error
            connection.execute(
                """
                INSERT INTO benchmark_strategy_results (
                    benchmark_run_id,
                    run_id,
                    retrieval_strategy,
                    average_retrieval_relevance,
                    average_retrieval_hit_rate,
                    average_retrieval_mrr,
                    average_retrieval_ndcg,
                    average_citation_support,
                    average_answer_faithfulness,
                    payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    benchmark_run_id,
                    strategy.run_id,
                    strategy.retrieval_strategy,
                    strategy.average_retrieval_relevance,
                    strategy.average_retrieval_hit_rate,
                    strategy.average_retrieval_mrr,
                    strategy.average_retrieval_ndcg,
                    strategy.average_citation_support,
                    strategy.average_answer_faithfulness,
                    result.model_dump_json(),
                ),
            )

    return benchmark_run_id


def list_history_runs(db_path: Path = DEFAULT_HISTORY_PATH) -> list[dict]:
    initialize_history_db(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT
                id,
                comparison_id,
                created_at,
                strategy_count
            FROM benchmark_runs
            ORDER BY created_at DESC, id DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def load_history_run(run_id: int, db_path: Path = DEFAULT_HISTORY_PATH) -> dict:
    initialize_history_db(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        run = connection.execute(
            """
            SELECT
                id,
                comparison_id,
                created_at,
                strategy_count,
                payload_json
            FROM benchmark_runs
            WHERE id = ?
            """,
            (run_id,),
        ).fetchone()
        if run is None:
            raise KeyError(f"Benchmark history run {run_id} was not found")

        strategies = connection.execute(
            """
            SELECT
                run_id,
                retrieval_strategy,
                average_retrieval_relevance,
                average_retrieval_hit_rate,
                average_retrieval_mrr,
                average_retrieval_ndcg,
                average_citation_support,
                average_answer_faithfulness,
                payload_json
            FROM benchmark_strategy_results
            WHERE benchmark_run_id = ?
            ORDER BY id
            """,
            (run_id,),
        ).fetchall()

    run_dict = dict(run)
    run_dict["payload"] = json.loads(run_dict.pop("payload_json"))
    run_dict["strategies"] = [
        {**dict(row), "payload": json.loads(row["payload_json"])}
        for row in strategies
    ]
    for strategy in run_dict["strategies"]:
        strategy.pop("payload_json")
    return run_dict


def build_history_trends(
    db_path: Path = DEFAULT_HISTORY_PATH,
    limit: int = 10,
) -> list[dict]:
    if limit < 1:
        raise ValueError("History trend limit must be at least 1")

    initialize_history_db(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        runs = connection.execute(
            """
            SELECT
                id,
                comparison_id,
                created_at
            FROM benchmark_runs
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        run_ids = [row["id"] for row in runs]
        if not run_ids:
            return []

        placeholders = ",".join("?" for _id in run_ids)
        strategy_rows = connection.execute(
            f"""
            SELECT
                benchmark_run_id,
                run_id,
                retrieval_strategy,
                average_retrieval_hit_rate,
                average_retrieval_mrr,
                average_retrieval_ndcg,
                average_answer_faithfulness
            FROM benchmark_strategy_results
            WHERE benchmark_run_id IN ({placeholders})
            ORDER BY benchmark_run_id, id
            """,
            run_ids,
        ).fetchall()

    runs_by_id = {
        row["id"]: {
            "id": row["id"],
            "comparison_id": row["comparison_id"],
            "created_at": row["created_at"],
            "strategies": {},
        }
        for row in reversed(runs)
    }
    for row in strategy_rows:
        run = runs_by_id[row["benchmark_run_id"]]
        run["strategies"][row["retrieval_strategy"]] = {
            "run_id": row["run_id"],
            **{metric: row[metric] for metric in TREND_METRICS},
        }

    runs_chronological = list(runs_by_id.values())
    return [
        _summarize_strategy_trend(strategy, runs_chronological)
        for strategy in _strategy_names(runs_by_id)
    ]


def _strategy_names(runs_by_id: dict[int, dict]) -> list[str]:
    names = {
        strategy_name
        for run in runs_by_id.values()
        for strategy_name in run["strategies"]
    }
    return sorted(names)


def _summarize_strategy_trend(strategy_name: str, runs: list[dict]) -> dict:
    points = []
    for run in runs:
        strategy = run["strategies"].get(strategy_name)
        if strategy is None:
            continue
        points.append(
            {
                "history_run_id": run["id"],
                "comparison_id": run["comparison_id"],
                "created_at": run["created_at"],
                "run_id": strategy["run_id"],
                **{metric: strategy[metric] for metric in TREND_METRICS},
            }
        )

    latest = points[-1] if points else None
    previous = points[-2] if len(points) > 1 else None
    return {
        "retrieval_strategy": strategy_name,
        "points": points,
        "latest": latest,
        "previous": previous,
        "deltas": _metric_deltas(latest, previous),
    }


def _metric_deltas(latest: dict | None, previous: dict | None) -> dict:
    if latest is None or previous is None:
        return {}
    return {
        metric: latest[metric] - previous[metric]
        for metric in TREND_METRICS
    }
