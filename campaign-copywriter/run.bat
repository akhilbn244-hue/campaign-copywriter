@echo off
REM ================================================================
REM  run.bat - double-click to start the app.
REM  It opens in your web browser. Keep this black window open while
REM  you use the app; close it when you're done.
REM ================================================================
cd /d "%~dp0"
title AI Campaign Copywriter - running (close this window to stop)

if not exist ".venv\Scripts\activate.bat" (
    echo  Please double-click setup.bat first.
    pause
    exit /b 1
)

REM Streamlit asks for an email the very first time it runs, and waits.
REM Creating this small settings file answers "no thanks" in advance.
if not exist "%USERPROFILE%\.streamlit\credentials.toml" (
    if not exist "%USERPROFILE%\.streamlit" mkdir "%USERPROFILE%\.streamlit"
    > "%USERPROFILE%\.streamlit\credentials.toml" echo [general]
    >> "%USERPROFILE%\.streamlit\credentials.toml" echo email = ""
)

call ".venv\Scripts\activate.bat"
echo  Starting the app... your browser will open in a few seconds.
streamlit run app.py
pause
