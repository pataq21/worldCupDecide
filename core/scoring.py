import json
from pathlib import Path
from typing import List

import pandas as pd

from core.data import get_user_predictions, load_predictions, load_results, load_users

_SCHEDULE_PATH = Path(__file__).parent.parent / "data" / "schedule.json"


def _get_outcome(goals1: int, goals2: int) -> str:
    """Return '1' (home win), 'X' (draw), or '2' (away win)."""
    if goals1 > goals2:
        return "1"
    elif goals1 < goals2:
        return "2"
    return "X"


def calculate_user_stats(user: str) -> dict:
    """Return points, exact score count, and correct sign (1/X/2) count for a user."""
    predictions = get_user_predictions(user)
    results = load_results()
    points = 0
    exact = 0
    sign = 0

    for match_id, result in results.items():
        if match_id == "_meta":
            continue
        pred = predictions.get(match_id)
        if not pred or not isinstance(pred, dict):
            continue

        pred_g1 = pred.get("goals1")
        pred_g2 = pred.get("goals2")
        real_g1 = result.get("goals1")
        real_g2 = result.get("goals2")

        if pred_g1 is None or pred_g2 is None or real_g1 is None or real_g2 is None:
            continue

        if pred_g1 == real_g1 and pred_g2 == real_g2:
            points += 3
            exact += 1
            sign += 1
        elif _get_outcome(pred_g1, pred_g2) == _get_outcome(real_g1, real_g2):
            points += 1
            sign += 1

    return {"points": points, "exact": exact, "sign": sign}


def calculate_user_points(user: str) -> int:
    return calculate_user_stats(user)["points"]


def get_ranking() -> List[tuple]:
    """Get user ranking sorted by points (computed dynamically)."""
    users = load_users()
    ranking = [(name, calculate_user_points(name)) for name in users]
    return sorted(ranking, key=lambda x: x[1], reverse=True)


def get_ranking_detailed() -> List[tuple]:
    """Get user ranking with points, exact scores, and correct signs."""
    users = load_users()
    rows = [(name, calculate_user_stats(name)) for name in users]
    return sorted(rows, key=lambda x: x[1]["points"], reverse=True)


def get_points_evolution() -> pd.DataFrame | None:
    """Cumulative points per user per match day. Returns DataFrame indexed 0..N or None."""
    schedule = json.loads(_SCHEDULE_PATH.read_text(encoding="utf-8"))
    match_to_day = {mid: s["match_day"] for mid, s in schedule.items() if s.get("match_day")}

    predictions = load_predictions()
    results = load_results()
    users = load_users()
    real_users = [u for u in users if not u.startswith("~")]

    if not real_users:
        return None

    # Accumulate incremental points per user per day
    day_pts: dict[str, dict[int, int]] = {u: {} for u in real_users}
    for mid, result in results.items():
        if mid == "_meta":
            continue
        day = match_to_day.get(mid)
        if not day:
            continue
        rg1, rg2 = result.get("goals1"), result.get("goals2")
        if rg1 is None or rg2 is None:
            continue
        for user in real_users:
            pred = predictions.get(user, {}).get(mid)
            if not pred or not isinstance(pred, dict):
                continue
            pg1, pg2 = pred.get("goals1"), pred.get("goals2")
            if pg1 is None or pg2 is None:
                continue
            if pg1 == rg1 and pg2 == rg2:
                pts = 3
            elif _get_outcome(pg1, pg2) == _get_outcome(rg1, rg2):
                pts = 1
            else:
                continue
            day_pts[user][day] = day_pts[user].get(day, 0) + pts

    played_days = sorted({match_to_day[mid] for mid in results if mid != "_meta" and mid in match_to_day})
    if not played_days:
        return None

    records = {}
    for user in real_users:
        cumulative = 0
        vals = [0]
        for day in played_days:
            cumulative += day_pts[user].get(day, 0)
            vals.append(cumulative)
        records[user] = vals

    return pd.DataFrame(records, index=[0] + played_days)
