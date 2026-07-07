import altair as alt
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
                "Grupos": stats["group_points"],
                "Eliminatoria": stats["knockout_points"],
                "Total": stats["points"],
                "Exactos": stats["exact"],
                "Signo": stats["sign"],
            }
        )

    df_ranking = pd.DataFrame(ranking_data)
    st.dataframe(df_ranking, hide_index=True, width="stretch")
    st.caption(
        "Puntuación: Grupos (3 pts exacto • 1 pt signo) • Eliminatoria (2/3/5/7/10/12 pts por R32/R16/QF/SF/3P/Final)"
    )

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
            ordered = evolution_df.index.tolist()
            melted = (
                evolution_df[selected]
                .reset_index()
                .rename(columns={"index": "Jornada"})
                .melt(id_vars="Jornada", var_name="Usuario", value_name="Puntos")
            )
            chart = (
                alt.Chart(melted)
                .mark_line(point=True)
                .encode(
                    x=alt.X("Jornada:O", sort=ordered, title="Jornada / Ronda"),
                    y=alt.Y("Puntos:Q", title="Puntos acumulados"),
                    color=alt.Color("Usuario:N"),
                    tooltip=["Jornada", "Usuario", "Puntos"],
                )
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Selecciona al menos un usuario para ver la gráfica")
    else:
        st.info("Aún no hay resultados registrados")
