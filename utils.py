import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

DATA_DIR = Path("data")
PREDICTIONS_FILE = DATA_DIR / "predictions.json"
USERS_FILE = DATA_DIR / "users.json"

# Create data directory if it doesn't exist
DATA_DIR.mkdir(exist_ok=True)


def load_predictions() -> Dict:
    """Load all user predictions"""
    if PREDICTIONS_FILE.exists():
        with open(PREDICTIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_predictions(predictions: Dict) -> None:
    """Save all user predictions"""
    with open(PREDICTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(predictions, f, ensure_ascii=False, indent=2)


def load_users() -> Dict:
    """Load user information"""
    if USERS_FILE.exists():
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_users(users: Dict) -> None:
    """Save user information"""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def register_user(name: str) -> bool:
    """Register a new user"""
    users = load_users()

    if name in users:
        return False

    users[name] = {
        "registration_date": datetime.now().isoformat(),
        "points": 0,
    }

    save_users(users)

    # Create empty predictions entry for the user
    predictions = load_predictions()
    predictions[name] = {}
    save_predictions(predictions)

    return True


def get_users() -> List[str]:
    """Get list of all registered users"""
    users = load_users()
    return sorted(list(users.keys()))


def save_prediction(user: str, match_id: str, prediction: str) -> None:
    """Save a user's prediction (1, X, 2)"""
    predictions = load_predictions()

    if user not in predictions:
        predictions[user] = {}

    predictions[user][match_id] = prediction
    save_predictions(predictions)


def get_user_predictions(user: str) -> Dict[str, str]:
    """Get all predictions from a user"""
    predictions = load_predictions()
    return predictions.get(user, {})


def get_prediction(user: str, match_id: str) -> Optional[str]:
    """Get a user's prediction for a specific match"""
    predictions = load_predictions()
    return predictions.get(user, {}).get(match_id)


def calculate_points(user: str, matches_with_result: Dict) -> int:
    """
    Calculate a user's points based on correct predictions.
    matches_with_result: {match_id: "1" or "X" or "2"}
    """
    predictions = get_user_predictions(user)
    points = 0

    for match_id, result in matches_with_result.items():
        prediction = predictions.get(match_id)
        if prediction and prediction == result:
            points += 1

    return points


def update_user_points(user: str, points: int) -> None:
    """Update a user's total points"""
    users = load_users()
    if user in users:
        users[user]["points"] = points
        save_users(users)


def get_ranking() -> List[tuple]:
    """Get user ranking sorted by points"""
    users = load_users()
    ranking = [(name, data["points"]) for name, data in users.items()]
    return sorted(ranking, key=lambda x: x[1], reverse=True)
