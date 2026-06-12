from datetime import datetime

import streamlit as st

from core.data import load_results
from tournament.groups import GROUP_STAGE_MATCHES, GROUPS


def tab_results():
    """Read-only tab showing group stage results."""
    st.header("📋 Fase de grupos (resultados)")

    results = load_results()

    past_matches = [m for m in GROUP_STAGE_MATCHES]

    if not past_matches:
        st.info("Aún no hay partidos disputados")
        return

    for group_name in sorted(GROUPS.keys()):
        group_matches = [m for m in past_matches if m["group"] == group_name]
        if not group_matches:
            continue

        st.subheader(f"Grupo {group_name}")
        for match in group_matches:
            existing = results.get(match["id"])

            if existing and isinstance(existing, dict):
                goals1 = existing["goals1"]
                goals2 = existing["goals2"]
                status = "✅"
            else:
                goals1 = "-"
                goals2 = "-"
                status = "⬜"

            date_str = datetime.strptime(match["date"], "%Y-%m-%d").strftime("%d %b")
            st.caption(f"{status} 📅 {date_str}  •  🇪🇸 {match.get('hora_espana', '')}h")

            col1, col2, col3, col4, col5 = st.columns(
                [4, 0.4, 0.3, 0.4, 4], vertical_alignment="center"
            )
            with col1:
                st.markdown(
                    f"<div style='text-align:right'>{match['team1']}</div>",
                    unsafe_allow_html=True,
                )
            with col2:
                st.markdown(
                    f"<div style='text-align:center'><b>{goals1}</b></div>",
                    unsafe_allow_html=True,
                )
            with col3:
                st.markdown(
                    "<div style='text-align:center'>-</div>",
                    unsafe_allow_html=True,
                )
            with col4:
                st.markdown(
                    f"<div style='text-align:center'><b>{goals2}</b></div>",
                    unsafe_allow_html=True,
                )
            with col5:
                st.write(match["team2"])

        st.divider()
