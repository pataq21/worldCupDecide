from datetime import datetime

import pandas as pd
import streamlit as st

from core.data import get_users, load_predictions, load_results
from tournament.groups import GROUP_STAGE_MATCHES


def _outcome(g1, g2):
    if g1 > g2:
        return "1"
    elif g1 < g2:
        return "2"
    return "X"


def _calc_pts(pred, result):
    if not pred or not isinstance(pred, dict) or not result:
        return None
    pg1, pg2 = pred.get("goals1"), pred.get("goals2")
    rg1, rg2 = result.get("goals1"), result.get("goals2")
    if None in (pg1, pg2, rg1, rg2):
        return None
    if pg1 == rg1 and pg2 == rg2:
        return 3
    if _outcome(pg1, pg2) == _outcome(rg1, rg2):
        return 1
    return 0


_PT_COLORS = {
    3: "background-color: rgba(0, 180, 80, 0.35)",
    1: "background-color: rgba(220, 170, 0, 0.35)",
}

_FIXED_COLS = ["_sort_datetime", "J.", "Gr.", "Fecha", "Partido", "Resultado"]


def tab_results():
    """Tab showing every user's predictions vs actual results — one row per match"""
    st.header("📋 Predicciones vs Resultados")

    users = get_users()
    if not users:
        st.info("Aún no hay usuarios registrados")
        return

    all_predictions = load_predictions()
    all_results = load_results()

    sort_order = st.radio("Ordenar por:", ["Fecha", "Grupo"], horizontal=True)

    rows = []
    style_rows = []

    for match in GROUP_STAGE_MATCHES:
        match_id = match["id"]
        result = all_results.get(match_id)

        sort_datetime = "9999-99-99 99:99"
        date_str = ""
        fecha_espana = match.get("fecha_espana", "") or match.get("date", "")
        hora_espana = match.get("hora_espana", "")
        if fecha_espana:
            dt = datetime.strptime(fecha_espana, "%Y-%m-%d")
            date_str = dt.strftime("%d %b")
            hora_sort = hora_espana.split()[0] if hora_espana else "99:99"
            sort_datetime = f"{fecha_espana} {hora_sort}"

        row = {
            "_sort_datetime": sort_datetime,
            "J.": match.get("match_day") or "—",
            "Gr.": match["group"],
            "Fecha": f"{date_str} {hora_espana}".strip() if date_str else "—",
            "Partido": f"{match['team1']} vs {match['team2']}",
            "Resultado": f"{result['goals1']}-{result['goals2']}" if result else "—",
        }
        style_row = {col: "" for col in _FIXED_COLS}

        for user in users:
            pred = all_predictions.get(user, {}).get(match_id)
            pts = _calc_pts(pred, result)
            row[user] = (
                f"{pred['goals1']}-{pred['goals2']}"
                if pred and isinstance(pred, dict)
                else "—"
            )
            style_row[user] = _PT_COLORS.get(pts, "")

        rows.append(row)
        style_rows.append(style_row)

    df = pd.DataFrame(rows)
    style_df = pd.DataFrame(style_rows)

    if sort_order == "Fecha":
        sorted_idx = df.sort_values("_sort_datetime").index
        df = df.loc[sorted_idx].reset_index(drop=True)
        style_df = style_df.loc[sorted_idx].reset_index(drop=True)

    df = df.drop(columns=["_sort_datetime"])
    style_df = style_df.drop(columns=["_sort_datetime"])

    st.dataframe(
        df.style.apply(lambda _: style_df, axis=None),
        hide_index=True,
        width="stretch",
    )
