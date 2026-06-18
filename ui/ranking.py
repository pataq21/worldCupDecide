import pandas as pd
import streamlit as st

from core.scoring import get_ranking_detailed


def tab_ranking():
    """Tab to view user ranking"""
    st.header("🏆 Clasificación de Usuarios")

    ranking = get_ranking_detailed()

    if not ranking:
        st.info("Aún no hay usuarios registrados")
        return

    ranking_data = []
    for position, (name, stats) in enumerate(ranking, 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(position, f"{position}.")
        ranking_data.append(
            {
                "Pos.": medal,
                "Usuario": name,
                "Pts": stats["points"],
                "Exactos": stats["exact"],
                "Signo": stats["sign"],
            }
        )

    df_ranking = pd.DataFrame(ranking_data)
    st.dataframe(df_ranking, hide_index=True, use_container_width=True)

    st.caption("Puntuación: 3 pts resultado exacto • 1 pt acertar signo (1/X/2) • Signo incluye exactos")
