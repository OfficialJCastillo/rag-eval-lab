from app.schemas.models import BenchmarkCase
from app.schemas.models import BenchmarkComparisonResult
from app.schemas.models import BenchmarkRequest
from app.schemas.models import QueryRequest
from app.evaluation.metrics import retrieval_mrr
from app.evaluation.metrics import retrieval_ndcg
from app.retrieval.index import Chunk
from app.retrieval.index import RetrievedChunk
from scripts.compare_benchmarks import build_requests
from app.services.pipeline import RAGEvaluationPipeline
from scripts.compare_benchmarks import build_metric_deltas


def test_query_and_benchmark_smoke() -> None:
    pipeline = RAGEvaluationPipeline()

    semantic_query_response = pipeline.answer_question(
        QueryRequest(
            question="What happens if work is submitted late?",
            corpus_dir="data/raw",
            top_k=2,
            retrieval_strategy="semantic",
        )
    )
    assert semantic_query_response.question
    assert semantic_query_response.retrieved_chunk_ids
    assert semantic_query_response.citations
    assert semantic_query_response.citation_checks
    assert semantic_query_response.retrieval_strategy == "semantic"

    keyword_query_response = pipeline.answer_question(
        QueryRequest(
            question="What is an excused absence?",
            corpus_dir="data/raw",
            top_k=2,
            retrieval_strategy="keyword",
        )
    )
    assert keyword_query_response.retrieval_strategy == "keyword"
    assert keyword_query_response.citations[0].retrieval_score >= 0.0

    benchmark_response = pipeline.run_benchmark(
        BenchmarkRequest(
            corpus_dir="data/raw",
            top_k=2,
            retrieval_strategy="semantic",
            cases=[
                BenchmarkCase(
                    question="What is an excused absence?",
                    expected_keywords=["excused", "absence"],
                )
            ],
        )
    )
    assert benchmark_response.question_count == 1
    assert benchmark_response.case_results
    assert benchmark_response.case_results[0]["citation_checks"]


def test_metric_delta_builder() -> None:
    comparison = BenchmarkComparisonResult(
        comparison_id="keyword-vs-semantic",
        strategies=[],
        metric_deltas=build_metric_deltas(
            [
                RAGEvaluationPipeline().run_benchmark(
                    BenchmarkRequest(
                        retrieval_strategy="keyword",
                        cases=[
                            BenchmarkCase(
                                question="What is an excused absence?",
                                expected_keywords=["excused", "absence"],
                            )
                        ],
                    )
                ),
                RAGEvaluationPipeline().run_benchmark(
                    BenchmarkRequest(
                        retrieval_strategy="semantic",
                        cases=[
                            BenchmarkCase(
                                question="What is an excused absence?",
                                expected_keywords=["excused", "absence"],
                            )
                        ],
                    )
                ),
            ]
        ),
    )
    assert "semantic_tfidf_retrieval_relevance_delta" in comparison.metric_deltas


def test_compare_requests_include_lexical_baselines() -> None:
    strategies = [request.retrieval_strategy for request in build_requests()]
    assert "keyword" in strategies
    assert "semantic" in strategies
    if "embedding_strong" in strategies:
        assert "embedding" in strategies
    if "embedding_strong_rerank" in strategies:
        assert "embedding_strong" in strategies


def test_rank_metrics_reward_earlier_hits() -> None:
    retrieved = [
        RetrievedChunk(chunk=Chunk(chunk_id="a", document_id="doc", text="alpha"), score=0.9),
        RetrievedChunk(chunk=Chunk(chunk_id="b", document_id="doc", text="beta"), score=0.8),
        RetrievedChunk(chunk=Chunk(chunk_id="c", document_id="doc", text="gamma"), score=0.7),
    ]
    assert retrieval_mrr(retrieved, ["b"]) == 0.5
    assert round(retrieval_ndcg(retrieved, ["b"]), 4) == 0.6309
