# World Cup 2026 Data - Group Stage (Official Draw)
import json
from pathlib import Path

SCHEDULE_PATH = Path(__file__).parent.parent / "data" / "schedule.json"

with open(SCHEDULE_PATH, encoding="utf-8") as f:
    MATCH_SCHEDULE = json.load(f)

GROUPS = {
    "A": ["México", "Corea del Sur", "República Checa", "Sudáfrica"],
    "B": ["Canadá", "Catar", "Suiza", "Bosnia y Herzegovina"],
    "C": ["Brasil", "Haití", "Escocia", "Marruecos"],
    "D": ["Estados Unidos", "Australia", "Turquía", "Paraguay"],
    "E": ["Alemania", "Curazao", "Costa de Marfil", "Ecuador"],
    "F": ["Países Bajos", "Japón", "Suecia", "Túnez"],
    "G": ["Bélgica", "Egipto", "Irán", "Nueva Zelanda"],
    "H": ["España", "Uruguay", "Arabia Saudí", "Cabo Verde"],
    "I": ["Francia", "Senegal", "Irak", "Noruega"],
    "J": ["Argentina", "Argelia", "Austria", "Jordania"],
    "K": ["Portugal", "Uzbekistán", "Colombia", "RD Congo"],
    "L": ["Inglaterra", "Croacia", "Panamá", "Ghana"],
}


def generate_matches():
    """Generates all group stage matches with schedule info, sorted by date"""
    matches = []

    for group_name, teams in GROUPS.items():
        for i in range(len(teams)):
            for j in range(i + 1, len(teams)):
                match_id = f"{group_name}_{i}_{j}"
                schedule = MATCH_SCHEDULE.get(match_id, {})
                matches.append(
                    {
                        "id": match_id,
                        "group": group_name,
                        "team1": teams[i],
                        "team2": teams[j],
                        "date": schedule.get("date", ""),
                        "venue": schedule.get("venue", ""),
                        "hora_local": schedule.get("hora_local", ""),
                        "hora_espana": schedule.get("hora_espana", ""),
                        "fecha_espana": schedule.get("fecha_espana", ""),
                        "match_day": schedule.get("match_day", 0),
                        "goals1": None,
                        "goals2": None,
                    }
                )

    # Sort by date within each group
    matches.sort(
        key=lambda m: (m["group"], MATCH_SCHEDULE.get(m["id"], {}).get("date", ""))
    )
    return matches


GROUP_STAGE_MATCHES = generate_matches()


def calculate_group_standings(group_name):
    """Calculate standings for a group based on match results"""
    from collections import defaultdict

    teams = GROUPS[group_name]
    standings = defaultdict(
        lambda: {
            "team": "",
            "played": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "goals_for": 0,
            "goals_against": 0,
        }
    )

    # Initialize standings for all teams
    for team in teams:
        standings[team]["team"] = team

    # Process matches
    group_matches = [m for m in GROUP_STAGE_MATCHES if m["group"] == group_name]

    for match in group_matches:
        if match["goals1"] is not None and match["goals2"] is not None:
            team1 = match["team1"]
            team2 = match["team2"]
            goals1 = match["goals1"]
            goals2 = match["goals2"]

            # Update played matches
            standings[team1]["played"] += 1
            standings[team2]["played"] += 1

            # Update goals
            standings[team1]["goals_for"] += goals1
            standings[team1]["goals_against"] += goals2
            standings[team2]["goals_for"] += goals2
            standings[team2]["goals_against"] += goals1

            # Update W/D/L
            if goals1 > goals2:
                standings[team1]["wins"] += 1
                standings[team2]["losses"] += 1
            elif goals1 < goals2:
                standings[team1]["losses"] += 1
                standings[team2]["wins"] += 1
            else:
                standings[team1]["draws"] += 1
                standings[team2]["draws"] += 1

    # Sort by: points (desc), goal difference (desc), goals for (desc)
    sorted_standings = sorted(
        standings.values(),
        key=lambda x: (
            x["wins"] * 3 + x["draws"],  # Points
            x["goals_for"] - x["goals_against"],  # Goal difference
            x["goals_for"],  # Goals for
        ),
        reverse=True,
    )

    return sorted_standings
