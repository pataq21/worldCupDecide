import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from filelock import FileLock

from core.storage import USE_GITHUB, read_json, write_json

DATA_DIR = Path("data")
PREDICTIONS_FILE = DATA_DIR / "predictions.json"
USERS_FILE = DATA_DIR / "users.json"
RESULTS_FILE = DATA_DIR / "results.json"
PREDICTIONS_LOCK = DATA_DIR / "predictions.json.lock"
USERS_LOCK = DATA_DIR / "users.json.lock"
RESULTS_LOCK = DATA_DIR / "results.json.lock"

# Create data directory if it doesn't exist
DATA_DIR.mkdir(exist_ok=True)


def load_predictions() -> Dict:
    """Load all user predictions"""
    if USE_GITHUB:
        return read_json("predictions.json")
    if PREDICTIONS_FILE.exists():
        with open(PREDICTIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_predictions(predictions: Dict) -> None:
    """Save all user predictions"""
    if USE_GITHUB:
        write_json("predictions.json", predictions)
        return
    with open(PREDICTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(predictions, f, ensure_ascii=False, indent=2)


def load_users() -> Dict:
    """Load user information"""
    if USE_GITHUB:
        return read_json("users.json")
    if USERS_FILE.exists():
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_users(users: Dict) -> None:
    """Save user information"""
    if USE_GITHUB:
        write_json("users.json", users)
        return
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def load_results() -> Dict:
    """Load all match results"""
    if USE_GITHUB:
        return read_json("results.json")
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_results(results: Dict) -> None:
    """Save all match results"""
    if USE_GITHUB:
        write_json("results.json", results)
        return
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def save_match_result(match_id: str, goals1: int, goals2: int) -> None:
    """Save goals for a specific match"""
    with FileLock(RESULTS_LOCK):
        results = load_results()
        results[match_id] = {"goals1": goals1, "goals2": goals2}
        save_results(results)


def get_match_result(match_id: str) -> Optional[Dict]:
    """Get goals for a specific match"""
    results = load_results()
    return results.get(match_id)


def register_user(name: str) -> bool:
    """Register a new user"""
    with FileLock(USERS_LOCK):
        users = load_users()

        if name in users:
            return False

        users[name] = {
            "registration_date": datetime.now().isoformat(),
            "points": 0,
        }

        save_users(users)

    # Create empty predictions entry for the user
    with FileLock(PREDICTIONS_LOCK):
        predictions = load_predictions()
        predictions[name] = {}
        save_predictions(predictions)

    return True


def get_users() -> List[str]:
    """Get list of all registered users"""
    users = load_users()
    return sorted(list(users.keys()))


def save_prediction(user: str, match_id: str, prediction) -> None:
    """Save a user's prediction (goals dict or team name string)"""
    with FileLock(PREDICTIONS_LOCK):
        predictions = load_predictions()

        if user not in predictions:
            predictions[user] = {}

        if prediction is None:
            predictions[user].pop(match_id, None)
        else:
            predictions[user][match_id] = prediction
        save_predictions(predictions)


def get_user_predictions(user: str) -> Dict[str, str]:
    """Get all predictions from a user"""
    predictions = load_predictions()
    return predictions.get(user, {})


def get_prediction(user: str, match_id: str):
    """Get a user's prediction for a specific match"""
    predictions = load_predictions()
    return predictions.get(user, {}).get(match_id)
