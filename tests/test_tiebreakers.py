"""
Regression test for FIFA head-to-head tiebreaking in group standings.

Scenario: España and Francia both finish on 6 points in the same group.
  - España beats Italia 5-0 and Grecia 5-0, loses to Francia 0-1  →  6 pts, GD +9
  - Francia beats España 1-0 and Italia 1-0, loses to Grecia 0-1  →  6 pts, GD +1

Without head-to-head tiebreaking, España ranks first (GD +9 > +1).
With FIFA rules, Francia ranks first because she beat España directly.
"""

from unittest.mock import patch

from tournament.knockout import calculate_real_group_standings

TEST_GROUPS = {"X": ["España", "Francia", "Italia", "Grecia"]}

TEST_MATCHES = [
    {"id": "X_0_1", "group": "X", "team1": "España",  "team2": "Francia"},
    {"id": "X_0_2", "group": "X", "team1": "España",  "team2": "Italia"},
    {"id": "X_0_3", "group": "X", "team1": "España",  "team2": "Grecia"},
    {"id": "X_1_2", "group": "X", "team1": "Francia", "team2": "Italia"},
    {"id": "X_1_3", "group": "X", "team1": "Francia", "team2": "Grecia"},
    {"id": "X_2_3", "group": "X", "team1": "Italia",  "team2": "Grecia"},
]

TEST_RESULTS = {
    "X_0_1": {"goals1": 0, "goals2": 1},  # España 0-1 Francia
    "X_0_2": {"goals1": 5, "goals2": 0},  # España 5-0 Italia
    "X_0_3": {"goals1": 5, "goals2": 0},  # España 5-0 Grecia
    "X_1_2": {"goals1": 1, "goals2": 0},  # Francia 1-0 Italia
    "X_1_3": {"goals1": 0, "goals2": 1},  # Francia 0-1 Grecia
    "X_2_3": {"goals1": 0, "goals2": 0},  # irrelevant
}


def test_head_to_head_tiebreaker():
    with (
        patch("tournament.knockout.load_results", return_value=TEST_RESULTS),
        patch("tournament.knockout.GROUPS", TEST_GROUPS),
        patch("tournament.knockout.GROUP_STAGE_MATCHES", TEST_MATCHES),
    ):
        standings = calculate_real_group_standings()

    teams = [t["team"] for t in standings["X"]]
    assert teams.index("Francia") < teams.index("España"), (
        f"Francia should rank above España (h2h win), but got order: {teams}"
    )
