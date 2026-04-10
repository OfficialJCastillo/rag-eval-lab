from app.retrieval.index import Chunk
from app.retrieval.index import RetrievedChunk
from app.retrieval.index import unique_tokens
import math


def retrieval_relevance_at_k(retrieved_chunks: list[RetrievedChunk], expected_keywords: list[str]) -> float:
    if not retrieved_chunks:
        return 0.0
    if not expected_keywords:
        return 1.0
    expected = {keyword.lower() for keyword in expected_keywords}
    relevant = 0
    for chunk in retrieved_chunks:
        if expected.intersection(unique_tokens(chunk.chunk.text)):
            relevant += 1
    return relevant / len(retrieved_chunks)


def retrieval_hit_rate_at_k(retrieved_chunks: list[RetrievedChunk], expected_chunk_ids: list[str]) -> float:
    if not expected_chunk_ids:
        return 0.0
    retrieved_ids = {item.chunk.chunk_id for item in retrieved_chunks}
    expected_ids = set(expected_chunk_ids)
    return len(retrieved_ids.intersection(expected_ids)) / len(expected_ids)


def retrieval_mrr(retrieved_chunks: list[RetrievedChunk], expected_chunk_ids: list[str]) -> float:
    if not expected_chunk_ids:
        return 0.0
    expected_ids = set(expected_chunk_ids)
    for index, item in enumerate(retrieved_chunks, start=1):
        if item.chunk.chunk_id in expected_ids:
            return 1.0 / index
    return 0.0


def retrieval_ndcg(retrieved_chunks: list[RetrievedChunk], expected_chunk_ids: list[str]) -> float:
    if not expected_chunk_ids:
        return 0.0

    expected_ids = set(expected_chunk_ids)
    dcg = 0.0
    for index, item in enumerate(retrieved_chunks, start=1):
        if item.chunk.chunk_id in expected_ids:
            dcg += 1.0 / math.log2(index + 1)

    ideal_hits = min(len(expected_ids), len(retrieved_chunks))
    if ideal_hits == 0:
        return 0.0
    ideal_dcg = sum(1.0 / math.log2(index + 1) for index in range(1, ideal_hits + 1))
    return dcg / ideal_dcg


def citation_support(citation_checks: list[dict]) -> float:
    if not citation_checks:
        return 0.0
    supported = sum(1 for check in citation_checks if check["supported"])
    return supported / len(citation_checks)


def answer_faithfulness(answer: str, retrieved_chunks: list[RetrievedChunk]) -> float:
    if not answer or not retrieved_chunks:
        return 0.0
    answer_tokens = unique_tokens(answer)
    context_tokens = set()
    for chunk in retrieved_chunks:
        context_tokens.update(unique_tokens(chunk.chunk.text))
    if not answer_tokens:
        return 0.0
    overlap = len(answer_tokens.intersection(context_tokens))
    return overlap / len(answer_tokens)


def claim_support_score(claim_text: str, chunk: Chunk) -> float:
    claim_tokens = unique_tokens(claim_text)
    chunk_tokens = unique_tokens(chunk.text)
    if not claim_tokens or not chunk_tokens:
        return 0.0
    overlap = len(claim_tokens.intersection(chunk_tokens))
    return overlap / len(claim_tokens)
