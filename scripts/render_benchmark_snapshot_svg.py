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


def _row(y: int, row_class: str, label: str, hit: float, mrr: float, ndcg: float, faith: float) -> str:
    return f"""
  <rect class=\"{row_class}\" x=\"24\" y=\"{y}\" width=\"1152\" height=\"50\" rx=\"10\"/>
  <text class=\"label\" x=\"36\" y=\"{y + 32}\">{label}</text>
  <rect class=\"track\" x=\"290\" y=\"{y + 15}\" width=\"120\" height=\"14\" rx=\"7\"/><rect class=\"hit\" x=\"290\" y=\"{y + 15}\" width=\"{_bar_width(hit)}\" height=\"14\" rx=\"7\"/><text class=\"value\" x=\"418\" y=\"{y + 28}\">{hit:.4f}</text>
  <rect class=\"track\" x=\"515\" y=\"{y + 15}\" width=\"120\" height=\"14\" rx=\"7\"/><rect class=\"mrr\" x=\"515\" y=\"{y + 15}\" width=\"{_bar_width(mrr)}\" height=\"14\" rx=\"7\"/><text class=\"value\" x=\"643\" y=\"{y + 28}\">{mrr:.4f}</text>
  <rect class=\"track\" x=\"740\" y=\"{y + 15}\" width=\"120\" height=\"14\" rx=\"7\"/><rect class=\"ndcg\" x=\"740\" y=\"{y + 15}\" width=\"{_bar_width(ndcg)}\" height=\"14\" rx=\"7\"/><text class=\"value\" x=\"868\" y=\"{y + 28}\">{ndcg:.4f}</text>
  <rect class=\"track\" x=\"965\" y=\"{y + 15}\" width=\"120\" height=\"14\" rx=\"7\"/><rect class=\"faith\" x=\"965\" y=\"{y + 15}\" width=\"{_bar_width(faith)}\" height=\"14\" rx=\"7\"/><text class=\"value\" x=\"1093\" y=\"{y + 28}\">{faith:.4f}</text>
""".rstrip()


def main() -> None:
    comparison = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    strategies = comparison["strategies"]

    rows = []
    row_y = 148
    for i, strategy in enumerate(strategies):
        row_class = "rowA" if i % 2 == 0 else "rowB"
        rows.append(
            _row(
                y=row_y,
                row_class=row_class,
                label=strategy["retrieval_strategy"],
                hit=strategy["average_retrieval_hit_rate"],
                mrr=strategy["average_retrieval_mrr"],
                ndcg=strategy["average_retrieval_ndcg"],
                faith=strategy["average_answer_faithfulness"],
            )
        )
        row_y += 56

    svg = f"""<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1200\" height=\"440\" viewBox=\"0 0 1200 440\" role=\"img\" aria-labelledby=\"title desc\">
  <title id=\"title\">rag-eval-lab benchmark snapshot</title>
  <desc id=\"desc\">Comparison of hit rate, MRR, nDCG, and faithfulness for retrieval strategies.</desc>
  <style>
    .bg {{ fill: #020b26; }}
    .panel {{ fill: #0b1737; }}
    .rowA {{ fill: #0e1d41; }}
    .rowB {{ fill: #0b1938; }}
    .title {{ fill: #f8fafc; font: 700 44px 'Inter', 'Segoe UI', sans-serif; }}
    .subtitle {{ fill: #cbd5e1; font: 400 28px 'Inter', 'Segoe UI', sans-serif; }}
    .header {{ fill: #e2e8f0; font: 700 24px 'Inter', 'Segoe UI', sans-serif; }}
    .label {{ fill: #a5b4fc; font: 700 24px 'Inter', 'Segoe UI', sans-serif; }}
    .value {{ fill: #f8fafc; font: 700 22px 'Inter', 'Segoe UI', sans-serif; }}
    .track {{ fill: #1e293b; }}
    .hit {{ fill: #22c55e; }}
    .mrr {{ fill: #60a5fa; }}
    .ndcg {{ fill: #a78bfa; }}
    .faith {{ fill: #f59e0b; }}
  </style>

  <rect class=\"bg\" x=\"0\" y=\"0\" width=\"1200\" height=\"440\" rx=\"16\"/>
  <rect class=\"panel\" x=\"18\" y=\"18\" width=\"1164\" height=\"404\" rx=\"14\"/>

  <text class=\"title\" x=\"36\" y=\"62\">rag-eval-lab · retrieval benchmark snapshot</text>
  <text class=\"subtitle\" x=\"36\" y=\"95\">Source: results/retrieval-backend-comparison.json</text>

  <text class=\"header\" x=\"36\" y=\"133\">Strategy</text>
  <text class=\"header\" x=\"290\" y=\"133\">Hit Rate</text>
  <text class=\"header\" x=\"515\" y=\"133\">MRR</text>
  <text class=\"header\" x=\"740\" y=\"133\">nDCG</text>
  <text class=\"header\" x=\"965\" y=\"133\">Faithfulness</text>

{chr(10).join(rows)}
</svg>
"""

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(PROJECT_ROOT)} from {RESULTS_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
