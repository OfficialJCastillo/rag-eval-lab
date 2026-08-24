from pathlib import Path
from xml.sax.saxutils import escape
import json
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


RESULTS_PATH = PROJECT_ROOT / "results" / "retrieval-backend-comparison.json"
OUTPUT_PATH = PROJECT_ROOT / "docs" / "benchmark-snapshot.svg"

METRICS = (
    ("Hit rate", "average_retrieval_hit_rate", "hit"),
    ("MRR", "average_retrieval_mrr", "mrr"),
    ("nDCG", "average_retrieval_ndcg", "ndcg"),
    ("Faithfulness", "average_answer_faithfulness", "faith"),
)


def _bar_width(value: float, width: int = 92) -> int:
    return int(round(max(0.0, min(1.0, value)) * width))


def _display_label(label: str) -> str:
    return escape(label.replace("_", " "))


def _row(index: int, strategy: dict, best_values: dict[str, float]) -> str:
    row_y = 124 + index * 58
    row_class = "row" if index % 2 == 0 else "row row-alt"
    label = _display_label(strategy["retrieval_strategy"])
    cells = []

    for metric_index, (_, key, color_class) in enumerate(METRICS):
        value = strategy[key]
        cell_x = 286 + metric_index * 164
        value_class = "value value-best" if value == best_values[key] else "value"
        cells.append(
            f'    <rect class="track" x="{cell_x}" y="{row_y + 23}" width="92" height="10" rx="5"/>'
        )
        cells.append(
            f'    <rect class="bar {color_class}" x="{cell_x}" y="{row_y + 23}" '
            f'width="{_bar_width(value)}" height="10" rx="5"/>'
        )
        cells.append(
            f'    <text class="{value_class}" x="{cell_x + 104}" y="{row_y + 33}">{value:.4f}</text>'
        )

    return "\n".join(
        [
            f'  <rect class="{row_class}" x="20" y="{row_y}" width="940" height="50" rx="10"/>',
            f'  <text class="label" x="36" y="{row_y + 31}">{label}</text>',
            *cells,
        ]
    )


def render_svg(comparison: dict) -> str:
    strategies = comparison["strategies"]
    best_values = {
        key: max(strategy[key] for strategy in strategies)
        for _, key, _ in METRICS
    }
    rows = [
        _row(index, strategy, best_values)
        for index, strategy in enumerate(strategies)
    ]
    height = 124 + len(strategies) * 58 + 20
    headers = "\n".join(
        f'  <text class="header" x="{286 + index * 164}" y="108">{label}</text>'
        for index, (label, _, _) in enumerate(METRICS)
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="980" height="{height}" viewBox="0 0 980 {height}" role="img" aria-labelledby="title desc">
  <title id="title">rag-eval-lab retrieval benchmark scorecard</title>
  <desc id="desc">Scorecard comparing hit rate, MRR, nDCG, and faithfulness across retrieval strategies. Higher values are better.</desc>
  <style>
    .bg {{ fill: #0b1020; }}
    .title {{ fill: #f8fafc; font: 700 25px 'Inter', 'Segoe UI', sans-serif; }}
    .subtitle {{ fill: #aebbd0; font: 500 14px 'Inter', 'Segoe UI', sans-serif; }}
    .header {{ fill: #dbe5f3; font: 700 13px 'Inter', 'Segoe UI', sans-serif; }}
    .label {{ fill: #e2e8f0; font: 600 14px 'Inter', 'Segoe UI', sans-serif; }}
    .value {{ fill: #dbe5f3; font: 650 12px 'Inter', 'Segoe UI', sans-serif; }}
    .value-best {{ fill: #6ee7b7; }}
    .row {{ fill: #121a2a; }}
    .row-alt {{ fill: #0f1726; }}
    .track {{ fill: #263247; }}
    .bar {{ opacity: 0.95; }}
    .hit {{ fill: #34d399; }}
    .mrr {{ fill: #60a5fa; }}
    .ndcg {{ fill: #a78bfa; }}
    .faith {{ fill: #fbbf24; }}
  </style>

  <rect class="bg" x="0" y="0" width="980" height="{height}" rx="16"/>
  <text class="title" x="30" y="43">Retrieval benchmark · strategy scorecard</text>
  <text class="subtitle" x="30" y="68">Higher is better · best values highlighted · deterministic benchmark artifact</text>

  <text class="header" x="36" y="108">Strategy</text>
{headers}
{chr(10).join(rows)}
</svg>
"""


def main() -> None:
    comparison = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(render_svg(comparison), encoding="utf-8")
    print(
        f"Wrote {OUTPUT_PATH.relative_to(PROJECT_ROOT)} from "
        f"{RESULTS_PATH.relative_to(PROJECT_ROOT)}"
    )


if __name__ == "__main__":
    main()
