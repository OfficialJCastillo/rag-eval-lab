from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Protocol
import math
import numpy as np
import re


WORD_PATTERN = re.compile(r"[A-Za-z0-9]+")
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
STRONG_EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
RERANK_MODEL = "answerdotai/answerai-colbert-small-v1"


class EmbeddingBackendUnavailable(RuntimeError):
    pass


@dataclass
class Chunk:
    chunk_id: str
    document_id: str
    text: str


@dataclass
class RetrievedChunk:
    chunk: Chunk
    score: float


class RetrievalBackend(Protocol):
    strategy_name: str

    def retrieve(self, question: str, chunks: list[Chunk], top_k: int) -> list[RetrievedChunk]:
        ...


class KeywordBackend:
    strategy_name = "keyword"

    def retrieve(self, question: str, chunks: list[Chunk], top_k: int) -> list[RetrievedChunk]:
        question_tokens = set(tokenize(question))
        ranked = sorted(
            chunks,
            key=lambda chunk: (
                len(question_tokens.intersection(unique_tokens(chunk.text))),
                len(chunk.text),
            ),
            reverse=True,
        )
        return [
            RetrievedChunk(
                chunk=chunk,
                score=float(len(question_tokens.intersection(unique_tokens(chunk.text)))),
            )
            for chunk in ranked[:top_k]
        ]


class TfidfBackend:
    strategy_name = "semantic"

    def retrieve(self, question: str, chunks: list[Chunk], top_k: int) -> list[RetrievedChunk]:
        question_vector = _tf_idf_vector(question, chunks)
        scored_chunks = [
            RetrievedChunk(
                chunk=chunk,
                score=_cosine_similarity(question_vector, _tf_idf_vector(chunk.text, chunks)),
            )
            for chunk in chunks
        ]
        scored_chunks.sort(key=lambda item: (item.score, len(item.chunk.text)), reverse=True)
        return scored_chunks[:top_k]


class EmbeddingBackend:
    strategy_name = "embedding"

    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL) -> None:
        self.model_name = model_name

    def retrieve(self, question: str, chunks: list[Chunk], top_k: int) -> list[RetrievedChunk]:
        embedder = _load_embedder(self.model_name)
        texts = [question, *[chunk.text for chunk in chunks]]
        vectors = list(embedder.embed(texts))
        question_vector = vectors[0]
        chunk_vectors = vectors[1:]

        scored_chunks = [
            RetrievedChunk(
                chunk=chunk,
                score=_dense_cosine_similarity(question_vector, chunk_vector),
            )
            for chunk, chunk_vector in zip(chunks, chunk_vectors, strict=True)
        ]
        scored_chunks.sort(key=lambda item: (item.score, len(item.chunk.text)), reverse=True)
        return scored_chunks[:top_k]


class RerankedEmbeddingBackend:
    strategy_name = "embedding_strong_rerank"

    def __init__(self) -> None:
        self.first_stage = EmbeddingBackend(model_name=STRONG_EMBEDDING_MODEL)

    def retrieve(self, question: str, chunks: list[Chunk], top_k: int) -> list[RetrievedChunk]:
        candidates = self.first_stage.retrieve(question, chunks, top_k=max(top_k, min(len(chunks), top_k * 2)))
        reranker = _load_late_interaction_embedder(RERANK_MODEL)
        query_vector = next(reranker.query_embed(question))
        passage_vectors = list(reranker.passage_embed([item.chunk.text for item in candidates]))

        reranked = [
            RetrievedChunk(
                chunk=item.chunk,
                score=_late_interaction_score(query_vector, passage_vector),
            )
            for item, passage_vector in zip(candidates, passage_vectors, strict=True)
        ]
        reranked.sort(key=lambda item: (item.score, len(item.chunk.text)), reverse=True)
        return reranked[:top_k]


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in WORD_PATTERN.findall(text)]


def unique_tokens(text: str) -> set[str]:
    return set(tokenize(text))


def split_sentences(text: str) -> list[str]:
    normalized = re.sub(r"\s*\n\s*", " ", text.strip())
    sentences = [sentence.strip() for sentence in SENTENCE_SPLIT_PATTERN.split(normalized)]
    return [sentence for sentence in sentences if sentence]


def load_text_documents(corpus_dir: str) -> list[Chunk]:
    base_path = Path(corpus_dir)
    chunks: list[Chunk] = []
    for file_path in sorted(base_path.glob("*.txt")):
        text = file_path.read_text(encoding="utf-8").strip()
        if not text:
            continue
        paragraphs = _merge_heading_paragraphs(
            [part.strip() for part in text.split("\n\n") if part.strip()]
        )
        for index, paragraph in enumerate(paragraphs, start=1):
            chunks.append(
                Chunk(
                    chunk_id=f"{file_path.stem}-chunk-{index}",
                    document_id=file_path.stem,
                    text=paragraph,
                )
            )
    return chunks


