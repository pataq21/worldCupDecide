"""Knockout stage logic: bracket structure, qualification, and team placement."""

from collections import defaultdict
from typing import Dict, List, Optional

from core.data import load_results
from tournament.groups import GROUP_STAGE_MATCHES, GROUPS

# Round of 32 bracket structure (from FIFA official schedule)
# Each entry: (match_number, team1_source, team2_source)
# Sources: "1A" = winner group A, "2A" = runner-up group A, "3ABCDF" = 3rd from pool
ROUND_OF_32 = [
    (73, "2A", "2B"),
    (74, "1E", "3ABCDF"),
    (75, "1F", "2C"),
    (76, "1C", "2F"),
    (77, "1I", "3CDFGH"),
    (78, "2E", "2I"),
    (79, "1A", "3CEFHI"),
    (80, "1L", "3EHIJK"),
    (81, "1D", "3BEFIJ"),
    (82, "1G", "3AEHIJ"),
    (83, "2K", "2L"),
    (84, "1H", "2J"),
    (85, "1B", "3EFGIJ"),
    (86, "1J", "2H"),
    (87, "1K", "3DEIJL"),
    (88, "2D", "2G"),
]

# Round of 16
ROUND_OF_16 = [
    (89, "W74", "W77"),
    (90, "W73", "W75"),
    (91, "W76", "W78"),
    (92, "W79", "W80"),
    (93, "W83", "W84"),
    (94, "W81", "W82"),
    (95, "W86", "W88"),
    (96, "W85", "W87"),
]

QUARTER_FINALS = [
    (97, "W89", "W90"),
    (98, "W93", "W94"),
    (99, "W91", "W92"),
    (100, "W95", "W96"),
]

SEMI_FINALS = [
    (101, "W97", "W98"),
    (102, "W99", "W100"),
]

THIRD_PLACE = [(103, "L101", "L102")]

FINAL = [(104, "W101", "W102")]


def calculate_real_group_standings() -> Dict[str, List[Dict]]:
    """
    Calculate group standings based on real results (from results.json).
    Returns {group_name: [sorted list of team dicts]}.
    """
    results = load_results()
    all_standings = {}

    for group_name, teams in GROUPS.items():
        standings = defaultdict(
            lambda: {
                "team": "",
                "played": 0,
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "goals_for": 0,
                "goals_against": 0,
            }
        )
        for team in teams:
            standings[team]["team"] = team

        group_matches = [m for m in GROUP_STAGE_MATCHES if m["group"] == group_name]
        for match in group_matches:
            result = results.get(match["id"])
            if not result or not isinstance(result, dict):
                continue
            g1 = result.get("goals1")
            g2 = result.get("goals2")
            if g1 is None or g2 is None:
                continue

            team1 = match["team1"]
            team2 = match["team2"]
            standings[team1]["played"] += 1
            standings[team2]["played"] += 1
            standings[team1]["goals_for"] += g1
            standings[team1]["goals_against"] += g2
            standings[team2]["goals_for"] += g2
            standings[team2]["goals_against"] += g1

            if g1 > g2:
                standings[team1]["wins"] += 1
                standings[team2]["losses"] += 1
            elif g1 < g2:
                standings[team1]["losses"] += 1
                standings[team2]["wins"] += 1
            else:
                standings[team1]["draws"] += 1
                standings[team2]["draws"] += 1

        sorted_standings = sorted(
            standings.values(),
            key=lambda x: (
                x["wins"] * 3 + x["draws"],
                x["goals_for"] - x["goals_against"],
                x["goals_for"],
            ),
            reverse=True,
        )
        all_standings[group_name] = sorted_standings

    return all_standings


def is_group_complete(group_name: str) -> bool:
    """Check if all matches in a group have results."""
    results = load_results()
    group_matches = [m for m in GROUP_STAGE_MATCHES if m["group"] == group_name]
    for match in group_matches:
        result = results.get(match["id"])
        if not result or not isinstance(result, dict):
            return False
        if result.get("goals1") is None or result.get("goals2") is None:
            return False
    return True


def get_qualified_teams() -> Dict[str, Optional[str]]:
    """
    Determine which teams qualify from each group.
    Returns dict with keys like "1A", "2A", "3A" mapping to team names (or None).
    Also includes "3rd_qualified" -> list of qualified 3rd-placed groups.
    """
    standings = calculate_real_group_standings()
    qualified = {}

    third_placed = []

    for group_name in sorted(GROUPS.keys()):
        group_standings = standings[group_name]
        complete = is_group_complete(group_name)

        if complete and len(group_standings) >= 3:
            qualified[f"1{group_name}"] = group_standings[0]["team"]
            qualified[f"2{group_name}"] = group_standings[1]["team"]
            third = group_standings[2]
            qualified[f"3{group_name}"] = third["team"]
            pts = third["wins"] * 3 + third["draws"]
            gd = third["goals_for"] - third["goals_against"]
            gf = third["goals_for"]
            third_placed.append((group_name, third["team"], pts, gd, gf))
        else:
            qualified[f"1{group_name}"] = None
            qualified[f"2{group_name}"] = None
            qualified[f"3{group_name}"] = None

    # Rank third-placed teams: by points, then GD, then GF
    third_placed.sort(key=lambda x: (x[2], x[3], x[4]), reverse=True)
    qualified_thirds = third_placed[:8]
    qualified["3rd_qualified_groups"] = [t[0] for t in qualified_thirds]

    return qualified


