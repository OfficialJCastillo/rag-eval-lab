from app.api.demo_ui import render_demo_ui
from app.schemas.models import BenchmarkRequest
from app.schemas.models import BenchmarkResult
from app.schemas.models import HealthResponse
from app.schemas.models import QueryRequest
from app.schemas.models import QueryResponse
from app.services.pipeline import RAGEvaluationPipeline
from fastapi import APIRouter


router = APIRouter()
pipeline = RAGEvaluationPipeline()


@router.get("/", include_in_schema=False)
def demo_ui():
    return render_demo_ui()


@router.get("/health", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post("/qa/query", response_model=QueryResponse)
def run_query(request: QueryRequest) -> QueryResponse:
    return pipeline.answer_question(request)


@router.post("/qa/benchmark", response_model=BenchmarkResult)
def run_benchmark(request: BenchmarkRequest) -> BenchmarkResult:
    return pipeline.run_benchmark(request)
