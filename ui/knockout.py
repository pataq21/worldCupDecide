from datetime import datetime

import streamlit as st

from core.data import get_user_predictions, load_predictions, save_predictions
from tournament.groups import GROUPS
from tournament.knockout import (
    FINAL,
    QUARTER_FINALS,
    ROUND_OF_16,
    ROUND_OF_32,
    SEMI_FINALS,
    THIRD_PLACE,
    fill_bracket,
    generate_full_bracket_html,
    is_group_complete,
    resolve_user_knockout_bracket,
)


def tab_knockout():
    """Tab to display knockout bracket and allow user predictions."""
    st.header("🏅 Fase Eliminatoria")

    user = st.session_state.current_user
    if not user:
        st.warning("Selecciona un usuario para ver y predecir la fase eliminatoria")
        return

    # Block predictions once the knockout stage starts (June 28)
    KNOCKOUT_START = datetime(2026, 6, 28).date()
    locked = datetime.now().date() >= KNOCKOUT_START

    if locked:
        st.error(
            "🔒 Las predicciones están cerradas. La fase eliminatoria ya ha comenzado."
        )

    # Check how many groups are complete
    complete_groups = [g for g in GROUPS if is_group_complete(g)]
    st.caption(
        f"Grupos completados: {len(complete_groups)}/12 — "
        f"{''.join(sorted(complete_groups)) if complete_groups else 'Ninguno'}"
    )

    if not complete_groups:
        st.info(
            "La fase eliminatoria se rellenará automáticamente cuando se "
            "introduzcan los resultados de los partidos en la pestaña Admin."
        )
        return

    # Load real bracket (R32 teams from group stage results)
    real_bracket = fill_bracket()

    # Load user knockout predictions
    user_predictions = get_user_predictions(user)
    user_ko_preds = {k: v for k, v in user_predictions.items() if k.startswith("KO_")}

    # Resolve user's bracket
    user_bracket = resolve_user_knockout_bracket(user_ko_preds, real_bracket)

    # Show visual bracket
    st.subheader("🏆 Cuadro del Torneo")
    bracket_html = generate_full_bracket_html(user_bracket)
    st.components.v1.html(bracket_html, height=650, scrolling=True)

    st.divider()

    # --- Input section ---
    st.subheader("✏️ Tus Predicciones")
    st.caption(
        "Selecciona quién gana cada partido. El ganador avanza a la siguiente ronda."
    )

    # Save button at the top
    if not locked:
        if st.button("💾 Guardar predicciones eliminatoria", type="primary"):
            _save_all_ko_predictions(user)

    def _show_match_selector(match_num, user_bracket_data):
        """Show a selectbox for picking the winner of a match."""
        info = user_bracket_data[match_num]
        t1 = info.get("team1")
        t2 = info.get("team2")
        current_winner = info.get("winner")

        if not t1 and not t2:
            st.caption(f"P{match_num}: _Equipos pendientes_")
            return

        options = ["—"]
        if t1:
            options.append(t1)
        if t2:
            options.append(t2)

        # Determine current index
        current_idx = 0
        if current_winner in options:
            current_idx = options.index(current_winner)

        label_parts = []
        label_parts.append(t1 if t1 else "?")
        label_parts.append(t2 if t2 else "?")
        label = f"P{match_num}: {label_parts[0]}  vs  {label_parts[1]}"

        st.selectbox(
            label,
            options=options,
            index=current_idx,
            key=f"ko_select_{user}_{match_num}",
            disabled=locked,
        )

    # Show rounds in order
    round_configs = [
        ("⚔️ Dieciseisavos (Round of 32)", ROUND_OF_32),
        ("🏹 Octavos de Final", ROUND_OF_16),
        ("🎯 Cuartos de Final", QUARTER_FINALS),
        ("🔥 Semifinales", SEMI_FINALS),
        ("🥉 Tercer Puesto", THIRD_PLACE),
        ("⭐ Final", FINAL),
    ]

    for round_title, round_matches in round_configs:
        with st.expander(round_title, expanded=(round_matches == ROUND_OF_32)):
            # Show matches in 2 columns for R32, otherwise single column
            if len(round_matches) > 4:
                col1, col2 = st.columns(2)
                half = len(round_matches) // 2
                for i, (match_num, _, _) in enumerate(round_matches):
                    with col1 if i < half else col2:
                        _show_match_selector(match_num, user_bracket)
            else:
                for match_num, _, _ in round_matches:
                    _show_match_selector(match_num, user_bracket)


def _save_all_ko_predictions(user: str):
    """Save all knockout predictions at once from the current form state."""
    all_predictions = load_predictions()
    if user not in all_predictions:
        all_predictions[user] = {}

    all_rounds = (
        ROUND_OF_32 + ROUND_OF_16 + QUARTER_FINALS + SEMI_FINALS + THIRD_PLACE + FINAL
    )
    for match_num, _, _ in all_rounds:
        key = f"ko_select_{user}_{match_num}"
        selected = st.session_state.get(key)
        ko_key = f"KO_{match_num}"
        if selected and selected != "—":
            all_predictions[user][ko_key] = selected
        else:
            all_predictions[user].pop(ko_key, None)

    save_predictions(all_predictions)
    st.success("✅ Predicciones de eliminatoria guardadas correctamente")
