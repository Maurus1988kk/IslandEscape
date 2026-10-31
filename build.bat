@echo off
rem ======================================================================
rem  Build di "Fuga dall'Isola Sperduta" -> dist\FugaDallIsola.exe
rem
rem  Uso:  build.bat              (installa, esegue i test, crea l'exe, lo prova)
rem        build.bat --no-test    (salta i test pytest)
rem ======================================================================
setlocal EnableExtensions
cd /d "%~dp0"

set "RUN_TESTS=1"
if /i "%~1"=="--no-test" set "RUN_TESTS=0"

rem ---------------------------------------------------------- 1. Python
set "PYEXE="
py -3.11 -c "import sys" >nul 2>nul
if not errorlevel 1 set "PYEXE=py -3.11"
if not defined PYEXE (
    py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
    if not errorlevel 1 set "PYEXE=py -3"
)
if not defined PYEXE (
    python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
    if not errorlevel 1 set "PYEXE=python"
)
if not defined PYEXE (
    echo ERRORE: serve Python 3.11 o superiore ^(https://www.python.org^).
    goto :fail
)
echo [1/6] Python trovato: %PYEXE%

rem ---------------------------------------------------------- 2. ambiente virtuale
if not exist ".venv\Scripts\python.exe" (
    echo [2/6] Creo l'ambiente virtuale .venv ...
    %PYEXE% -m venv .venv
    if errorlevel 1 goto :fail
) else (
    echo [2/6] Ambiente virtuale gia' presente
)
set "VPY=%~dp0.venv\Scripts\python.exe"

rem ---------------------------------------------------------- 3. dipendenze
echo [3/6] Installo le dipendenze ...
"%VPY%" -m pip install --upgrade pip --quiet
"%VPY%" -m pip install -r requirements.txt --quiet
if errorlevel 1 goto :fail

rem Genera i moduli comtypes della voce di Windows (SAPI), cosi' entrano nell'exe.
"%VPY%" -c "import comtypes.client as cc; cc.CreateObject('SAPI.SpVoice'); from comtypes.gen import SpeechLib"
if errorlevel 1 echo ATTENZIONE: moduli della voce non generati: la lettura vocale potrebbe non funzionare.

"%VPY%" tools\make_icon.py
if errorlevel 1 echo ATTENZIONE: icona non creata, uso quella predefinita.

rem ---------------------------------------------------------- 4. test
if "%RUN_TESTS%"=="1" (
    echo [4/6] Eseguo i test ...
    "%VPY%" -m pytest -q
    if errorlevel 1 (
        echo ERRORE: alcuni test non passano. Build interrotta.
        goto :fail
    )
) else (
    echo [4/6] Test saltati
)

rem ---------------------------------------------------------- 5. PyInstaller
echo [5/6] Creo l'eseguibile con PyInstaller ...
set "ICON_ARG="
if exist "tools\icona.ico" set "ICON_ARG=--icon tools\icona.ico"
"%VPY%" -m PyInstaller --noconfirm --clean --onefile --windowed ^
    --name FugaDallIsola %ICON_ARG% ^
    --hidden-import pyttsx3.drivers ^
    --hidden-import pyttsx3.drivers.sapi5 ^
    --hidden-import pyttsx3.drivers.dummy ^
    --hidden-import comtypes ^
    --hidden-import comtypes.client ^
    --hidden-import comtypes.gen ^
    --hidden-import comtypes.gen.SpeechLib ^
    --collect-submodules comtypes.gen ^
    --hidden-import pythoncom ^
    --hidden-import pywintypes ^
    --hidden-import win32com ^
    --hidden-import win32com.client ^
    main.py
if errorlevel 1 goto :fail
if not exist "dist\FugaDallIsola.exe" goto :fail

rem ---------------------------------------------------------- 6. prova dell'exe
echo [6/6] Provo l'eseguibile (autotest, si apre una finestra per pochi secondi) ...
set "FUGAISOLA_DATA_DIR=%~dp0build\autotest"
if exist "%FUGAISOLA_DATA_DIR%\selftest.txt" del "%FUGAISOLA_DATA_DIR%\selftest.txt"
start "" /wait "dist\FugaDallIsola.exe" --selftest
set "SELFTEST_RC=%errorlevel%"
set "FUGAISOLA_DATA_DIR="
if exist "build\autotest\selftest.txt" (
    type "build\autotest\selftest.txt"
    echo.
)
if not "%SELFTEST_RC%"=="0" (
    echo ERRORE: l'autotest dell'eseguibile non e' riuscito ^(codice %SELFTEST_RC%^).
    goto :fail
)

echo.
echo ======================================================================
echo  FATTO!  L'eseguibile e' in:  dist\FugaDallIsola.exe
echo ======================================================================
endlocal
exit /b 0

:fail
echo.
echo *** Build NON riuscita. Controllare i messaggi qui sopra. ***
endlocal
exit /b 1
