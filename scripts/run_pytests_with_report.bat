@echo off

title "running pytests with report"

pushd %~dp0
cd ..
set cmd_venv_activate=%CD%\.venv\Scripts\activate.bat
set cmd_venv_deactivate=%CD%\.venv\Scripts\deactivate.bat

:ACTIVATE_VENV
call %cmd_venv_activate%
if %ERRORLEVEL% NEQ 0 (GOTO ERROR)

:POETRY_SETUP
poetry install
if %ERRORLEVEL% NEQ 0 (GOTO ERROR)

:START_PYTESTS
pytest tests/ --html=tests/report/full_test_teport.html --self-contained-html
if %ERRORLEVEL% NEQ 0 (GOTO ERROR)

:END
call %cmd_venv_deactivate%
popd
GOTO :eof

:ERROR
title "Failed to run pytests due to error %ERRORLEVEL%"
popd
pause
GOTO :eof
