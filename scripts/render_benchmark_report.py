from pathlib import Path
import json
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


RESULTS_DIR = PROJECT_ROOT / "results"
COMPARISON_PATH = RESULTS_DIR / "retrieval-backend-comparison.json"
OUTPUT_PATH = RESULTS_DIR / "benchmark-report.md"


def main() -> None:
    comparison = json.loads(COMPARISON_PATH.read_text(encoding="utf-8"))
    lines: list[str] = [
        "# Benchmark Report",
        "",
        "Generated from `results/retrieval-backend-comparison.json` and per-strategy run artifacts.",
        "",
        "## Strategy Summary",
        "",
        "| Strategy | Hit Rate | MRR | nDCG | Faithfulness |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]

    for strategy in comparison["strategies"]:
        lines.append(
            "| `{}` | {:.4f} | {:.4f} | {:.4f} | {:.4f} |".format(
                strategy["retrieval_strategy"],
                strategy["average_retrieval_hit_rate"],
                strategy["average_retrieval_mrr"],
                strategy["average_retrieval_ndcg"],
                strategy["average_answer_faithfulness"],
            )
        )

    lines.extend(
        [
            "",
            "## Key Findings",
            "",
            "- `keyword` remains a strong lexical baseline on this benchmark.",
            "- Dense retrieval improves answer faithfulness slightly, but embedding-only variants trail the lexical baseline on rank-sensitive metrics.",
            "- `embedding_strong_rerank` matches the lexical baseline on `MRR` and `nDCG`, which suggests second-stage ranking quality matters more than stronger dense retrieval alone.",
            "",
            "## Case Notes",
            "",
        ]
    )

    lines.extend(build_case_notes(comparison))
    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")


def build_case_notes(comparison: dict) -> list[str]:
    by_strategy = {}
    for strategy in comparison["strategies"]:
        run_path = RESULTS_DIR / f"{strategy['run_id']}.json"
        by_strategy[strategy["retrieval_strategy"]] = json.loads(run_path.read_text(encoding="utf-8"))

    keyword_rows = index_cases(by_strategy["keyword"]["case_results"])
    embedding_rows = index_cases(by_strategy["embedding"]["case_results"])
    rerank_rows = index_cases(by_strategy["embedding_strong_rerank"]["case_results"])

    notes: list[str] = []

    timeline_question = "What should take priority over writing the full incident timeline?"
    timeline_embedding = embedding_rows[timeline_question]
    timeline_rerank = rerank_rows[timeline_question]
    notes.extend(
        [
            f"- `{timeline_question}`",
            f"  `embedding` ranked `{timeline_embedding['retrieved_chunk_ids'][0]}` first and pushed the correct chunk to rank 2 (`MRR={timeline_embedding['retrieval_mrr']:.1f}`).",
            f"  `embedding_strong_rerank` restored `{timeline_rerank['retrieved_chunk_ids'][0]}` to rank 1 (`MRR={timeline_rerank['retrieval_mrr']:.1f}`).",
        ]
    )

    security_question = "How should someone disclose a security flaw before a fix is ready?"
    security_keyword = keyword_rows[security_question]
    security_embedding = embedding_rows[security_question]
    security_rerank = rerank_rows[security_question]
    notes.extend(
        [
            f"- `{security_question}`",
            f"  `keyword` starts with `{security_keyword['retrieved_chunk_ids'][0]}` followed by `{security_keyword['retrieved_chunk_ids'][1]}`.",
            f"  `embedding` pulls in the near-miss `{security_embedding['retrieved_chunk_ids'][1]}` at rank 2, while `embedding_strong_rerank` restores `{security_rerank['retrieved_chunk_ids'][1]}` as the stronger second result.",
        ]
    )

    unanswerable_question = "Does the playbook require weekend pager coverage?"
    unanswerable_keyword = keyword_rows[unanswerable_question]
    unanswerable_rerank = rerank_rows[unanswerable_question]
    notes.extend(
        [
            f"- `{unanswerable_question}`",
            f"  Both `keyword` and `embedding_strong_rerank` remain unsupported here (`MRR={unanswerable_keyword['retrieval_mrr']:.1f}` and `{unanswerable_rerank['retrieval_mrr']:.1f}`), which keeps an explicit unanswerable check in the benchmark.",
        ]
    )

    return notes


def index_cases(rows: list[dict]) -> dict[str, dict]:
    return {row["question"]: row for row in rows}


if __name__ == "__main__":
    main()
