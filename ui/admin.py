from datetime import datetime

import streamlit as st

from core.data import load_results, save_results
from tournament.groups import GROUP_STAGE_MATCHES, GROUPS


def tab_admin():
    """Admin tab for entering real match results."""
    import os

    from dotenv import load_dotenv

    load_dotenv()
    try:
        ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
    except (FileNotFoundError, KeyError):
        ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

    st.header("🔧 Administración de Resultados")

    # Password protection
    if not st.session_state.get("admin_authenticated", False):
        password = st.text_input(
            "Contraseña de administrador:", type="password", key="admin_pw"
        )
        if st.button("Acceder"):
            if password == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
        return

    # --- Admin authenticated ---
    today = datetime.now().date()

    # Manual result entry
    st.subheader("✏️ Introducir resultados")

    # Filter matches already played (date <= today)
    past_matches = [m for m in GROUP_STAGE_MATCHES]

    if not past_matches:
        st.info("Aún no hay partidos disputados")
        return

    results = load_results()

    with st.form("admin_results_form"):
        for group_name in sorted(GROUPS.keys()):
            group_past = [m for m in past_matches if m["group"] == group_name]
            if not group_past:
                continue

            st.subheader(f"Grupo {group_name}")
            for match in group_past:
                existing = results.get(match["id"])
                default_g1 = (
                    str(existing["goals1"])
                    if existing and isinstance(existing, dict)
                    else ""
                )
                default_g2 = (
                    str(existing["goals2"])
                    if existing and isinstance(existing, dict)
                    else ""
                )

                status = "✅" if existing and isinstance(existing, dict) else "⬜"
                date_str = datetime.strptime(match["date"], "%Y-%m-%d").strftime(
                    "%d %b"
                )
                st.caption(
                    f"{status} 📅 {date_str}  •  🇪🇸 {match.get('hora_espana', '')}h"
                )

                col1, col2, col3, col4, col5 = st.columns(
                    [4, 0.4, 0.3, 0.4, 4], vertical_alignment="center"
                )
                with col1:
                    st.markdown(
                        f"<div style='text-align:right'>{match['team1']}</div>",
                        unsafe_allow_html=True,
                    )
                with col2:
                    st.text_input(
                        label=f"G1 {match['id']}",
                        value=default_g1,
                        key=f"res_goals1_{match['id']}",
                        label_visibility="collapsed",
                    )
                with col3:
                    st.markdown(
                        "<div style='text-align:center'>-</div>",
                        unsafe_allow_html=True,
                    )
                with col4:
                    st.text_input(
                        label=f"G2 {match['id']}",
                        value=default_g2,
                        key=f"res_goals2_{match['id']}",
                        label_visibility="collapsed",
                    )
                with col5:
                    st.write(match["team2"])

            st.divider()

        submitted = st.form_submit_button("💾 Guardar resultados", type="primary")

    if submitted:
        _save_all_results()


def _save_all_results():
    """Save all manually entered results at once."""
    old_results = load_results()
    meta = old_results.pop("_meta", {})

    # Build results from scratch based on form values
    results = {}
    count = 0

    for match in GROUP_STAGE_MATCHES:
        match_id = match["id"]
        raw1 = st.session_state.get(f"res_goals1_{match_id}", "")
        raw2 = st.session_state.get(f"res_goals2_{match_id}", "")
        try:
            raw1 = str(raw1).strip() if raw1 is not None else ""
            raw2 = str(raw2).strip() if raw2 is not None else ""
            if raw1 and raw2:
                g1 = int(raw1)
                g2 = int(raw2)
                if g1 >= 0 and g2 >= 0:
                    results[match_id] = {"goals1": g1, "goals2": g2}
                    count += 1
        except (ValueError, TypeError):
            pass

    results["_meta"] = meta
    save_results(results)
    st.success(f"✅ {count} resultado(s) guardados correctamente")
    st.rerun()
