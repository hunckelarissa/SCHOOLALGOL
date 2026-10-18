@echo off
REM ALG / SCHOOLALGOL run wrapper (.alg)
REM Usage: shaya-run.bat <program.alg> --run|--check|--debug [extra args...]
setlocal EnableExtensions EnableDelayedExpansion

set "PROG=%~1"
set "MODE=%~2"
if "%PROG%"=="" (
  echo Usage: shaya-run.bat ^<program.alg^> --run^|--check^|--debug [extra...]
  exit /b 2
)
if "%MODE%"=="" set "MODE=--run"

REM Toolchain home: env from plugin, else folder containing tools\
if defined SHAYA_TOOLCHAIN_HOME (
  set "HOME=%SHAYA_TOOLCHAIN_HOME%"
) else (
  set "HOME=%~dp0.."
)
for %%I in ("%HOME%") do set "HOME=%%~fI"

set "ENGINE_DIR=%HOME%\interpreters\SchoolAlgol"
set "MAIN=%ENGINE_DIR%\main.py"
if not exist "%MAIN%" (
  echo FAIL: не найден SCHOOLALGOL main.py:
  echo   %MAIN%
  echo Укажите Preferences -^> ALG -^> Toolchain home = dropins\schoolalgol-shaya
  echo Затем снова запустите install_dropins.ps1
  exit /b 1
)

REM Python: SHAYA_PYTHON from prefs, else py -3, else python
if defined SHAYA_PYTHON (
  set "PY=%SHAYA_PYTHON%"
) else (
  where py >nul 2>&1
  if not errorlevel 1 (
    set "PY=py -3"
  ) else (
    set "PY=python"
  )
)

set "EXTRA="
shift
shift
:collect
if "%~1"=="" goto run
set "EXTRA=!EXTRA! %1"
shift
goto collect

:run
pushd "%ENGINE_DIR%" >nul
if /I "%MODE%"=="--check" (
  %PY% -u "%MAIN%" "%PROG%" --check !EXTRA!
  set "RC=!ERRORLEVEL!"
) else if /I "%MODE%"=="--debug" (
  echo NOTE: CLI Debug не поддерживается для SCHOOLALGOL; выполняется Run.
  echo Используйте Step Debug в Eclipse ^(SHAYDBG^).
  %PY% -u "%MAIN%" "%PROG%" !EXTRA!
  set "RC=!ERRORLEVEL!"
) else if /I "%MODE%"=="--run" (
  %PY% -u "%MAIN%" "%PROG%" !EXTRA!
  set "RC=!ERRORLEVEL!"
) else (
  echo Неизвестный режим: %MODE%
  echo Ожидается --run, --check или --debug
  set "RC=2"
)
popd >nul
exit /b %RC%
