import pandas as pd
import streamlit as st

from core.scoring import get_points_evolution, get_ranking_detailed


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

    st.subheader("Evolución por jornada")
    evolution_df = get_points_evolution()
    if evolution_df is not None:
        all_users = list(evolution_df.columns)
        selected = st.multiselect(
            "Mostrar usuarios:",
            options=all_users,
            default=all_users[:5] if len(all_users) > 5 else all_users,
        )
        if selected:
            st.line_chart(evolution_df[selected], x_label="Jornada", y_label="Puntos acumulados")
        else:
            st.info("Selecciona al menos un usuario para ver la gráfica")
    else:
        st.info("Aún no hay resultados registrados")