def _resolve_third_place_pool(pool: str, qualified_groups: List[str]) -> Optional[str]:
    """
    Given a pool like "ABCDF" and the list of qualified 3rd-place groups,
    find which group from the pool actually qualified.
    Returns the group letter or None.
    """
    for group in qualified_groups:
        if group in pool:
            return group
    return None


def _assign_third_place_teams(qualified_3rd_groups: List[str]) -> Dict[int, str]:
    """
    Assign qualified third-place groups to R32 match slots using backtracking
    to ensure each group is used exactly once.
    Returns {match_num: group_letter} for all third-place pool slots.
    """
    # Collect all third-place pool slots from ROUND_OF_32
    pool_slots = []  # [(match_num, slot_idx, pool_str)]
    for match_num, src1, src2 in ROUND_OF_32:
        if src1.startswith("3") and len(src1) > 2:
            pool_slots.append((match_num, 1, src1[1:]))
        if src2.startswith("3") and len(src2) > 2:
            pool_slots.append((match_num, 2, src2[1:]))

    # Sort by most constrained first (fewest options)
    qualified_set = set(qualified_3rd_groups)
    pool_slots.sort(key=lambda x: len([g for g in qualified_set if g in x[2]]))

    assignment: Dict[int, str] = {}

    def _backtrack(idx: int, used: set) -> bool:
        if idx == len(pool_slots):
            return True
        match_num, slot_idx, pool = pool_slots[idx]
        for group in qualified_3rd_groups:
            if group in pool and group not in used:
                used.add(group)
                assignment[match_num] = group
                if _backtrack(idx + 1, used):
                    return True
                used.discard(group)
                del assignment[match_num]
        return False

    _backtrack(0, set())
    return assignment


def fill_bracket() -> Dict[int, Dict]:
    """
    Fill the knockout bracket with team names based on real results.
    Returns {match_number: {"team1": name/None, "team2": name/None, "label1": str, "label2": str}}
    """
    qualified = get_qualified_teams()
    qualified_3rd_groups = qualified.get("3rd_qualified_groups", [])

    # Pre-compute third-place assignments to avoid duplicates
    third_assignment = _assign_third_place_teams(qualified_3rd_groups)

    bracket = {}

    # Resolve Round of 32
    for match_num, src1, src2 in ROUND_OF_32:
        team1 = _resolve_source_v2(src1, qualified, third_assignment, match_num)
        team2 = _resolve_source_v2(src2, qualified, third_assignment, match_num)
        label1 = _source_label(src1)
        label2 = _source_label(src2)
        bracket[match_num] = {
            "team1": team1,
            "team2": team2,
            "label1": label1,
            "label2": label2,
        }

    # Later rounds depend on knockout results (not implemented yet for real results)
    for round_matches in [ROUND_OF_16, QUARTER_FINALS, SEMI_FINALS, THIRD_PLACE, FINAL]:
        for match_num, src1, src2 in round_matches:
            bracket[match_num] = {
                "team1": None,
                "team2": None,
                "label1": _source_label(src1),
                "label2": _source_label(src2),
            }

    return bracket


# --- User bracket prediction logic ---

# Mapping: for each match, which match+slot does the winner go to?
# Format: {match_num: (next_match_num, slot)} where slot is "team1" or "team2"
WINNER_FEEDS_TO: Dict[int, tuple] = {}
LOSER_FEEDS_TO: Dict[int, tuple] = {}

# Build from round definitions
for match_num, src1, src2 in ROUND_OF_16:
    if src1.startswith("W"):
        WINNER_FEEDS_TO[int(src1[1:])] = (match_num, "team1")
    if src2.startswith("W"):
        WINNER_FEEDS_TO[int(src2[1:])] = (match_num, "team2")

for match_num, src1, src2 in QUARTER_FINALS:
    if src1.startswith("W"):
        WINNER_FEEDS_TO[int(src1[1:])] = (match_num, "team1")
    if src2.startswith("W"):
        WINNER_FEEDS_TO[int(src2[1:])] = (match_num, "team2")