def retrieve(question: str, chunks: list[Chunk], top_k: int, strategy: str = "semantic") -> list[RetrievedChunk]:
    backend = get_backend(strategy)
    return backend.retrieve(question, chunks, top_k)


def get_backend(strategy: str) -> RetrievalBackend:
    if strategy == "keyword":
        return KeywordBackend()
    if strategy == "semantic":
        return TfidfBackend()
    if strategy == "embedding":
        return EmbeddingBackend()
    if strategy == "embedding_strong":
        return EmbeddingBackend(model_name=STRONG_EMBEDDING_MODEL)
    if strategy == "embedding_strong_rerank":
        return RerankedEmbeddingBackend()
    raise ValueError(f"Unsupported retrieval strategy: {strategy}")


def available_strategies() -> list[str]:
    strategies = ["keyword", "semantic"]
    try:
        _load_embedder(DEFAULT_EMBEDDING_MODEL)
    except EmbeddingBackendUnavailable:
        return strategies
    strategies.append("embedding")
    try:
        _load_embedder(STRONG_EMBEDDING_MODEL)
    except EmbeddingBackendUnavailable:
        return strategies
    strategies.append("embedding_strong")
    try:
        _load_late_interaction_embedder(RERANK_MODEL)
    except EmbeddingBackendUnavailable:
        return strategies
    return [*strategies, "embedding_strong_rerank"]


def _tf_idf_vector(text: str, chunks: list[Chunk]) -> dict[str, float]:
    tokens = tokenize(text)
    if not tokens:
        return {}

    term_counts = Counter(tokens)
    chunk_token_sets = [set(tokenize(chunk.text)) for chunk in chunks]
    document_count = max(len(chunk_token_sets), 1)
    vector: dict[str, float] = {}

    for token, count in term_counts.items():
        document_frequency = sum(1 for chunk_tokens in chunk_token_sets if token in chunk_tokens)
        idf = math.log((document_count + 1) / (document_frequency + 1)) + 1.0
        tf = count / len(tokens)
        vector[token] = tf * idf

    return vector


def _cosine_similarity(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0

    overlap = set(left).intersection(right)
    numerator = sum(left[token] * right[token] for token in overlap)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))

    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return numerator / (left_norm * right_norm)


def _dense_cosine_similarity(left, right) -> float:
    numerator = sum(float(left_value) * float(right_value) for left_value, right_value in zip(left, right))
    left_norm = math.sqrt(sum(float(value) * float(value) for value in left))
    right_norm = math.sqrt(sum(float(value) * float(value) for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return numerator / (left_norm * right_norm)


def _late_interaction_score(query_vector, passage_vector) -> float:
    query_array = np.asarray(query_vector, dtype=np.float32)
    passage_array = np.asarray(passage_vector, dtype=np.float32)
    if query_array.size == 0 or passage_array.size == 0:
        return 0.0

    similarity = query_array @ passage_array.T
    max_sim = similarity.max(axis=1)
    return float(max_sim.sum())


def _merge_heading_paragraphs(paragraphs: list[str]) -> list[str]:
    merged: list[str] = []
    index = 0

    while index < len(paragraphs):
        current = paragraphs[index]
        current_token_count = len(tokenize(current))

        if current_token_count <= 4 and index + 1 < len(paragraphs):
            merged.append(f"{current}\n{paragraphs[index + 1]}")
            index += 2
            continue

        merged.append(current)
        index += 1

    return merged


@lru_cache(maxsize=4)
def _load_embedder(model_name: str):
    try:
        from fastembed import TextEmbedding
    except ImportError as exc:
        raise EmbeddingBackendUnavailable(
            "Embedding backend requires the fastembed package."
        ) from exc

    try:
        return TextEmbedding(model_name=model_name)
    except Exception as exc:
        raise EmbeddingBackendUnavailable(
            f"Unable to load embedding model '{model_name}'."
        ) from exc


@lru_cache(maxsize=2)
def _load_late_interaction_embedder(model_name: str):
    try:
        from fastembed import LateInteractionTextEmbedding
    except ImportError as exc:
        raise EmbeddingBackendUnavailable(
            "Rerank backend requires the fastembed late-interaction package support."
        ) from exc

    try:
        return LateInteractionTextEmbedding(model_name=model_name)
    except Exception as exc:
        raise EmbeddingBackendUnavailable(
            f"Unable to load rerank model '{model_name}'."
        ) from exc
