from datetime import datetime

import streamlit as st

from core.data import (
    load_knockout_config,
    load_results,
    save_knockout_config,
    save_results,
)
from tournament.groups import GROUP_STAGE_MATCHES, GROUPS
from tournament.knockout import (
    FINAL,
    QUARTER_FINALS,
    ROUND_OF_16,
    ROUND_OF_32,
    SEMI_FINALS,
    THIRD_PLACE,
    fill_bracket_from_config,
    generate_full_bracket_html,
)

# Empty sentinel used in selectboxes to mean "no winner / no team selected"
_EMPTY = "\u2014"  # em dash

# All knockout rounds in order, paired with a human label
_KO_ROUNDS = [
    ("\u2694\ufe0f Dieciseisavos", ROUND_OF_32),
    ("\U0001f3f9 Octavos de Final", ROUND_OF_16),
    ("\U0001f3af Cuartos de Final", QUARTER_FINALS),
    ("\U0001f525 Semifinales", SEMI_FINALS),
    ("\U0001f949 Tercer Puesto", THIRD_PLACE),
    ("\u2b50 Final", FINAL),
]
_ALL_KO_MATCHES = (
    ROUND_OF_32 + ROUND_OF_16 + QUARTER_FINALS + SEMI_FINALS + THIRD_PLACE + FINAL
)


def _admin_authenticate():
    """Helper for admin authentication"""
    import os

    from dotenv import load_dotenv

    load_dotenv()
    try:
        ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
    except (FileNotFoundError, KeyError):
        ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

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
        return False

    return True


def tab_group_results():
    """Admin tab for entering real match results from group stage."""
    st.header("✏️ Resultados Fase de Grupos")

    # Manual result entry
    st.subheader("Introducir resultados de partidos")

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
                fecha_espana = match.get("fecha_espana", "") or match["date"]
                date_str = datetime.strptime(fecha_espana, "%Y-%m-%d").strftime("%d %b")
                hora_espana = match.get("hora_espana", "")
                st.caption(f"{status} 📅 {date_str} {hora_espana}")

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


def _build_live_config() -> dict:
    """Build the current knockout config from the live session_state widget values."""
    config = {}

    # R32: team pairings come from the admin selectors
    for match_num, _, _ in ROUND_OF_32:
        t1 = st.session_state.get(f"adm_t1_{match_num}", "")
        t2 = st.session_state.get(f"adm_t2_{match_num}", "")
        entry = {}
        if t1:
            entry["team1"] = t1
        if t2:
            entry["team2"] = t2
        if entry:
            config[f"match_{match_num}"] = entry

    # Winners for every round (teams of later rounds are propagated)
    for match_num, _, _ in _ALL_KO_MATCHES:
        winner = st.session_state.get(f"adm_win_{match_num}", _EMPTY)
        if winner and winner != _EMPTY:
            config.setdefault(f"match_{match_num}", {})["winner"] = winner

    return config


def tab_knockout_config():
    """Admin tab: fully configurable knockout bracket (the real reference)."""
    st.header("⚙️ Fase Eliminatoria")

    saved_config = load_knockout_config()
    all_teams = sorted({t for teams in GROUPS.values() for t in teams})

    # Always initialize from the saved config, but preserve existing values
    for match_num, _, _ in ROUND_OF_32:
        cfg = saved_config.get(f"match_{match_num}", {})
        st.session_state.setdefault(f"adm_t1_{match_num}", cfg.get("team1", ""))
        st.session_state.setdefault(f"adm_t2_{match_num}", cfg.get("team2", ""))
    for match_num, _, _ in _ALL_KO_MATCHES:
        cfg = saved_config.get(f"match_{match_num}", {})
        st.session_state.setdefault(f"adm_win_{match_num}", cfg.get("winner") or _EMPTY)

    # Build the live bracket from the current widget state
    live_bracket = fill_bracket_from_config(_build_live_config())

    # --- Visual bracket (same component used in the user-facing tab) ---
    bracket_html = generate_full_bracket_html(live_bracket)
    st.html(bracket_html)

    st.divider()

    if st.button("💾 Guardar cuadro real", type="primary"):
        _save_knockout_config()

    def _winner_selector(match_num, container):
        """Render a winner selectbox whose options are the two teams of the match."""
        info = live_bracket.get(match_num, {})
        t1 = info.get("team1")
        t2 = info.get("team2")
        options = [_EMPTY] + [t for t in (t1, t2) if t]

        key = f"adm_win_{match_num}"
        # Reset stale winners that are no longer part of this match
        if st.session_state.get(key) not in options:
            st.session_state[key] = _EMPTY

        t1_lbl = t1 or "?"
        t2_lbl = t2 or "?"
        container.selectbox(
            f"P{match_num}: {t1_lbl} vs {t2_lbl} — Ganador",
            options=options,
            key=key,
        )

    # --- Round of 32: configurable team pairings + winner ---
    st.subheader("⚔️ Dieciseisavos (Round of 32)")
    col_left, col_right = st.columns(2)
    half = len(ROUND_OF_32) // 2
    for i, (match_num, _, _) in enumerate(ROUND_OF_32):
        target = col_left if i < half else col_right
        with target:
            st.markdown(f"**Partido {match_num}**")
            c1, c2 = st.columns(2)
            c1.selectbox(
                f"P{match_num} Equipo 1",
                options=[""] + all_teams,
                key=f"adm_t1_{match_num}",
                label_visibility="collapsed",
            )
            c2.selectbox(
                f"P{match_num} Equipo 2",
                options=[""] + all_teams,
                key=f"adm_t2_{match_num}",
                label_visibility="collapsed",
            )
            _winner_selector(match_num, st)
            st.divider()

    # --- Later rounds: propagated teams, configurable winner ---
    for round_title, round_def in _KO_ROUNDS[1:]:
        st.subheader(round_title)
        if len(round_def) > 4:
            col_left, col_right = st.columns(2)
            half = len(round_def) // 2
            for i, (match_num, _, _) in enumerate(round_def):
                _winner_selector(match_num, col_left if i < half else col_right)
        else:
            for match_num, _, _ in round_def:
                _winner_selector(match_num, st)
        st.divider()


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


def _save_knockout_config():
    """Persist the full configurable bracket (R32 pairings + winners per round).

    Note: we intentionally do NOT call st.rerun() here. The save button is
    rendered above the team/winner selectboxes, so a rerun would abort the
    script before those widgets are re-instantiated, causing Streamlit to
    discard their session-state values and leave the admin bracket empty.
    """
    save_knockout_config(_build_live_config())
    st.success("✅ Cuadro real guardado correctamente")


def tab_admin():
    """Admin tab for managing group stage results and knockout configuration."""
    st.header("🔧 Administración")

    # Password protection
    if not _admin_authenticate():
        return

    # Create two sub-tabs
    admin_tab1, admin_tab2 = st.tabs(
        ["⚽ Fase de Grupos", "🏅 Knockout - Configuración Manual"]
    )

    with admin_tab1:
        tab_group_results()

    with admin_tab2:
        tab_knockout_config()
