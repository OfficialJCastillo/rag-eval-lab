from pathlib import Path
from xml.sax.saxutils import escape
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.evaluation.history import DEFAULT_HISTORY_PATH
from app.evaluation.history import build_history_trends


OUTPUT_PATH = PROJECT_ROOT / "docs" / "benchmark-history-trends.svg"

COLORS = ["#60a5fa", "#34d399", "#a78bfa", "#fbbf24", "#fb923c", "#94a3b8"]


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
    height = 124 + len(visible_trends) * 58 + 22

    if not visible_trends:
        return empty_svg(width, 260)

    values = [
        point["average_retrieval_mrr"]
        for trend in visible_trends
        for point in trend["points"]
    ]
    min_value, max_value = metric_bounds(values)
    max_points = max(len(trend["points"]) for trend in visible_trends)
    rows = "\n".join(
        render_trend_row(
            trend,
            COLORS[index % len(COLORS)],
            index,
            max_points,
            min_value,
            max_value,
        )
        for index, trend in enumerate(visible_trends)
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">rag-eval-lab benchmark history trends</title>
  <desc id="desc">Separate MRR sparklines and latest-run changes for each retrieval strategy.</desc>
  <style>
    .bg {{ fill: #0b1020; }}
    .title {{ fill: #f8fafc; font: 700 25px 'Inter', 'Segoe UI', sans-serif; }}
    .subtitle {{ fill: #aebbd0; font: 500 14px 'Inter', 'Segoe UI', sans-serif; }}
    .header {{ fill: #dbe5f3; font: 700 13px 'Inter', 'Segoe UI', sans-serif; }}
    .row {{ fill: #121a2a; }}
    .row-alt {{ fill: #0f1726; }}
    .label {{ fill: #e2e8f0; font: 600 14px 'Inter', 'Segoe UI', sans-serif; }}
    .track {{ stroke: #34425a; stroke-width: 2; }}
    .line {{ fill: none; stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; }}
    .point {{ stroke: #121a2a; stroke-width: 2; }}
    .value {{ fill: #f8fafc; font: 650 13px 'Inter', 'Segoe UI', sans-serif; }}
    .delta {{ fill: #cbd5e1; font: 600 13px 'Inter', 'Segoe UI', sans-serif; }}
    .status {{ fill: #0b1020; font: 700 11px 'Inter', 'Segoe UI', sans-serif; text-anchor: middle; }}
  </style>

  <rect class="bg" x="0" y="0" width="{width}" height="{height}" rx="16"/>
  <text class="title" x="30" y="43">Benchmark history · MRR stability</text>
  <text class="subtitle" x="30" y="68">{max_points} local comparison runs · one sparkline per strategy · shared 0–1 scale</text>

  <text class="header" x="36" y="108">Strategy</text>
  <text class="header" x="260" y="108">Oldest → latest</text>
  <text class="header" x="636" y="108">Latest MRR</text>
  <text class="header" x="752" y="108">Change</text>
  <text class="header" x="875" y="108">Status</text>
{rows}
</svg>
"""


def render_trend_row(
    trend: dict,
    color: str,
    index: int,
    max_points: int,
    min_value: float,
    max_value: float,
) -> str:
    row_y = 124 + index * 58
    row_class = "row" if index % 2 == 0 else "row row-alt"
    raw_label = escape(trend["retrieval_strategy"])
    display_label = escape(trend["retrieval_strategy"].replace("_", " "))
    spark_left = 260
    spark_width = 330
    spark_top = row_y + 9
    spark_height = 32
    points = [
        (
            x_coordinate(
                point_index,
                len(trend["points"]),
                max_points,
                spark_left,
                spark_width,
            ),
            y_coordinate(
                point["average_retrieval_mrr"],
                spark_top,
                spark_height,
                min_value,
                max_value,
            ),
        )
        for point_index, point in enumerate(trend["points"])
    ]
    path = " ".join(
        f"{'M' if point_index == 0 else 'L'} {x:.2f} {y:.2f}"
        for point_index, (x, y) in enumerate(points)
    )
    circles = "\n".join(
        f'    <circle class="point" cx="{x:.2f}" cy="{y:.2f}" r="4.5" fill="{color}"/>'
        for x, y in points
    )
    latest_mrr = trend["latest"]["average_retrieval_mrr"]
    delta = trend["deltas"].get("average_retrieval_mrr")
    delta_label = "—" if delta is None else format_delta(delta)
    status_label, status_color = delta_status(delta)

    return f"""  <g data-strategy="{raw_label}">
    <rect class="{row_class}" x="20" y="{row_y}" width="940" height="50" rx="10"/>
    <text class="label" x="36" y="{row_y + 31}">{display_label}</text>
    <line class="track" x1="{spark_left}" y1="{row_y + 25}" x2="{spark_left + spark_width}" y2="{row_y + 25}"/>
    <path class="line" d="{path}" stroke="{color}"/>
{circles}
    <text class="value" x="636" y="{row_y + 31}">{latest_mrr:.4f}</text>
    <text class="delta" x="752" y="{row_y + 31}">{delta_label}</text>
    <rect x="856" y="{row_y + 15}" width="88" height="22" rx="11" fill="{status_color}"/>
    <text class="status" x="900" y="{row_y + 30}">{status_label}</text>
  </g>"""


def empty_svg(width: int, height: int) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">rag-eval-lab benchmark history trends</title>
  <desc id="desc">No local benchmark history runs were available.</desc>
  <rect fill="#0b1020" x="0" y="0" width="{width}" height="{height}" rx="16"/>
  <text fill="#f8fafc" x="30" y="46" font-size="25" font-weight="700">Benchmark history · MRR stability</text>
  <text fill="#aebbd0" x="30" y="84" font-size="15">Run scripts/compare_benchmarks.py twice to populate local history.</text>
</svg>
"""


def metric_bounds(_values: list[float]) -> tuple[float, float]:
    return 0.0, 1.0


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


def delta_status(value: float | None) -> tuple[str, str]:
    if value is None:
        return "new", "#94a3b8"
    if abs(value) < 0.00005:
        return "stable", "#6ee7b7"
    if value > 0:
        return "improved", "#93c5fd"
    return "declined", "#fbbf24"


if __name__ == "__main__":
    main()
