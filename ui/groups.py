import pandas as pd
import streamlit as st

from core.data import get_user_predictions
from tournament.groups import GROUP_STAGE_MATCHES, GROUPS, calculate_group_standings


def tab_group_stage():
    """Tab to view group standings"""
    st.header("📊 Tabla de Posiciones")

    user = st.session_state.current_user
    if not user:
        st.warning("Selecciona un usuario para ver su tabla de posiciones")
        return

    st.write(f"Tabla según predicciones de **{user}**")

    # Load user predictions into matches
    user_predictions = get_user_predictions(user)
    for match in GROUP_STAGE_MATCHES:
        pred = user_predictions.get(match["id"])
        if pred and isinstance(pred, dict):
            match["goals1"] = pred["goals1"]
            match["goals2"] = pred["goals2"]
        else:
            match["goals1"] = None
            match["goals2"] = None

    # Show each group
    for group_name in sorted(GROUPS.keys()):
        st.subheader(f"Grupo {group_name}")

        # Get standings for this group
        standings = calculate_group_standings(group_name)

        # Create standings table
        standings_data = []
        for position, team_data in enumerate(standings, 1):
            points = team_data["wins"] * 3 + team_data["draws"]
            goal_diff = team_data["goals_for"] - team_data["goals_against"]
            standings_data.append(
                {
                    "Pos": position,
                    "Equipo": team_data["team"],
                    "Pts": points,
                    "J": team_data["played"],
                    "G": team_data["wins"],
                    "E": team_data["draws"],
                    "P": team_data["losses"],
                    "GF": team_data["goals_for"],
                    "GC": team_data["goals_against"],
                    "DG": goal_diff,
                }
            )

        df_standings = pd.DataFrame(standings_data)
        st.dataframe(df_standings, width="stretch", hide_index=True)

        # Show matches for this group
        with st.expander(f"Ver partidos - Grupo {group_name}"):
            group_matches = [m for m in GROUP_STAGE_MATCHES if m["group"] == group_name]
            matches_data = []
            for match in group_matches:
                if match["goals1"] is not None and match["goals2"] is not None:
                    result = f"{match['goals1']} - {match['goals2']}"
                else:
                    result = "Sin jugar"

                matches_data.append(
                    {
                        "Partido": f"{match['team1']} vs {match['team2']}",
                        "Resultado": result,
                    }
                )

            df_matches = pd.DataFrame(matches_data)
            st.dataframe(df_matches, width="stretch", hide_index=True)

        st.divider()
