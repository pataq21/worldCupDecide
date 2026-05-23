import streamlit as st
import pandas as pd
from data import GROUPS, GROUP_STAGE_MATCHES
from utils import (
    register_user,
    get_users,
    save_prediction,
    get_prediction,
    get_ranking,
    load_users,
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


def tab_predictions(user):
    """Tab to make predictions"""
    st.header("🎯 Hacer Predicciones")

    if not user:
        st.warning("Por favor, selecciona o crea un usuario primero")
        return

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
                st.write(f"{match['team1']} vs {match['team2']}")

                current_prediction = get_prediction(user, match["id"])

                prediction = st.radio(
                    label="Resultado:",
                    options=["1", "X", "2"],
                    format_func=lambda x: {
                        "1": f"1️⃣ {match['team1']} gana",
                        "X": "🤝 Empate",
                        "2": f"2️⃣ {match['team2']} gana",
                    }[x],
                    index=["1", "X", "2"].index(current_prediction) if current_prediction else None,
                    key=f"pred_{match['id']}",
                    horizontal=False,
                )

                if st.button("Guardar", key=f"btn_{match['id']}"):
                    save_prediction(user, match["id"], prediction)
                    st.success("✅ Predicción guardada")

            col_index += 1

        st.divider()


def tab_group_stage(user):
    """Tab to view group stage with predictions"""
    st.header("📊 Fase de Grupos")

    # Show each group
    for group_name in sorted(GROUPS.keys()):
        st.subheader(f"Grupo {group_name}")

        group_teams = GROUPS[group_name]

        # Matches table for the group
        st.write("**Partidos:**")

        group_matches = [m for m in GROUP_STAGE_MATCHES if m["group"] == group_name]

        matches_data = []
        for match in group_matches:
            prediction = (
                get_prediction(user, match["id"])
                if user
                else None
            )

            prediction_text = {
                "1": f"1️⃣ {match['team1']}",
                "X": "🤝 Empate",
                "2": f"2️⃣ {match['team2']}",
            }.get(prediction, "Sin predicción")

            matches_data.append({
                "Partido": f"{match['team1']} vs {match['team2']}",
                "Tu Predicción": prediction_text if user else "-",
            })

        df = pd.DataFrame(matches_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.divider()


def tab_ranking():
    """Tab to view user ranking"""
    st.header("🏆 Clasificación")

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
        ["🎯 Predicciones", "📊 Grupos", "🏆 Clasificación"]
    )

    with tab1:
        tab_predictions(user)

    with tab2:
        tab_group_stage(user)

    with tab3:
        tab_ranking()


if __name__ == "__main__":
    main()
