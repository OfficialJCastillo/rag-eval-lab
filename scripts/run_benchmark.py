from pathlib import Path
import json
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.schemas.models import BenchmarkCase
from app.schemas.models import BenchmarkRequest
from app.services.pipeline import RAGEvaluationPipeline


def build_default_cases() -> list[BenchmarkCase]:
    return [
        BenchmarkCase(
            question="When can a missed class be treated as excused?",
            expected_keywords=["excused", "absence", "illness"],
            expected_chunk_ids=["university_policy_sample-chunk-1"],
        ),
        BenchmarkCase(
            question="What happens to coursework turned in after the cutoff?",
            expected_keywords=["late", "deadline", "penalty"],
            expected_chunk_ids=["university_policy_sample-chunk-2"],
        ),
        BenchmarkCase(
            question="How should someone disclose a security flaw before a fix is ready?",
            expected_keywords=["security", "privately", "public issue"],
            expected_chunk_ids=["opensource_maintainer_guide-chunk-1"],
        ),
        BenchmarkCase(
            question="Which release track should cautious teams choose if they value stability?",
            expected_keywords=["predictable", "support", "breaking changes"],
            expected_chunk_ids=["opensource_maintainer_guide-chunk-2"],
        ),
        BenchmarkCase(
            question="What approvals are needed before buying home office gear?",
            expected_keywords=["manager approval", "equipment", "purchase"],
            expected_chunk_ids=["public_operations_manual-chunk-2"],
        ),
        BenchmarkCase(
            question="Which checks happen before software handling customer information can be bought?",
            expected_keywords=["procurement review", "security assessment", "customer data"],
            expected_chunk_ids=["public_operations_manual-chunk-3"],
        ),
        BenchmarkCase(
            question="Can business travelers claim alcohol with their meal receipts?",
            expected_keywords=["meal reimbursement", "alcohol", "receipts"],
            expected_chunk_ids=["public_operations_manual-chunk-1"],
        ),
        BenchmarkCase(
            question="How should on-call ownership be shared to prevent burnout?",
            expected_keywords=["rotate", "pager", "fatigue"],
            expected_chunk_ids=["incident_response_playbook-chunk-1"],
        ),
        BenchmarkCase(
            question="Who can reverse a bad deployment during an outage?",
            expected_keywords=["incident commander", "release lead", "reverting"],
            expected_chunk_ids=["incident_response_playbook-chunk-2"],
        ),
        BenchmarkCase(
            question="What should take priority over writing the full incident timeline?",
            expected_keywords=["restore service", "timeline", "outage"],
            expected_chunk_ids=["incident_response_playbook-chunk-2"],
        ),
        BenchmarkCase(
            question="Who reviews a routine restart before planned maintenance begins?",
            expected_keywords=["checklist review", "operations coordinator", "planned maintenance"],
            expected_chunk_ids=["incident_response_playbook-chunk-3"],
        ),
        BenchmarkCase(
            question="Does the playbook require weekend pager coverage?",
            expected_keywords=[],
            expected_chunk_ids=[],
        ),
    ]


def main() -> None:
    pipeline = RAGEvaluationPipeline()
    request = BenchmarkRequest(
        run_id="semantic-tfidf-retrieval",
        retrieval_strategy="semantic",
        top_k=5,
        cases=build_default_cases(),
    )
    result = pipeline.run_benchmark(request)
    output_path = Path("results") / f"{result.run_id}.json"
    output_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    print(json.dumps(result.model_dump(), indent=2))


if __name__ == "__main__":
    main()
