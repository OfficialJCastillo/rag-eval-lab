from html import escape
from pathlib import Path
import json
import os
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.evaluation.history import DEFAULT_HISTORY_PATH
from app.evaluation.history import build_history_trends


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
    history_path = Path(os.environ.get("RAG_EVAL_HISTORY_PATH", DEFAULT_HISTORY_PATH))
    history_trends = build_history_trends(history_path) if history_path.exists() else []
    OUTPUT_PATH.write_text(render_html(comparison, history_trends), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")


def render_html(comparison: dict, history_trends: list[dict] | None = None) -> str:
    strategies = comparison["strategies"]
    rows = "\n".join(render_strategy_row(strategy) for strategy in strategies)
    delta_rows = "\n".join(render_delta_row(comparison, strategy) for strategy in strategies[1:])
    case_notes = "\n".join(render_case_note(note) for note in build_case_notes())
    snapshot_src = escape(Path(os.path.relpath(SNAPSHOT_PATH, OUTPUT_PATH.parent)).as_posix())
    history_section = render_history_section(history_trends or [])

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
    .trend-chart {{
      margin-top: 16px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #ffffff;
      overflow: hidden;
    }}
    .trend-chart svg {{
      display: block;
      width: 100%;
      height: auto;
    }}
    .trend-line {{ fill: none; stroke-width: 2.5; }}
    .trend-point {{ stroke: #ffffff; stroke-width: 1.5; }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>rag-eval-lab Benchmark Report</h1>
      <p>Generated from <code>results/retrieval-backend-comparison.json</code> and per-strategy run artifacts.</p>
    </header>

    <img class="snapshot" src="{snapshot_src}" alt="Benchmark snapshot for retrieval strategies">

{history_section}

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


def render_history_section(history_trends: list[dict]) -> str:
    trends = [trend for trend in history_trends if trend["points"]]
    if not trends:
        return ""

    chart = render_mrr_trend_svg(trends)
    rows = "\n".join(render_history_row(trend) for trend in trends)
    return f"""    <section>
      <h2>History Trends</h2>
      <p>Recent local benchmark history from <code>results/benchmark-history.sqlite3</code>.</p>
      <div class="trend-chart">
{chart}
      </div>
      <table>
        <thead>
          <tr>
            <th>Strategy</th>
            <th>Runs</th>
            <th>Latest MRR</th>
            <th>MRR Change</th>
            <th>Latest nDCG</th>
            <th>Faithfulness Change</th>
          </tr>
        </thead>
        <tbody>
{rows}
        </tbody>
      </table>
    </section>
"""


def render_mrr_trend_svg(trends: list[dict]) -> str:
    width = 960
    height = 260
    left = 64
    right = 24
    top = 28
    bottom = 46
    plot_width = width - left - right
    plot_height = height - top - bottom
    values = [
        point["average_retrieval_mrr"]
        for trend in trends
        for point in trend["points"]
    ]
    min_value = min(values)
    max_value = max(values)
    if min_value == max_value:
        min_value = max(0.0, min_value - 0.05)
        max_value = min(1.0, max_value + 0.05)
    else:
        padding = (max_value - min_value) * 0.15
        min_value = max(0.0, min_value - padding)
        max_value = min(1.0, max_value + padding)

    max_points = max(len(trend["points"]) for trend in trends)
    series = "\n".join(
        render_trend_series(
            trend,
            color=trend_color(index),
            max_points=max_points,
            bounds=(left, top, plot_width, plot_height, min_value, max_value),
        )
        for index, trend in enumerate(trends)
    )
    y_ticks = "\n".join(
        render_y_tick(value, left, top, plot_width, plot_height, min_value, max_value)
        for value in [min_value, (min_value + max_value) / 2, max_value]
    )
    return f"""        <svg viewBox="0 0 {width} {height}" role="img" aria-label="MRR trend by retrieval strategy">
          <rect width="{width}" height="{height}" fill="#ffffff"></rect>
{y_ticks}
          <line x1="{left}" y1="{height - bottom}" x2="{width - right}" y2="{height - bottom}" stroke="#d9e1ea"></line>
          <text x="{left}" y="{height - 16}" fill="#607083" font-size="13">Oldest</text>
          <text x="{width - right}" y="{height - 16}" fill="#607083" font-size="13" text-anchor="end">Latest</text>
{series}
        </svg>"""


def render_trend_series(
    trend: dict,
    color: str,
    max_points: int,
    bounds: tuple[float, float, float, float, float, float],
) -> str:
    left, top, plot_width, plot_height, min_value, max_value = bounds
    coordinates = [
        trend_coordinate(
            index,
            point["average_retrieval_mrr"],
            len(trend["points"]),
            max_points,
            left,
            top,
            plot_width,
            plot_height,
            min_value,
            max_value,
        )
        for index, point in enumerate(trend["points"])
    ]
    if len(coordinates) == 1:
        x, y = coordinates[0]
        path = f"M {x:.2f} {y:.2f}"
    else:
        path = " ".join(
            f"{'M' if index == 0 else 'L'} {x:.2f} {y:.2f}"
            for index, (x, y) in enumerate(coordinates)
        )
    points = "\n".join(
        f'          <circle class="trend-point" cx="{x:.2f}" cy="{y:.2f}" r="4" fill="{color}"></circle>'
        for x, y in coordinates
    )
    label_x, label_y = coordinates[-1]
    label = escape(trend["retrieval_strategy"])
    return f"""          <path class="trend-line" d="{path}" stroke="{color}"></path>
{points}
          <text x="{label_x + 8:.2f}" y="{label_y - 6:.2f}" fill="{color}" font-size="13">{label}</text>"""


def trend_coordinate(
    index: int,
    value: float,
    point_count: int,
    max_points: int,
    left: float,
    top: float,
    plot_width: float,
    plot_height: float,
    min_value: float,
    max_value: float,
) -> tuple[float, float]:
    x_denominator = max(max_points - 1, 1)
    x_offset = max_points - point_count
    x = left + ((index + x_offset) / x_denominator) * plot_width
    y_ratio = (value - min_value) / (max_value - min_value)
    y = top + (1 - y_ratio) * plot_height
    return x, y


def render_y_tick(
    value: float,
    left: float,
    top: float,
    plot_width: float,
    plot_height: float,
    min_value: float,
    max_value: float,
) -> str:
    y_ratio = (value - min_value) / (max_value - min_value)
    y = top + (1 - y_ratio) * plot_height
    return f"""          <line x1="{left}" y1="{y:.2f}" x2="{left + plot_width}" y2="{y:.2f}" stroke="#eef3f7"></line>
          <text x="{left - 10}" y="{y + 4:.2f}" fill="#607083" font-size="12" text-anchor="end">{value:.3f}</text>"""


def render_history_row(trend: dict) -> str:
    latest = trend["latest"]
    deltas = trend["deltas"]
    mrr_delta = deltas.get("average_retrieval_mrr")
    faithfulness_delta = deltas.get("average_answer_faithfulness")
    cells = [
        f"            <td><code>{escape(trend['retrieval_strategy'])}</code></td>",
        f"            <td>{len(trend['points'])}</td>",
        f"            <td>{latest['average_retrieval_mrr']:.4f}</td>",
        f"            <td class=\"{delta_class(mrr_delta or 0.0)}\">{format_optional_delta(mrr_delta)}</td>",
        f"            <td>{latest['average_retrieval_ndcg']:.4f}</td>",
        f"            <td class=\"{delta_class(faithfulness_delta or 0.0)}\">{format_optional_delta(faithfulness_delta)}</td>",
    ]
    return "          <tr>\n" + "\n".join(cells) + "\n          </tr>"


def format_optional_delta(value: float | None) -> str:
    if value is None:
        return "n/a"
    return format_delta(value)


def trend_color(index: int) -> str:
    colors = ["#126c7a", "#7a4e12", "#6f4dbf", "#14764d", "#b33636", "#334155"]
    return colors[index % len(colors)]


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
