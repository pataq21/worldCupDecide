import os
from datetime import datetime

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from data import GROUP_STAGE_MATCHES, GROUPS, calculate_group_standings
from knockout import (
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
from utils import (
    get_ranking,
    get_user_predictions,
    get_users,
    load_results,
    register_user,
    save_match_result,
    save_prediction,
    save_results,
)

load_dotenv()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Page configuration
st.set_page_config(
    page_title="Porra Mundial 2026",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("⚽ Porra Mundial 2026")

# Initialize session
if "current_user" not in st.session_state:
    st.session_state.current_user = None


def select_user():
    """Interface to select or register a user"""
    st.sidebar.header("👤 Usuario")

    users = get_users()

    col1, col2 = st.sidebar.columns([2, 1])

    with col1:
        selected_user = st.selectbox(
            "Selecciona tu usuario:",
            options=users if users else ["Sin usuarios"],
            key="user_select",
        )

    with col2:
        if st.button("Nuevo usuario"):
            st.session_state.new_user = True

    # Form for new user
    if st.session_state.get("new_user", False):
        new_name = st.sidebar.text_input("Nombre de nuevo usuario:")
        if st.sidebar.button("Crear usuario"):
            if new_name:
                if register_user(new_name):
                    st.session_state.current_user = new_name
                    st.session_state.new_user = False
                    st.rerun()
                else:
                    st.sidebar.error("El usuario ya existe")

    return selected_user if selected_user != "Sin usuarios" else None


def tab_results():
    """Tab to enter match results (goals)"""
    st.header("⚽ Ingreso de Goles")

    user = st.session_state.current_user
    if not user:
        st.warning("Selecciona un usuario para ingresar tu porra")
        return

    # Block predictions once the World Cup starts
    WORLD_CUP_START = datetime(2026, 6, 11).date()
    locked = datetime.now().date() >= WORLD_CUP_START

    if locked:
        st.error("🔒 Las predicciones están cerradas. El Mundial ya ha comenzado.")

    st.write(f"Predicciones de **{user}**")

    def _auto_save(match_id):
        """Save prediction automatically when a field changes"""
        if locked:
            return
        raw1 = st.session_state.get(f"goals1_{user}_{match_id}", "")
        raw2 = st.session_state.get(f"goals2_{user}_{match_id}", "")
        try:
            if not raw1.strip() or not raw2.strip():
                return
            goals1 = int(raw1)
            goals2 = int(raw2)
            if goals1 >= 0 and goals2 >= 0:
                save_prediction(user, match_id, {"goals1": goals1, "goals2": goals2})
        except (ValueError, AttributeError):
            pass

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

            # Show date, time in Spain and venue
            date_str = ""
            if match["date"]:
                dt = datetime.strptime(match["date"], "%Y-%m-%d")
                date_str = dt.strftime("%d %b")
            hora = match.get("hora_espana", "")
            venue = match["venue"]
            st.caption(f"📅 {date_str}  •  🇪🇸 {hora}h  •  🏟️ {venue}")

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
                    on_change=_auto_save,
                    args=(match["id"],),
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
                    on_change=_auto_save,
                    args=(match["id"],),
                    disabled=locked,
                )
            with col5:
                st.write(match["team2"])

        st.divider()


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


def tab_admin():
    """Admin tab for entering real match results."""
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

    # API fetch button
    st.subheader("🔄 Actualizar desde API")
    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        fetch_clicked = st.button("Obtener resultados de API")
    with col_info:
        results_data = load_results()
        last_fetch = results_data.get("_meta", {}).get("last_fetch", "Nunca")
        st.caption(f"Última actualización: {last_fetch}")

    if fetch_clicked:
        try:
            from api import fetch_results_from_api

            fetched = fetch_results_from_api()
            if fetched:
                current_results = load_results()
                meta = current_results.pop("_meta", {})
                current_results.update(fetched)
                meta["last_fetch"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                current_results["_meta"] = meta
                save_results(current_results)
                st.success(f"✅ {len(fetched)} resultado(s) actualizados desde la API")
                st.rerun()
            else:
                st.info("No se encontraron resultados nuevos")
        except ValueError as e:
            st.warning(str(e))
        except Exception as e:
            st.error(f"Error al consultar la API: {e}")

    st.divider()

    # Manual result entry
    st.subheader("✏️ Introducir resultados manualmente")

    # Filter matches already played (date <= today)
    past_matches = [m for m in GROUP_STAGE_MATCHES]

    if not past_matches:
        st.info("Aún no hay partidos disputados")
        return

    results = load_results()

    def _save_result(match_id):
        """Save result on field change."""
        raw1 = st.session_state.get(f"res_goals1_{match_id}", "")
        raw2 = st.session_state.get(f"res_goals2_{match_id}", "")
        try:
            g1 = int(raw1) if raw1.strip() else None
            g2 = int(raw2) if raw2.strip() else None
            if g1 is not None and g2 is not None and g1 >= 0 and g2 >= 0:
                save_match_result(match_id, g1, g2)
        except (ValueError, AttributeError):
            pass

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
                st.text_input(
                    label=f"G1 {match['id']}",
                    value=default_g1,
                    key=f"res_goals1_{match['id']}",
                    label_visibility="collapsed",
                    on_change=_save_result,
                    args=(match["id"],),
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
                    on_change=_save_result,
                    args=(match["id"],),
                )
            with col5:
                st.write(match["team2"])

        st.divider()


def tab_knockout():
    """Tab to display knockout bracket and allow user predictions."""
    st.header("🏅 Fase Eliminatoria")

    user = st.session_state.current_user
    if not user:
        st.warning("Selecciona un usuario para ver y predecir la fase eliminatoria")
        return

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

    def _save_ko_prediction(match_num):
        """Save knockout prediction and trigger rerun for propagation."""
        key = f"ko_select_{user}_{match_num}"
        selected = st.session_state.get(key)
        if selected and selected != "—":
            save_prediction(user, f"KO_{match_num}", selected)
        elif selected == "—":
            # Clear prediction
            save_prediction(user, f"KO_{match_num}", None)

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
            on_change=_save_ko_prediction,
            args=(match_num,),
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


def main():
    # Select user
    user = select_user()

    if user:
        st.session_state.current_user = user
        st.sidebar.success(f"✅ Sesión: {user}")

    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "⚽ Fase de grupos",
            "📊 Tabla de posiciones",
            "🏅 Fase eliminatoria",
            "🏆 Clasificación",
            "🔧 Admin",
        ]
    )

    with tab1:
        tab_results()

    with tab2:
        tab_group_stage()

    with tab3:
        tab_knockout()

    with tab4:
        tab_ranking()

    with tab5:
        tab_admin()


if __name__ == "__main__":
    main()
