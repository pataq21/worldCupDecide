from datetime import datetime

import streamlit as st

from core.data import get_user_predictions, load_predictions, save_predictions
from tournament.groups import GROUP_STAGE_MATCHES, GROUPS


def tab_predictions():
    """Tab to enter match results (goals)"""
    st.header("⚽ Fase de grupos")

    user = st.session_state.current_user
    if not user:
        st.warning("Selecciona un usuario para ingresar tu porra")
        return

    # Block predictions once the World Cup starts
    WORLD_CUP_START = datetime(2026, 6, 11, 22, 0, 0)
    locked = datetime.now() >= WORLD_CUP_START

    if locked:
        st.error("🔒 Las predicciones están cerradas. El Mundial ya ha comenzado.")

    st.write(f"Predicciones de **{user}**")

    # Save button at the top
    if not locked:
        if st.button("💾 Guardar predicciones", type="primary"):
            _save_all_predictions(user)

    # Load existing predictions for this user
    user_predictions = get_user_predictions(user)

    # Group matches by group
    for group_name in sorted(GROUPS.keys()):
        st.subheader(f"Grupo {group_name}")

        # Filter matches for this group
        group_matches = [m for m in GROUP_STAGE_MATCHES if m["group"] == group_name]

        for match in group_matches:
            pred = user_predictions.get(match["id"])
            default_goals1 = (
                str(pred["goals1"]) if pred and isinstance(pred, dict) else ""
            )
            default_goals2 = (
                str(pred["goals2"]) if pred and isinstance(pred, dict) else ""
            )

            fecha_espana = match.get("fecha_espana", "") or match["date"]
            date_str = datetime.strptime(fecha_espana, "%Y-%m-%d").strftime("%d %b") if fecha_espana else ""
            hora_espana = match.get("hora_espana", "")
            venue = match["venue"]
            st.caption(f"📅 {date_str} {hora_espana}  •  🏟️ {venue}")

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
                    label=match["team1"],
                    value=default_goals1,
                    key=f"goals1_{user}_{match['id']}",
                    label_visibility="collapsed",
                    disabled=locked,
                )
            with col3:
                st.markdown(
                    "<div style='text-align:center'>-</div>",
                    unsafe_allow_html=True,
                )
            with col4:
                st.text_input(
                    label=match["team2"],
                    value=default_goals2,
                    key=f"goals2_{user}_{match['id']}",
                    label_visibility="collapsed",
                    disabled=locked,
                )
            with col5:
                st.write(match["team2"])

        st.divider()


def _save_all_predictions(user: str):
    """Save all predictions at once from the current form state."""
    all_predictions = load_predictions()
    if user not in all_predictions:
        all_predictions[user] = {}

    for match in GROUP_STAGE_MATCHES:
        match_id = match["id"]
        raw1 = st.session_state.get(f"goals1_{user}_{match_id}", "")
        raw2 = st.session_state.get(f"goals2_{user}_{match_id}", "")
        try:
            if not raw1.strip() or not raw2.strip():
                all_predictions[user].pop(match_id, None)
                continue
            goals1 = int(raw1)
            goals2 = int(raw2)
            if goals1 >= 0 and goals2 >= 0:
                all_predictions[user][match_id] = {"goals1": goals1, "goals2": goals2}
        except (ValueError, AttributeError):
            pass

    save_predictions(all_predictions)
    st.success("✅ Predicciones guardadas correctamente")
