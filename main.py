import streamlit as st
import pandas as pd
from data import GROUPS, GROUP_STAGE_MATCHES, calculate_group_standings
from utils import (
    register_user,
    get_users,
    save_prediction,
    get_prediction,
    get_ranking,
    load_users,
    save_match_result,
    get_match_result,
    load_results,
)

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


def load_match_results():
    """Load all match results from persistent storage"""
    results = load_results()
    for match in GROUP_STAGE_MATCHES:
        if match["id"] in results:
            match["goals1"] = results[match["id"]]["goals1"]
            match["goals2"] = results[match["id"]]["goals2"]


def tab_results():
    """Tab to enter match results (goals)"""
    st.header("⚽ Ingreso de Goles")
    st.write("Ingresa los goles de cada partido para calcular automáticamente la tabla de posiciones")

    # Load existing results
    load_match_results()

    # Group matches by group
    for group_name in sorted(GROUPS.keys()):
        st.subheader(f"Grupo {group_name}")

        # Filter matches for this group
        group_matches = [m for m in GROUP_STAGE_MATCHES if m["group"] == group_name]

        # Show group teams
        group_teams = GROUPS[group_name]
        st.markdown(f"**Equipos:** {', '.join(group_teams)}")

        # Create columns for matches
        cols = st.columns(3)
        col_index = 0

        for match in group_matches:
            with cols[col_index % 3]:
                st.write(f"**{match['team1']} vs {match['team2']}**")

                col_a, col_b = st.columns(2, gap="small")

                with col_a:
                    goals1 = st.number_input(
                        label=match['team1'],
                        min_value=0,
                        value=match['goals1'] if match['goals1'] is not None else 0,
                        key=f"goals1_{match['id']}",
                    )

                with col_b:
                    goals2 = st.number_input(
                        label=match['team2'],
                        min_value=0,
                        value=match['goals2'] if match['goals2'] is not None else 0,
                        key=f"goals2_{match['id']}",
                    )

                if st.button("Guardar", key=f"btn_{match['id']}", use_container_width=True):
                    save_match_result(match["id"], goals1, goals2)
                    match['goals1'] = goals1
                    match['goals2'] = goals2
                    st.success("✅ Goles guardados")

            col_index += 1

        st.divider()


def tab_group_stage():
    """Tab to view group standings"""
    st.header("📊 Tabla de Posiciones")

    # Load existing results
    load_match_results()

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
            standings_data.append({
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
            })

        df_standings = pd.DataFrame(standings_data)
        st.dataframe(df_standings, use_container_width=True, hide_index=True)

        # Show matches for this group
        with st.expander(f"Ver partidos - Grupo {group_name}"):
            group_matches = [m for m in GROUP_STAGE_MATCHES if m["group"] == group_name]
            matches_data = []
            for match in group_matches:
                if match['goals1'] is not None and match['goals2'] is not None:
                    result = f"{match['goals1']} - {match['goals2']}"
                else:
                    result = "Sin jugar"

                matches_data.append({
                    "Partido": f"{match['team1']} vs {match['team2']}",
                    "Resultado": result,
                })

            df_matches = pd.DataFrame(matches_data)
            st.dataframe(df_matches, use_container_width=True, hide_index=True)

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
        ranking_data.append({
            "Posición": medal,
            "Usuario": name,
            "Puntos": points,
        })

    df_ranking = pd.DataFrame(ranking_data)
    st.dataframe(df_ranking, use_container_width=True, hide_index=True)


def main():
    # Select user
    user = select_user()

    if user:
        st.session_state.current_user = user
        st.sidebar.success(f"✅ Sesión: {user}")

    # Create tabs
    tab1, tab2, tab3 = st.tabs(
        ["⚽ Goles", "📊 Tabla de Posiciones", "🏆 Clasificación"]
    )

    with tab1:
        tab_results()

    with tab2:
        tab_group_stage()

    with tab3:
        tab_ranking()


if __name__ == "__main__":
    main()
