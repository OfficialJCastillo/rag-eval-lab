from app.evaluation.metrics import answer_faithfulness
from app.evaluation.metrics import citation_support
from app.evaluation.metrics import claim_support_score
from app.evaluation.metrics import retrieval_hit_rate_at_k
from app.evaluation.metrics import retrieval_mrr
from app.evaluation.metrics import retrieval_ndcg
from app.evaluation.metrics import retrieval_relevance_at_k
from app.retrieval.index import Chunk
from app.retrieval.index import load_text_documents
from app.retrieval.index import retrieve
from app.retrieval.index import RetrievedChunk
from app.retrieval.index import split_sentences
from app.retrieval.index import unique_tokens
from app.schemas.models import BenchmarkRequest
from app.schemas.models import BenchmarkResult
from app.schemas.models import Citation
from app.schemas.models import CitationCheck
from app.schemas.models import QueryRequest
from app.schemas.models import QueryResponse


class RAGEvaluationPipeline:
    def answer_question(self, request: QueryRequest) -> QueryResponse:
        chunks = load_text_documents(request.corpus_dir)
        retrieved = retrieve(request.question, chunks, request.top_k, request.retrieval_strategy)
        answer, citation_checks = self._build_grounded_answer(request.question, retrieved)
        citations = [self._citation_from_chunk(chunk, citation_checks) for chunk in retrieved]
        return QueryResponse(
            question=request.question,
            answer=answer,
            citations=citations,
            retrieved_chunk_ids=[item.chunk.chunk_id for item in retrieved],
            retrieval_strategy=request.retrieval_strategy,
            citation_checks=citation_checks,
            unsupported_claims=[check.claim_text for check in citation_checks if not check.supported],
        )

    def run_benchmark(self, request: BenchmarkRequest) -> BenchmarkResult:
        chunks = load_text_documents(request.corpus_dir)
        case_results: list[dict] = []

        for case in request.cases:
            retrieved = retrieve(case.question, chunks, request.top_k, request.retrieval_strategy)
            answer, citation_checks = self._build_grounded_answer(case.question, retrieved)
            cited_chunk_ids = [item.chunk.chunk_id for item in retrieved]

            case_results.append(
                {
                    "question": case.question,
                    "retrieval_strategy": request.retrieval_strategy,
                    "retrieved_chunk_ids": cited_chunk_ids,
                    "retrieval_scores": {
                        item.chunk.chunk_id: round(item.score, 4) for item in retrieved
                    },
                    "retrieval_relevance": retrieval_relevance_at_k(retrieved, case.expected_keywords),
                    "retrieval_hit_rate": retrieval_hit_rate_at_k(retrieved, case.expected_chunk_ids),
                    "retrieval_mrr": retrieval_mrr(retrieved, case.expected_chunk_ids),
                    "retrieval_ndcg": retrieval_ndcg(retrieved, case.expected_chunk_ids),
                    "citation_support": citation_support(
                        [check.model_dump() for check in citation_checks]
                    ),
                    "answer_faithfulness": answer_faithfulness(answer, retrieved),
                    "citation_checks": [check.model_dump() for check in citation_checks],
                }
            )

        question_count = len(case_results)
        return BenchmarkResult(
            run_id=request.run_id,
            question_count=question_count,
            average_retrieval_relevance=self._average(case_results, "retrieval_relevance"),
            average_retrieval_hit_rate=self._average(case_results, "retrieval_hit_rate"),
            average_retrieval_mrr=self._average(case_results, "retrieval_mrr"),
            average_retrieval_ndcg=self._average(case_results, "retrieval_ndcg"),
            average_citation_support=self._average(case_results, "citation_support"),
            average_answer_faithfulness=self._average(case_results, "answer_faithfulness"),
            case_results=case_results,
        )

    def _build_grounded_answer(
        self, question: str, retrieved_chunks: list[RetrievedChunk]
    ) -> tuple[str, list[CitationCheck]]:
        if not retrieved_chunks:
            return f"No supporting context was found for: {question}", []

        question_tokens = unique_tokens(question)
        claims: list[str] = []
        citation_checks: list[CitationCheck] = []

        for item in retrieved_chunks[:2]:
            claim_text = self._select_best_sentence(item.chunk, question_tokens)
            if not claim_text:
                continue
            support_score = claim_support_score(claim_text, item.chunk)
            citation_checks.append(
                CitationCheck(
                    chunk_id=item.chunk.chunk_id,
                    document_id=item.chunk.document_id,
                    claim_text=claim_text,
                    support_score=round(support_score, 4),
                    supported=support_score >= 0.55,
                )
            )
            claims.append(f"{claim_text} [{item.chunk.chunk_id}]")

        if not claims:
            fallback = retrieved_chunks[0].chunk.text[:280].strip()
            return f"Grounded answer draft: {fallback}", citation_checks

        return " ".join(claims), citation_checks

    def _citation_from_chunk(
        self, retrieved_chunk: RetrievedChunk, citation_checks: list[CitationCheck]
    ) -> Citation:
        support_lookup = {check.chunk_id: check for check in citation_checks}
        support = support_lookup.get(retrieved_chunk.chunk.chunk_id)
        return Citation(
            chunk_id=retrieved_chunk.chunk.chunk_id,
            document_id=retrieved_chunk.chunk.document_id,
            snippet=retrieved_chunk.chunk.text[:180],
            retrieval_score=round(retrieved_chunk.score, 4),
            support_score=None if support is None else support.support_score,
            supported=None if support is None else support.supported,
        )

    def _average(self, rows: list[dict], key: str) -> float:
        if not rows:
            return 0.0
        return sum(row[key] for row in rows) / len(rows)

    def _select_best_sentence(self, chunk: Chunk, question_tokens: set[str]) -> str:
        sentences = split_sentences(chunk.text)
        if not sentences:
            return chunk.text[:220].strip()
        ranked = sorted(
            sentences,
            key=lambda sentence: (
                len(question_tokens.intersection(unique_tokens(sentence))),
                len(sentence),
            ),
            reverse=True,
        )
        return ranked[0]
