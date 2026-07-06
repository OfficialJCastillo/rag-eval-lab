from html import escape
from pathlib import Path
import json
import os
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


RESULTS_DIR = PROJECT_ROOT / "results"
COMPARISON_PATH = RESULTS_DIR / "retrieval-backend-comparison.json"
OUTPUT_PATH = RESULTS_DIR / "benchmark-report.html"
SNAPSHOT_PATH = PROJECT_ROOT / "docs" / "benchmark-snapshot.svg"

SUMMARY_METRICS = [
    ("average_retrieval_hit_rate", "Hit Rate"),
    ("average_retrieval_mrr", "MRR"),
    ("average_retrieval_ndcg", "nDCG"),
    ("average_answer_faithfulness", "Faithfulness"),
]

DELTA_METRICS = [
    ("retrieval_hit_rate", "Hit Rate"),
    ("retrieval_mrr", "MRR"),
    ("retrieval_ndcg", "nDCG"),
    ("answer_faithfulness", "Faithfulness"),
]


def main() -> None:
    comparison = json.loads(COMPARISON_PATH.read_text(encoding="utf-8"))
    OUTPUT_PATH.write_text(render_html(comparison), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")


def render_html(comparison: dict) -> str:
    strategies = comparison["strategies"]
    rows = "\n".join(render_strategy_row(strategy) for strategy in strategies)
    delta_rows = "\n".join(render_delta_row(comparison, strategy) for strategy in strategies[1:])
    case_notes = "\n".join(render_case_note(note) for note in build_case_notes())
    snapshot_src = escape(Path(os.path.relpath(SNAPSHOT_PATH, OUTPUT_PATH.parent)).as_posix())

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>rag-eval-lab Benchmark Report</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #18212f;
      --muted: #607083;
      --line: #d9e1ea;
      --panel: #f7f9fc;
      --accent: #126c7a;
      --good: #14764d;
      --bad: #b33636;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background: #ffffff;
      font: 16px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    main {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 40px 24px 56px;
    }}
    header {{
      border-bottom: 1px solid var(--line);
      margin-bottom: 28px;
      padding-bottom: 20px;
    }}
    h1, h2 {{ line-height: 1.15; margin: 0; }}
    h1 {{ font-size: 34px; }}
    h2 {{ font-size: 22px; margin-top: 34px; }}
    p {{ color: var(--muted); margin: 10px 0 0; }}
    code {{
      background: #eef3f7;
      border-radius: 4px;
      padding: 1px 5px;
    }}
    .snapshot {{
      display: block;
      max-width: 100%;
      height: auto;
      margin: 22px 0 30px;
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 14px;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 10px 12px;
      text-align: right;
      vertical-align: top;
    }}
    th:first-child, td:first-child {{ text-align: left; }}
    th {{
      background: var(--panel);
      color: #334155;
      font-size: 13px;
      text-transform: uppercase;
    }}
    .delta-positive {{ color: var(--good); font-weight: 700; }}
    .delta-negative {{ color: var(--bad); font-weight: 700; }}
    .delta-neutral {{ color: var(--muted); }}
    .notes {{
      display: grid;
      gap: 12px;
      margin-top: 14px;
    }}
    .note {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px 16px;
      background: #ffffff;
    }}
    .note strong {{ color: var(--accent); }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>rag-eval-lab Benchmark Report</h1>
      <p>Generated from <code>results/retrieval-backend-comparison.json</code> and per-strategy run artifacts.</p>
    </header>

    <img class="snapshot" src="{snapshot_src}" alt="Benchmark snapshot for retrieval strategies">

    <section>
      <h2>Strategy Summary</h2>
      <table>
        <thead>
          <tr>
            <th>Strategy</th>
            <th>Hit Rate</th>
            <th>MRR</th>
            <th>nDCG</th>
            <th>Faithfulness</th>
          </tr>
        </thead>
        <tbody>
{rows}
        </tbody>
      </table>
    </section>

    <section>
      <h2>Deltas vs Keyword Baseline</h2>
      <table>
        <thead>
          <tr>
            <th>Strategy</th>
            <th>Hit Rate</th>
            <th>MRR</th>
            <th>nDCG</th>
            <th>Faithfulness</th>
          </tr>
        </thead>
        <tbody>
{delta_rows}
        </tbody>
      </table>
    </section>

    <section>
      <h2>Key Findings</h2>
      <div class="notes">
        <div class="note"><strong>Lexical baseline:</strong> <code>keyword</code> remains hard to beat on rank-sensitive retrieval metrics.</div>
        <div class="note"><strong>Dense retrieval:</strong> Embedding-only strategies improve faithfulness slightly but trail the lexical baseline on <code>MRR</code> and <code>nDCG</code>.</div>
        <div class="note"><strong>Reranking:</strong> <code>embedding_strong_rerank</code> restores rank quality and matches the lexical baseline on <code>MRR</code> and <code>nDCG</code>.</div>
      </div>
    </section>

    <section>
      <h2>Case Notes</h2>
      <div class="notes">
{case_notes}
      </div>
    </section>
  </main>
</body>
</html>
"""


def render_strategy_row(strategy: dict) -> str:
    cells = [
        f"            <td><code>{escape(strategy['retrieval_strategy'])}</code></td>",
        *[
            f"            <td>{strategy[key]:.4f}</td>"
            for key, _label in SUMMARY_METRICS
        ],
    ]
    return "          <tr>\n" + "\n".join(cells) + "\n          </tr>"


def render_delta_row(comparison: dict, strategy: dict) -> str:
    prefix = strategy["run_id"].replace("-retrieval", "").replace("-", "_")
    cells = [f"            <td><code>{escape(strategy['retrieval_strategy'])}</code></td>"]
    for key, _label in DELTA_METRICS:
        value = comparison["metric_deltas"][f"{prefix}_{key}_delta"]
        cells.append(f"            <td class=\"{delta_class(value)}\">{format_delta(value)}</td>")
    return "          <tr>\n" + "\n".join(cells) + "\n          </tr>"


def format_delta(value: float) -> str:
    if value > 0:
        return f"+{value:.4f}"
    return f"{value:.4f}"


def delta_class(value: float) -> str:
    if value > 0:
        return "delta-positive"
    if value < 0:
        return "delta-negative"
    return "delta-neutral"


def render_case_note(note: tuple[str, str]) -> str:
    question, detail = note
    return (
        "        <div class=\"note\">"
        f"<strong>{escape(question)}</strong><br>"
        f"{escape(detail)}"
        "</div>"
    )


def build_case_notes() -> list[tuple[str, str]]:
    comparison = json.loads(COMPARISON_PATH.read_text(encoding="utf-8"))
    by_strategy = {}
    for strategy in comparison["strategies"]:
        run_path = RESULTS_DIR / f"{strategy['run_id']}.json"
        by_strategy[strategy["retrieval_strategy"]] = json.loads(run_path.read_text(encoding="utf-8"))

    keyword_rows = index_cases(by_strategy["keyword"]["case_results"])
    embedding_rows = index_cases(by_strategy["embedding"]["case_results"])
    rerank_rows = index_cases(by_strategy["embedding_strong_rerank"]["case_results"])

    timeline_question = "What should take priority over writing the full incident timeline?"
    timeline_embedding = embedding_rows[timeline_question]
    timeline_rerank = rerank_rows[timeline_question]

    security_question = "How should someone disclose a security flaw before a fix is ready?"
    security_keyword = keyword_rows[security_question]
    security_rerank = rerank_rows[security_question]

    unanswerable_question = "Does the playbook require weekend pager coverage?"
    unanswerable_keyword = keyword_rows[unanswerable_question]
    unanswerable_rerank = rerank_rows[unanswerable_question]

    return [
        (
            timeline_question,
            "{} ranked {} first and pushed the correct chunk to rank 2; {} restored {} to rank 1.".format(
                "embedding",
                timeline_embedding["retrieved_chunk_ids"][0],
                "embedding_strong_rerank",
                timeline_rerank["retrieved_chunk_ids"][0],
            ),
        ),
        (
            security_question,
            "{} starts with {} followed by {}; {} pulls in a near-miss at rank 2, while {} restores {} as the stronger second result.".format(
                "keyword",
                security_keyword["retrieved_chunk_ids"][0],
                security_keyword["retrieved_chunk_ids"][1],
                "embedding",
                "embedding_strong_rerank",
                security_rerank["retrieved_chunk_ids"][1],
            ),
        ),
        (
            unanswerable_question,
            "Both keyword and embedding_strong_rerank remain unsupported here, with MRR values of {:.1f} and {:.1f}.".format(
                unanswerable_keyword["retrieval_mrr"],
                unanswerable_rerank["retrieval_mrr"],
            ),
        ),
    ]


def index_cases(rows: list[dict]) -> dict[str, dict]:
    return {row["question"]: row for row in rows}


if __name__ == "__main__":
    main()