for match_num, src1, src2 in SEMI_FINALS:
    if src1.startswith("W"):
        WINNER_FEEDS_TO[int(src1[1:])] = (match_num, "team1")
    if src2.startswith("W"):
        WINNER_FEEDS_TO[int(src2[1:])] = (match_num, "team2")

for match_num, src1, src2 in THIRD_PLACE:
    if src1.startswith("L"):
        LOSER_FEEDS_TO[int(src1[1:])] = (match_num, "team1")
    if src2.startswith("L"):
        LOSER_FEEDS_TO[int(src2[1:])] = (match_num, "team2")

for match_num, src1, src2 in FINAL:
    if src1.startswith("W"):
        WINNER_FEEDS_TO[int(src1[1:])] = (match_num, "team1")
    if src2.startswith("W"):
        WINNER_FEEDS_TO[int(src2[1:])] = (match_num, "team2")


# Define bracket halves for visual layout
# Top half: leads to SF101
LEFT_BRACKET = {
    "r32": [74, 77, 73, 75, 83, 84, 81, 82],
    "r16": [89, 90, 93, 94],
    "qf": [97, 98],
    "sf": [101],
}
# Bottom half: leads to SF102
RIGHT_BRACKET = {
    "r32": [76, 78, 79, 80, 86, 88, 85, 87],
    "r16": [91, 92, 95, 96],
    "qf": [99, 100],
    "sf": [102],
}


def resolve_user_knockout_bracket(
    user_ko_preds: Dict[str, str], real_bracket: Dict[int, Dict]
) -> Dict[int, Dict]:
    """
    Build user's knockout bracket state from their predictions.
    user_ko_preds: {"KO_73": "México", "KO_74": "Inglaterra", ...}
    real_bracket: output of fill_bracket() (R32 teams from real group results)
    Returns: {match_num: {"team1": str|None, "team2": str|None, "winner": str|None}}
    """
    user_bracket = {}

    # Initialize R32 from real bracket
    for match_num, src1, src2 in ROUND_OF_32:
        rb = real_bracket[match_num]
        winner = user_ko_preds.get(f"KO_{match_num}")
        user_bracket[match_num] = {
            "team1": rb["team1"],
            "team2": rb["team2"],
            "label1": rb["label1"],
            "label2": rb["label2"],
            "winner": winner,
        }

    # Initialize later rounds empty
    all_later = ROUND_OF_16 + QUARTER_FINALS + SEMI_FINALS + THIRD_PLACE + FINAL
    for match_num, src1, src2 in all_later:
        user_bracket[match_num] = {
            "team1": None,
            "team2": None,
            "label1": _source_label(src1),
            "label2": _source_label(src2),
            "winner": user_ko_preds.get(f"KO_{match_num}"),
        }

    # Propagate winners through the bracket
    all_matches = ROUND_OF_32 + ROUND_OF_16 + QUARTER_FINALS + SEMI_FINALS
    for match_num, _, _ in all_matches:
        winner = user_bracket[match_num].get("winner")
        if winner:
            # Propagate winner
            if match_num in WINNER_FEEDS_TO:
                next_match, slot = WINNER_FEEDS_TO[match_num]
                user_bracket[next_match][slot] = winner
            # Propagate loser
            if match_num in LOSER_FEEDS_TO:
                t1 = user_bracket[match_num]["team1"]
                t2 = user_bracket[match_num]["team2"]
                loser = t2 if winner == t1 else t1
                if loser:
                    next_match, slot = LOSER_FEEDS_TO[match_num]
                    user_bracket[next_match][slot] = loser

    return user_bracket


def generate_bracket_html(user_bracket: Dict[int, Dict], half: str = "left") -> str:
    """Generate HTML for one half of the bracket."""
    config = LEFT_BRACKET if half == "left" else RIGHT_BRACKET

    def _team_cell(match_num, team, is_winner=False):
        name = team if team else "—"
        cls = "team winner" if is_winner else "team"
        return f'<div class="{cls}">{name}</div>'

    def _match_html(match_num):
        info = user_bracket.get(match_num, {})
        t1 = info.get("team1")
        t2 = info.get("team2")
        winner = info.get("winner")
        w1 = winner == t1 and t1 is not None
        w2 = winner == t2 and t2 is not None
        return (
            f'<div class="match" data-match="{match_num}">'
            f'  <div class="match-num">P{match_num}</div>'
            f"  {_team_cell(match_num, t1, w1)}"
            f"  {_team_cell(match_num, t2, w2)}"
            f"</div>"
        )

    rounds_html = []
    round_names = ["r32", "r16", "qf", "sf"]
    round_labels = ["Dieciseisavos", "Octavos", "Cuartos", "Semifinal"]

    for rnd, label in zip(round_names, round_labels):
        matches = config[rnd]
        matches_html = "\n".join(_match_html(m) for m in matches)
        rounds_html.append(
            f'<div class="round">'
            f'  <div class="round-title">{label}</div>'
            f'  <div class="matches">{matches_html}</div>'
            f"</div>"
        )

    return "\n".join(rounds_html)


