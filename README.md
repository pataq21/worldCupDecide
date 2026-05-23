# ⚽ Porra Mundial 2026

Aplicación de porra para el Mundial 2026 con Streamlit. Permite hacer predicciones de resultados (1x2) en los partidos de la fase de grupos y ver la clasificación de usuarios según sus aciertos.

## Características

✅ **Sistema de usuarios** - Crea y gestiona diferentes jugadores
✅ **Predicciones 1x2** - Haz pronósticos para cada partido de la fase de grupos
✅ **Visualización de grupos** - Ve todos los equipos y partidos organizados por grupo
✅ **Clasificación** - Tabla de posiciones con puntos (1 punto por acierto)
✅ **Almacenamiento persistente** - Los datos se guardan automáticamente

## Estructura

- **main.py** - Aplicación principal de Streamlit
- **data.py** - Datos de grupos y partidos del Mundial 2026
- **utils.py** - Funciones auxiliares para manejo de datos y usuarios
- **datos/** - Carpeta donde se almacenan las predicciones y usuarios (JSON)

## Instalación

```bash
uv sync
```

## Ejecutar

```bash
streamlit run main.py
```

La aplicación se abrirá en `http://localhost:8501`

## Cómo usar

1. **Crear usuario**: Haz clic en "Nuevo usuario" en la barra lateral y asigna un nombre
2. **Hacer predicciones**: Ve a la pestaña "Predicciones" y selecciona el resultado para cada partido
3. **Ver grupos**: En "Grupos" puedes ver todos los partidos y tus predicciones
4. **Clasificación**: Consulta la tabla de posiciones en "Clasificación"

## Sistema de puntuación

- 1 punto por cada predicción correcta
- Las predicciones se guardan automáticamente
- Los puntos se calculan en tiempo real

## Mundial 2026 - Estructura

- **12 Grupos** (A-L) con 4 equipos cada uno
- **Total de partidos fase de grupos**: 72 (6 partidos por grupo)
- **Formato**: Todos contra todos dentro de cada grupo
