"""Football-data.org API integration for fetching real match results."""

import os
from typing import Dict, Optional

import requests
import streamlit as st
from dotenv import load_dotenv

from data import GROUPS

load_dotenv()

API_BASE = "https://api.football-data.org/v4"
API_KEY = st.secrets.get(
    "FOOTBALL_DATA_API_KEY", os.getenv("FOOTBALL_DATA_API_KEY", "")
)

# Mapping from football-data.org English team names to our Spanish names
TEAM_NAME_MAP = {
    "Mexico": "México",
    "Korea Republic": "Corea del Sur",
    "Czech Republic": "República Checa",
    "South Africa": "Sudáfrica",
    "Canada": "Canadá",
    "Qatar": "Catar",
    "Switzerland": "Suiza",
    "Bosnia and Herzegovina": "Bosnia y Herzegovina",
    "Brazil": "Brasil",
    "Haiti": "Haití",
    "Scotland": "Escocia",
    "Morocco": "Marruecos",
    "United States": "Estados Unidos",
    "Australia": "Australia",
    "Turkey": "Turquía",
    "Paraguay": "Paraguay",
    "Germany": "Alemania",
    "Curacao": "Curazao",
    "Ivory Coast": "Costa de Marfil",
    "Côte d'Ivoire": "Costa de Marfil",
    "Ecuador": "Ecuador",
    "Netherlands": "Países Bajos",
    "Japan": "Japón",
    "Sweden": "Suecia",
    "Tunisia": "Túnez",
    "Belgium": "Bélgica",
    "Egypt": "Egipto",
    "Iran": "Irán",
    "New Zealand": "Nueva Zelanda",
    "Spain": "España",
    "Uruguay": "Uruguay",
    "Saudi Arabia": "Arabia Saudí",
    "Cape Verde": "Cabo Verde",
    "France": "Francia",
    "Senegal": "Senegal",
    "Iraq": "Irak",
    "Norway": "Noruega",
    "Argentina": "Argentina",
    "Algeria": "Argelia",
    "Austria": "Austria",
    "Jordan": "Jordania",
    "Portugal": "Portugal",
    "Uzbekistan": "Uzbekistán",
    "Colombia": "Colombia",
    "DR Congo": "RD Congo",
    "Congo DR": "RD Congo",
    "England": "Inglaterra",
    "Croatia": "Croacia",
    "Panama": "Panamá",
    "Ghana": "Ghana",
}

# Build reverse lookup: Spanish name -> (group, index in group)
_TEAM_TO_GROUP_INDEX: Dict[str, tuple] = {}
for _group, _teams in GROUPS.items():
    for _idx, _team in enumerate(_teams):
        _TEAM_TO_GROUP_INDEX[_team] = (_group, _idx)


def _find_match_id(team1_es: str, team2_es: str) -> Optional[str]:
    """Find the match_id for two teams (in Spanish) regardless of order."""
    info1 = _TEAM_TO_GROUP_INDEX.get(team1_es)
    info2 = _TEAM_TO_GROUP_INDEX.get(team2_es)
    if not info1 or not info2:
        return None
    if info1[0] != info2[0]:
        return None  # Not in same group

    group = info1[0]
    i, j = sorted([info1[1], info2[1]])
    match_id = f"{group}_{i}_{j}"

    # Check if the order matches our schedule (team1 is the lower index)
    teams = GROUPS[group]
    if teams[i] == team1_es:
        return match_id
    # If reversed, still same match_id but we need to note the swap
    return match_id


def _get_match_order(match_id: str, team1_es: str) -> bool:
    """Returns True if team1_es is the 'home' team (lower index) in our schedule."""
    parts = match_id.split("_")
    group = parts[0]
    i = int(parts[1])
    return GROUPS[group][i] == team1_es


def fetch_results_from_api() -> Dict[str, Dict]:
    """
    Fetch finished match results from football-data.org.
    Returns: {match_id: {"goals1": int, "goals2": int}} for matches we can map.
    Raises requests.HTTPError on API failure.
    """
    if not API_KEY or API_KEY == "your_api_key_here":
        raise ValueError("API key not configured. Set FOOTBALL_DATA_API_KEY in .env")

    headers = {"X-Auth-Token": API_KEY}
    url = f"{API_BASE}/competitions/WC/matches"
    params = {"status": "FINISHED"}

    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()
    matches = data.get("matches", [])

    results = {}
    for match in matches:
        home_name = match.get("homeTeam", {}).get("name", "")
        away_name = match.get("awayTeam", {}).get("name", "")
        score = match.get("score", {}).get("fullTime", {})

        if score.get("home") is None or score.get("away") is None:
            continue

        # Map to Spanish names
        home_es = TEAM_NAME_MAP.get(home_name)
        away_es = TEAM_NAME_MAP.get(away_name)

        if not home_es or not away_es:
            continue

        match_id = _find_match_id(home_es, away_es)
        if not match_id:
            continue

        # Determine goal order based on our schedule's team order
        if _get_match_order(match_id, home_es):
            results[match_id] = {
                "goals1": score["home"],
                "goals2": score["away"],
            }
        else:
            results[match_id] = {
                "goals1": score["away"],
                "goals2": score["home"],
            }

    return results
