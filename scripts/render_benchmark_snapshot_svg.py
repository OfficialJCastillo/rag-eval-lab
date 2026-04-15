from pathlib import Path
import json
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


RESULTS_PATH = PROJECT_ROOT / "results" / "retrieval-backend-comparison.json"
OUTPUT_PATH = PROJECT_ROOT / "docs" / "benchmark-snapshot.svg"


def _bar_width(value: float) -> int:
    return int(round(value * 120))


def _value_x(index: int) -> tuple[int, int, int, int]:
    if index == 0:
        return (357, 507, 657, 797)
    if index == 1:
        return (357, 497, 650, 797)
    if index in (2, 3):
        return (357, 502, 653, 799)
    return (357, 507, 657, 798)


def _row(index: int, strategy: dict) -> str:
    hit = strategy["average_retrieval_hit_rate"]
    mrr = strategy["average_retrieval_mrr"]
    ndcg = strategy["average_retrieval_ndcg"]
    faith = strategy["average_answer_faithfulness"]
    label = strategy["retrieval_strategy"]
    y_offset = index * 56
    row_class = "row" if index % 2 == 0 else "rowAlt"
    hit_x, mrr_x, ndcg_x, faith_x = _value_x(index)

    return f"""
  <g transform=\"translate(0,{y_offset})\">
    <rect class=\"{row_class}\" x=\"20\" y=\"108\" width=\"940\" height=\"52\" rx=\"8\"/>
    <text class=\"label\" x=\"30\" y=\"138\">{label}</text>
    <rect class=\"barHit\" x=\"240\" y=\"124\" width=\"{_bar_width(hit)}\" height=\"12\" rx=\"6\"/><text class=\"value\" x=\"{hit_x}\" y=\"135\">{hit:.4f}</text>
    <rect class=\"barMrr\" x=\"390\" y=\"124\" width=\"{_bar_width(mrr)}\" height=\"12\" rx=\"6\"/><text class=\"value\" x=\"{mrr_x}\" y=\"135\">{mrr:.4f}</text>
    <rect class=\"barNdcg\" x=\"540\" y=\"124\" width=\"{_bar_width(ndcg)}\" height=\"12\" rx=\"6\"/><text class=\"value\" x=\"{ndcg_x}\" y=\"135\">{ndcg:.4f}</text>
    <rect class=\"barFaith\" x=\"690\" y=\"124\" width=\"{_bar_width(faith)}\" height=\"12\" rx=\"6\"/><text class=\"value\" x=\"{faith_x}\" y=\"135\">{faith:.4f}</text>
  </g>
""".rstrip()


def main() -> None:
    comparison = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    strategies = comparison["strategies"]
    rows = [_row(index, strategy) for index, strategy in enumerate(strategies)]

    svg = f"""<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"980\" height=\"420\" viewBox=\"0 0 980 420\" role=\"img\" aria-labelledby=\"title desc\">
  <title id=\"title\">rag-eval-lab benchmark snapshot</title>
  <desc id=\"desc\">Comparison of hit rate, MRR, nDCG, and faithfulness for retrieval strategies.</desc>
  <style>
    .bg {{ fill: #0b1020; }}
    .title {{ fill: #f8fafc; font: 700 24px 'Inter', 'Segoe UI', sans-serif; }}
    .subtitle {{ fill: #cbd5e1; font: 400 14px 'Inter', 'Segoe UI', sans-serif; }}
    .header {{ fill: #e2e8f0; font: 700 13px 'Inter', 'Segoe UI', sans-serif; }}
    .label {{ fill: #94a3b8; font: 600 12px 'Inter', 'Segoe UI', sans-serif; }}
    .value {{ fill: #f8fafc; font: 600 12px 'Inter', 'Segoe UI', sans-serif; }}
    .row {{ fill: #111827; }}
    .rowAlt {{ fill: #0f172a; }}
    .barHit {{ fill: #22c55e; }}
    .barMrr {{ fill: #60a5fa; }}
    .barNdcg {{ fill: #a78bfa; }}
    .barFaith {{ fill: #f59e0b; }}
  </style>

  <rect class=\"bg\" x=\"0\" y=\"0\" width=\"980\" height=\"420\" rx=\"14\"/>
  <text class=\"title\" x=\"30\" y=\"42\">rag-eval-lab · retrieval benchmark snapshot</text>
  <text class=\"subtitle\" x=\"30\" y=\"64\">Source: results/retrieval-backend-comparison.json (April 2026)</text>

  <text class=\"header\" x=\"30\" y=\"95\">Strategy</text>
  <text class=\"header\" x=\"240\" y=\"95\">Hit Rate</text>
  <text class=\"header\" x=\"390\" y=\"95\">MRR</text>
  <text class=\"header\" x=\"540\" y=\"95\">nDCG</text>
  <text class=\"header\" x=\"690\" y=\"95\">Faithfulness</text>

{chr(10).join(rows)}
</svg>
"""

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(PROJECT_ROOT)} from {RESULTS_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