def generate_full_bracket_html(user_bracket: Dict[int, Dict]) -> str:
    """Generate complete HTML bracket visualization."""
    left_html = generate_bracket_html(user_bracket, "left")
    right_html = generate_bracket_html(user_bracket, "right")

    # Final and 3rd place
    final_info = user_bracket.get(104, {})
    third_info = user_bracket.get(103, {})

    def _final_match(info, label, match_num):
        t1 = info.get("team1") or "—"
        t2 = info.get("team2") or "—"
        winner = info.get("winner")
        w1 = "winner" if winner == info.get("team1") and info.get("team1") else ""
        w2 = "winner" if winner == info.get("team2") and info.get("team2") else ""
        return (
            f'<div class="final-match">'
            f'  <div class="round-title">{label}</div>'
            f'  <div class="match" data-match="{match_num}">'
            f'    <div class="match-num">P{match_num}</div>'
            f'    <div class="team {w1}">{t1}</div>'
            f'    <div class="team {w2}">{t2}</div>'
            f"  </div>"
            f"</div>"
        )

    final_html = _final_match(final_info, "⭐ FINAL", 104)
    third_html = _final_match(third_info, "🥉 3er Puesto", 103)

    css = """
    <style>
    .bracket-container {
        display: flex;
        justify-content: center;
        align-items: flex-start;
        gap: 10px;
        overflow-x: auto;
        padding: 10px;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 12px;
    }
    .bracket-half {
        display: flex;
        gap: 6px;
        align-items: center;
    }
    .bracket-half.right {
        flex-direction: row-reverse;
    }
    .round {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    .round-title {
        text-align: center;
        font-weight: bold;
        font-size: 11px;
        color: #666;
        margin-bottom: 4px;
    }
    .matches {
        display: flex;
        flex-direction: column;
        gap: 8px;
        justify-content: space-around;
        min-height: 100%;
    }
    .match {
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 3px 6px;
        background: #f8f9fa;
        min-width: 120px;
        position: relative;
    }
    .match-num {
        position: absolute;
        top: -8px;
        left: 4px;
        font-size: 9px;
        color: #999;
        background: white;
        padding: 0 2px;
    }
    .team {
        padding: 2px 4px;
        border-bottom: 1px solid #eee;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .team:last-child {
        border-bottom: none;
    }
    .team.winner {
        font-weight: bold;
        color: #28a745;
        background: #e8f5e9;
    }
    .center-section {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 20px;
        min-width: 140px;
    }
    .final-match .match {
        border-color: #ffd700;
        background: #fffde7;
    }
    </style>
    """

    html = f"""
    {css}
    <div class="bracket-container">
        <div class="bracket-half left">
            {left_html}
        </div>
        <div class="center-section">
            {final_html}
            {third_html}
        </div>
        <div class="bracket-half right">
            {right_html}
        </div>
    </div>
    """
    return html


def _resolve_source(
    src: str,
    qualified: Dict,
    qualified_3rd_groups: List[str],
    used_3rd_groups: Optional[List[str]] = None,
) -> Optional[str]:
    """Resolve a source like '1A', '2B', '3ABCDF' to a team name."""
    if src.startswith("3") and len(src) > 2:
        # Third-place pool
        pool = src[1:]
        # Find which group from pool qualified AND hasn't been used yet
        for group in qualified_3rd_groups:
            if group in pool and (
                used_3rd_groups is None or group not in used_3rd_groups
            ):
                if used_3rd_groups is not None:
                    used_3rd_groups.append(group)
                return qualified.get(f"3{group}")
        return None
    elif src.startswith(("1", "2")):
        return qualified.get(src)
    return None


def _resolve_source_v2(
    src: str, qualified: Dict, third_assignment: Dict[int, str], match_num: int
) -> Optional[str]:
    """Resolve a source using pre-computed third-place assignment."""
    if src.startswith("3") and len(src) > 2:
        group = third_assignment.get(match_num)
        if group:
            return qualified.get(f"3{group}")
        return None
    elif src.startswith(("1", "2")):
        return qualified.get(src)
    return None


def _source_label(src: str) -> str:
    """Human-readable label for a bracket source."""
    if src.startswith("W"):
        return f"Ganador P{src[1:]}"
    elif src.startswith("L"):
        return f"Perdedor P{src[1:]}"
    elif src.startswith("3") and len(src) > 2:
        return f"3º ({'/'.join(src[1:])})"
    elif src.startswith("1"):
        return f"1º Grupo {src[1:]}"
    elif src.startswith("2"):
        return f"2º Grupo {src[1:]}"
