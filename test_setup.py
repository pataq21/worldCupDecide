"""
Script de prueba para verificar que la aplicación está correctamente configurada
"""

import sys
from data import GROUPS, GROUP_STAGE_MATCHES
from utils import register_user, get_users


def test_data():
    """Verify that World Cup data is correct"""
    print("🔍 Verificando datos del Mundial 2026...\n")

    # Verify groups
    print(f"✅ Cantidad de grupos: {len(GROUPS)}")
    assert len(GROUPS) == 12, "Debe haber 12 grupos"

    # Verify teams
    total_teams = sum(len(teams) for teams in GROUPS.values())
    print(f"✅ Total de equipos: {total_teams}")
    assert total_teams == 48, "Debe haber 48 equipos (4 por grupo)"

    # Verify matches
    print(f"✅ Cantidad de partidos: {len(GROUP_STAGE_MATCHES)}")
    assert len(GROUP_STAGE_MATCHES) == 72, "Debe haber 72 partidos (6 por grupo)"

    # Show example group
    print(f"\n📋 Ejemplo - Grupo A:")
    print(f"   Equipos: {', '.join(GROUPS['A'])}")

    matches_a = [m for m in GROUP_STAGE_MATCHES if m['group'] == 'A']
    print(f"   Partidos ({len(matches_a)}):")
    for m in matches_a[:3]:
        print(f"   - {m['team1']} vs {m['team2']}")
    if len(matches_a) > 3:
        print(f"   - ... y {len(matches_a) - 3} más")

    print("\n✅ Todos los datos están correctos!\n")


if __name__ == "__main__":
    try:
        test_data()
        print("🎉 La aplicación está lista para ejecutarse!")
        print("\nPara iniciar la aplicación, ejecuta:")
        print("  streamlit run main.py")
    except AssertionError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        sys.exit(1)
