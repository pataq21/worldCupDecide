# World Cup 2026 Data - Group Stage

GROUPS = {
    "A": ["USA", "México", "Uruguay", "Panamá"],
    "B": ["Argentina", "Paraguay", "Perú", "Chile"],
    "C": ["Brasil", "Colombia", "Venezuela", "Ecuador"],
    "D": ["Francia", "Italia", "Holanda", "Dinamarca"],
    "E": ["España", "Portugal", "Alemania", "Polonia"],
    "F": ["Inglaterra", "Gales", "Escocia", "Irlanda del Norte"],
    "G": ["Bélgica", "Suecia", "Czechia", "Turquía"],
    "H": ["Croacia", "Serbia", "Rumania", "Bosnia"],
    "I": ["Japón", "Corea del Sur", "Australia", "Irán"],
    "J": ["Arabia Saudí", "Emiratos Árabes", "Uzbekistán", "Catar"],
    "K": ["Marruecos", "Túnez", "Argelia", "Costa de Marfil"],
    "L": ["Nigeria", "Camerún", "Ghana", "Senegal"],
}

# Generate all group stage matches


def generate_matches():
    """Generates all group stage matches (round-robin format)"""
    matches = []

    for group_name, teams in GROUPS.items():
        # Create all possible matchups for the group
        for i in range(len(teams)):
            for j in range(i + 1, len(teams)):
                matches.append({
                    "id": f"{group_name}_{i}_{j}",
                    "group": group_name,
                    "team1": teams[i],
                    "team2": teams[j],
                    "result": None,  # Will be filled when the match is played
                })

    return matches


GROUP_STAGE_MATCHES = generate_matches()
