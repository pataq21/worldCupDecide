from typing import List

from core.data import get_user_predictions, load_results, load_users


def _get_outcome(goals1: int, goals2: int) -> str:
    """Return '1' (home win), 'X' (draw), or '2' (away win)."""
    if goals1 > goals2:
        return "1"
    elif goals1 < goals2:
        return "2"
    return "X"


def calculate_user_points(user: str) -> int:
    """
    Calculate a user's total points.
    - 3 pts for exact score match
    - 1 pt for correct outcome (1/X/2) but wrong score
    """
    predictions = get_user_predictions(user)
    results = load_results()
    points = 0

    for match_id, result in results.items():
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
        elif _get_outcome(pred_g1, pred_g2) == _get_outcome(real_g1, real_g2):
            points += 1

    return points


def get_ranking() -> List[tuple]:
    """Get user ranking sorted by points (computed dynamically)."""
    users = load_users()
    ranking = [(name, calculate_user_points(name)) for name in users]
    return sorted(ranking, key=lambda x: x[1], reverse=True)
