from pydantic import BaseModel
from pydantic import Field


class HealthResponse(BaseModel):
    status: str


class Citation(BaseModel):
    chunk_id: str
    document_id: str
    snippet: str
    retrieval_score: float
    support_score: float | None = None
    supported: bool | None = None


class CitationCheck(BaseModel):
    chunk_id: str
    document_id: str
    claim_text: str
    support_score: float
    supported: bool


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3)
    top_k: int = Field(default=3, ge=1, le=10)
    corpus_dir: str = Field(default="data/raw")
    retrieval_strategy: str = Field(default="semantic")


class QueryResponse(BaseModel):
    question: str
    answer: str
    citations: list[Citation]
    retrieved_chunk_ids: list[str]
    retrieval_strategy: str
    citation_checks: list[CitationCheck]
    unsupported_claims: list[str]


class BenchmarkCase(BaseModel):
    question: str
    expected_keywords: list[str] = Field(default_factory=list)
    expected_chunk_ids: list[str] = Field(default_factory=list)


class BenchmarkRequest(BaseModel):
    run_id: str = Field(default="semantic-tfidf-retrieval")
    corpus_dir: str = Field(default="data/raw")
    top_k: int = Field(default=3, ge=1, le=10)
    retrieval_strategy: str = Field(default="semantic")
    cases: list[BenchmarkCase]


class BenchmarkResult(BaseModel):
    run_id: str
    question_count: int
    average_retrieval_relevance: float
    average_retrieval_hit_rate: float
    average_retrieval_mrr: float
    average_retrieval_ndcg: float
    average_citation_support: float
    average_answer_faithfulness: float
    case_results: list[dict]


class StrategySummary(BaseModel):
    run_id: str
    retrieval_strategy: str
    average_retrieval_relevance: float
    average_retrieval_hit_rate: float
    average_retrieval_mrr: float
    average_retrieval_ndcg: float
    average_citation_support: float
    average_answer_faithfulness: float


class BenchmarkComparisonResult(BaseModel):
    comparison_id: str
    strategies: list[StrategySummary]
    metric_deltas: dict[str, float]
