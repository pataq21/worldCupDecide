@echo off
REM Script para ejecutar la porra del Mundial 2026

echo.
echo   ======================================
echo   ⚽  Porra Mundial 2026
echo   ======================================
echo.

REM Activar el entorno virtual
call .venv\Scripts\activate.bat

REM Ejecutar Streamlit
streamlit run app.py

pause
