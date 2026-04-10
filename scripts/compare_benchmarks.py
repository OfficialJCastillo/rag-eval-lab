from pathlib import Path
import json
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.schemas.models import BenchmarkComparisonResult
from app.schemas.models import BenchmarkRequest
from app.schemas.models import StrategySummary
from app.retrieval.index import available_strategies
from app.services.pipeline import RAGEvaluationPipeline
from scripts.run_benchmark import build_default_cases


def main() -> None:
    pipeline = RAGEvaluationPipeline()
    requests = build_requests()

    results = [pipeline.run_benchmark(request) for request in requests]
    for result in results:
        output_path = Path("results") / f"{result.run_id}.json"
        output_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")

    comparison = BenchmarkComparisonResult(
        comparison_id="retrieval-backend-comparison",
        strategies=[
            StrategySummary(
                run_id=result.run_id,
                retrieval_strategy=request.retrieval_strategy,
                average_retrieval_relevance=result.average_retrieval_relevance,
                average_retrieval_hit_rate=result.average_retrieval_hit_rate,
                average_retrieval_mrr=result.average_retrieval_mrr,
                average_retrieval_ndcg=result.average_retrieval_ndcg,
                average_citation_support=result.average_citation_support,
                average_answer_faithfulness=result.average_answer_faithfulness,
            )
            for request, result in zip(requests, results, strict=True)
        ],
        metric_deltas=build_metric_deltas(results),
    )

    comparison_path = Path("results") / f"{comparison.comparison_id}.json"
    comparison_path.write_text(comparison.model_dump_json(indent=2), encoding="utf-8")
    print(json.dumps(comparison.model_dump(), indent=2))


def build_requests() -> list[BenchmarkRequest]:
    run_ids = {
        "keyword": "baseline-keyword-retrieval",
        "semantic": "semantic-tfidf-retrieval",
        "embedding": "embedding-retrieval",
        "embedding_strong": "embedding-strong-retrieval",
        "embedding_strong_rerank": "embedding-strong-rerank-retrieval",
    }
    return [
        BenchmarkRequest(
            run_id=run_ids[strategy],
            retrieval_strategy=strategy,
            top_k=5,
            cases=build_default_cases(),
        )
        for strategy in available_strategies()
    ]


def build_metric_deltas(results: list) -> dict[str, float]:
    if len(results) < 2:
        return {}

    baseline = results[0]
    deltas: dict[str, float] = {}
    for candidate in results[1:]:
        prefix = candidate.run_id.replace("-retrieval", "").replace("-", "_")
        deltas[f"{prefix}_retrieval_relevance_delta"] = round(
            candidate.average_retrieval_relevance - baseline.average_retrieval_relevance, 4
        )
        deltas[f"{prefix}_retrieval_hit_rate_delta"] = round(
            candidate.average_retrieval_hit_rate - baseline.average_retrieval_hit_rate, 4
        )
        deltas[f"{prefix}_retrieval_mrr_delta"] = round(
            candidate.average_retrieval_mrr - baseline.average_retrieval_mrr, 4
        )
        deltas[f"{prefix}_retrieval_ndcg_delta"] = round(
            candidate.average_retrieval_ndcg - baseline.average_retrieval_ndcg, 4
        )
        deltas[f"{prefix}_citation_support_delta"] = round(
            candidate.average_citation_support - baseline.average_citation_support, 4
        )
        deltas[f"{prefix}_answer_faithfulness_delta"] = round(
            candidate.average_answer_faithfulness - baseline.average_answer_faithfulness, 4
        )
    return deltas


if __name__ == "__main__":
    main()
