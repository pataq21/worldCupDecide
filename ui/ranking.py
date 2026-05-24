import pandas as pd
import streamlit as st

from core.scoring import get_ranking


def tab_ranking():
    """Tab to view user ranking"""
    st.header("🏆 Clasificación de Usuarios")

    ranking = get_ranking()

    if not ranking:
        st.info("Aún no hay usuarios registrados")
        return

    # Create ranking table
    ranking_data = []
    for position, (name, points) in enumerate(ranking, 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(position, f"{position}.")
        ranking_data.append(
            {
                "Posición": medal,
                "Usuario": name,
                "Puntos": points,
            }
        )

    df_ranking = pd.DataFrame(ranking_data)
    st.dataframe(df_ranking, width="stretch", hide_index=True)

    st.caption("Puntuación: 3 pts resultado exacto • 1 pt acertar ganador/empate")
