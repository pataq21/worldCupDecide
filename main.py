import streamlit as st
from dotenv import load_dotenv

from core.data import get_users, register_user
from ui.admin import tab_admin
from ui.groups import tab_group_stage
from ui.knockout import tab_knockout
from ui.knockout_results import tab_knockout_results
from ui.predictions import tab_predictions
from ui.ranking import tab_ranking
from ui.results import tab_results

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Porra Mundial 2026",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("⚽ Porra Mundial 2026")

# Debug: show storage mode
# st.sidebar.caption(f"💾 Almacenamiento: {'GitHub' if USE_GITHUB else 'Local'}")

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


def main():
    # Select user
    user = select_user()

    if user:
        st.session_state.current_user = user
        st.sidebar.success(f"✅ Sesión: {user}")

    # Top-level tabs
    grupos, eliminatoria, clasificacion, admin = st.tabs(
        ["⚽ Fase de grupos", "🏅 Fase eliminatoria", "🏆 Clasificación", "🔧 Admin"]
    )

    with grupos:
        sub1, sub2, sub3 = st.tabs(
            ["✏️ Predicciones", "📋 Resultados", "📊 Posiciones"]
        )
        with sub1:
            tab_predictions()
        with sub2:
            tab_results()
        with sub3:
            tab_group_stage()

    with eliminatoria:
        sub4, sub5 = st.tabs(["✏️ Predicciones", "⚡ Resultados"])
        with sub4:
            tab_knockout()
        with sub5:
            tab_knockout_results()

    with clasificacion:
        tab_ranking()

    with admin:
        tab_admin()


if __name__ == "__main__":
    main()
