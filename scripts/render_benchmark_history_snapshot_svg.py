from pathlib import Path
from xml.sax.saxutils import escape
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.evaluation.history import DEFAULT_HISTORY_PATH
from app.evaluation.history import build_history_trends


OUTPUT_PATH = PROJECT_ROOT / "docs" / "benchmark-history-trends.svg"

COLORS = ["#60a5fa", "#22c55e", "#a78bfa", "#f59e0b", "#f97316", "#94a3b8"]


def main() -> None:
    trends = build_history_trends(DEFAULT_HISTORY_PATH)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(render_svg(trends), encoding="utf-8")
    print(
        f"Wrote {OUTPUT_PATH.relative_to(PROJECT_ROOT)} from "
        f"{DEFAULT_HISTORY_PATH}"
    )


def render_svg(trends: list[dict]) -> str:
    visible_trends = [trend for trend in trends if trend["points"]]
    width = 980
    height = 420
    left = 72
    right = 210
    top = 104
    bottom = 74
    plot_width = width - left - right
    plot_height = height - top - bottom

    if not visible_trends:
        return empty_svg(width, height)

    values = [
        point["average_retrieval_mrr"]
        for trend in visible_trends
        for point in trend["points"]
    ]
    min_value, max_value = metric_bounds(values)
    max_points = max(len(trend["points"]) for trend in visible_trends)

    grid = "\n".join(
        render_y_tick(value, left, top, plot_width, plot_height, min_value, max_value)
        for value in [min_value, (min_value + max_value) / 2, max_value]
    )
    series = "\n".join(
        render_series(
            trend,
            COLORS[index % len(COLORS)],
            max_points,
            left,
            top,
            plot_width,
            plot_height,
            min_value,
            max_value,
        )
        for index, trend in enumerate(visible_trends)
    )
    legend = "\n".join(
        render_legend_item(trend, COLORS[index % len(COLORS)], 770, 126 + index * 34)
        for index, trend in enumerate(visible_trends)
    )
    latest_run_count = max_points

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">rag-eval-lab benchmark history trends</title>
  <desc id="desc">MRR trend lines for retrieval strategies across local benchmark history runs.</desc>
  <style>
    .bg {{ fill: #0b1020; }}
    .panel {{ fill: #111827; }}
    .title {{ fill: #f8fafc; font: 700 24px 'Inter', 'Segoe UI', sans-serif; }}
    .subtitle {{ fill: #cbd5e1; font: 400 14px 'Inter', 'Segoe UI', sans-serif; }}
    .axis {{ stroke: #334155; stroke-width: 1; }}
    .grid {{ stroke: #1f2937; stroke-width: 1; }}
    .tick {{ fill: #94a3b8; font: 600 12px 'Inter', 'Segoe UI', sans-serif; }}
    .line {{ fill: none; stroke-width: 3; }}
    .point {{ stroke: #0b1020; stroke-width: 2; }}
    .legend {{ fill: #e2e8f0; font: 600 13px 'Inter', 'Segoe UI', sans-serif; }}
    .latest {{ fill: #cbd5e1; font: 400 12px 'Inter', 'Segoe UI', sans-serif; }}
  </style>

  <rect class="bg" x="0" y="0" width="{width}" height="{height}" rx="14"/>
  <text class="title" x="30" y="42">rag-eval-lab - benchmark history trends</text>
  <text class="subtitle" x="30" y="66">MRR by retrieval strategy across {latest_run_count} local comparison runs</text>

  <rect class="panel" x="24" y="88" width="932" height="300" rx="10"/>
{grid}
  <line class="axis" x1="{left}" y1="{height - bottom}" x2="{width - right}" y2="{height - bottom}"/>
  <text class="tick" x="{left}" y="{height - 38}">Oldest</text>
  <text class="tick" x="{width - right}" y="{height - 38}" text-anchor="end">Latest</text>
{series}
{legend}
</svg>
"""


def empty_svg(width: int, height: int) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">rag-eval-lab benchmark history trends</title>
  <desc id="desc">No local benchmark history runs were available.</desc>
  <rect fill="#0b1020" x="0" y="0" width="{width}" height="{height}" rx="14"/>
  <text fill="#f8fafc" x="30" y="46" font-size="24" font-weight="700">rag-eval-lab · benchmark history trends</text>
  <text fill="#cbd5e1" x="30" y="84" font-size="15">Run scripts/compare_benchmarks.py twice to populate local history.</text>
</svg>
"""


def metric_bounds(values: list[float]) -> tuple[float, float]:
    min_value = min(values)
    max_value = max(values)
    if min_value == max_value:
        return max(0.0, min_value - 0.05), min(1.0, max_value + 0.05)
    padding = (max_value - min_value) * 0.18
    return max(0.0, min_value - padding), min(1.0, max_value + padding)


def render_y_tick(
    value: float,
    left: int,
    top: int,
    plot_width: int,
    plot_height: int,
    min_value: float,
    max_value: float,
) -> str:
    y = y_coordinate(value, top, plot_height, min_value, max_value)
    return f"""  <line class="grid" x1="{left}" y1="{y:.2f}" x2="{left + plot_width}" y2="{y:.2f}"/>
  <text class="tick" x="{left - 14}" y="{y + 4:.2f}" text-anchor="end">{value:.3f}</text>"""


def render_series(
    trend: dict,
    color: str,
    max_points: int,
    left: int,
    top: int,
    plot_width: int,
    plot_height: int,
    min_value: float,
    max_value: float,
) -> str:
    points = [
        (
            x_coordinate(index, len(trend["points"]), max_points, left, plot_width),
            y_coordinate(
                point["average_retrieval_mrr"],
                top,
                plot_height,
                min_value,
                max_value,
            ),
        )
        for index, point in enumerate(trend["points"])
    ]
    path = " ".join(
        f"{'M' if index == 0 else 'L'} {x:.2f} {y:.2f}"
        for index, (x, y) in enumerate(points)
    )
    circles = "\n".join(
        f'  <circle class="point" cx="{x:.2f}" cy="{y:.2f}" r="5" fill="{color}"/>'
        for x, y in points
    )
    return f"""  <path class="line" d="{path}" stroke="{color}"/>
{circles}"""


def render_legend_item(trend: dict, color: str, x: int, y: int) -> str:
    latest = trend["latest"]
    label = escape(trend["retrieval_strategy"])
    latest_mrr = latest["average_retrieval_mrr"]
    delta = trend["deltas"].get("average_retrieval_mrr")
    delta_label = "no previous run" if delta is None else format_delta(delta)
    return f"""  <circle cx="{x}" cy="{y - 5}" r="5" fill="{color}"/>
  <text class="legend" x="{x + 14}" y="{y}">{label}</text>
  <text class="latest" x="{x + 14}" y="{y + 16}">latest MRR {latest_mrr:.4f} - {delta_label}</text>"""


def x_coordinate(
    index: int,
    point_count: int,
    max_points: int,
    left: int,
    plot_width: int,
) -> float:
    denominator = max(max_points - 1, 1)
    offset = max_points - point_count
    return left + ((index + offset) / denominator) * plot_width


def y_coordinate(
    value: float,
    top: int,
    plot_height: int,
    min_value: float,
    max_value: float,
) -> float:
    ratio = (value - min_value) / (max_value - min_value)
    return top + (1 - ratio) * plot_height


def format_delta(value: float) -> str:
    if value > 0:
        return f"+{value:.4f}"
    return f"{value:.4f}"


if __name__ == "__main__":
    main()
