from pathlib import Path
import json
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.evaluation.history import DEFAULT_HISTORY_PATH
from app.evaluation.history import build_history_trends
from app.evaluation.history import list_history_runs
from app.evaluation.history import load_history_run


def main() -> None:
    rows = list_history_runs()
    if not rows:
        print(f"No benchmark history runs found in {DEFAULT_HISTORY_PATH}")
        return

    latest = load_history_run(rows[0]["id"])
    trends = build_history_trends()
    print(
        json.dumps(
            {
                "history_path": str(DEFAULT_HISTORY_PATH),
                "runs": rows,
                "trends": trends,
                "latest": {
                    "id": latest["id"],
                    "comparison_id": latest["comparison_id"],
                    "created_at": latest["created_at"],
                    "strategies": [
                        {
                            "run_id": strategy["run_id"],
                            "retrieval_strategy": strategy["retrieval_strategy"],
                            "average_retrieval_mrr": strategy["average_retrieval_mrr"],
                            "average_retrieval_ndcg": strategy["average_retrieval_ndcg"],
                            "average_answer_faithfulness": strategy[
                                "average_answer_faithfulness"
                            ],
                        }
                        for strategy in latest["strategies"]
                    ],
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
