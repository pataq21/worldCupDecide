import pandas as pd
import streamlit as st

from core.data import get_users, load_knockout_config, load_predictions
from tournament.knockout import (
    FINAL,
    QUARTER_FINALS,
    ROUND_OF_16,
    ROUND_OF_32,
    SEMI_FINALS,
    THIRD_PLACE,
    fill_bracket,
    fill_bracket_from_config,
)

_ROUND_CONFIGS = [
    ("Dieciseisavos", ROUND_OF_32, 2),
    ("Octavos", ROUND_OF_16, 3),
    ("Cuartos", QUARTER_FINALS, 5),
    ("Semifinales", SEMI_FINALS, 7),
    ("3er Puesto", THIRD_PLACE, 10),
    ("Final", FINAL, 12),
]

_FIXED_COLS = ["Ronda", "Pts", "Partido", "Resultado"]

_GREEN = "background-color: rgba(0, 180, 80, 0.35)"
_RED = "background-color: rgba(220, 50, 50, 0.25)"
_AMBER = "background-color: rgba(220, 170, 0, 0.35)"


@st.cache_data
def _build_ko_results_rows(
    all_predictions: dict, real_bracket: dict, users: tuple
) -> tuple:
    # Teams definitively eliminated: they played a decided match and lost.
    eliminated = set()
    for info in real_bracket.values():
        winner = info.get("winner")
        if winner:
            for side in ("team1", "team2"):
                team = info.get(side)
                if team and team != winner:
                    eliminated.add(team)

    rows = []
    style_rows = []

    for round_name, round_matches, pts in _ROUND_CONFIGS:
        for match_num, _, _ in round_matches:
            info = real_bracket.get(match_num, {})
            team1 = info.get("team1")
            team2 = info.get("team2")
            actual_winner = info.get("winner")
            valid_teams = {t for t in (team1, team2) if t}

            if valid_teams:
                partido = f"{team1 or '?'} vs {team2 or '?'}"
            else:
                partido = "Por definir"

            row = {
                "Ronda": round_name,
                "Pts": pts,
                "Partido": partido,
                "Resultado": actual_winner or "—",
            }
            style_row = {col: "" for col in _FIXED_COLS}

            for user in users:
                pred = all_predictions.get(user, {}).get(f"KO_{match_num}")
                row[user] = pred or "—"

                if not pred:
                    style_row[user] = ""
                elif actual_winner:
                    style_row[user] = _GREEN if pred == actual_winner else _RED
                elif len(valid_teams) == 2 and pred not in valid_teams:
                    # Both teams are determined and pred isn't one of them —
                    # impossible regardless of remaining results.
                    style_row[user] = _AMBER
                elif pred in eliminated:
                    # Team lost an earlier match — can't reach this one.
                    style_row[user] = _AMBER
                else:
                    style_row[user] = ""

            rows.append(row)
            style_rows.append(style_row)

    return rows, style_rows


def tab_knockout_results():
    st.header("⚡ Eliminatoria: Predicciones vs Resultados")

    users = get_users()
    if not users:
        st.info("Aún no hay usuarios registrados")
        return

    knockout_config = load_knockout_config()
    if knockout_config:
        real_bracket = fill_bracket_from_config(knockout_config)
    else:
        real_bracket = fill_bracket()

    all_predictions = load_predictions()

    rows, style_rows = _build_ko_results_rows(
        all_predictions, real_bracket, tuple(users)
    )

    df = pd.DataFrame(rows)
    style_df = pd.DataFrame(style_rows)

    st.caption(
        "🟩 Correcto &nbsp;&nbsp; 🟥 Incorrecto &nbsp;&nbsp;"
        " 🟨 El equipo predicho no llegó a este partido"
    )

    st.dataframe(
        df.style.apply(lambda _: style_df, axis=None),
        hide_index=True,
        width="stretch",
    )
