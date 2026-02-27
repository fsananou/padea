@echo off
chcp 65001 > nul
echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║      BUILD - Lettre de Mission (.exe)                    ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

:: ── Vérification Python ──────────────────────────────────────────────────────
python --version > nul 2>&1
if errorlevel 1 (
    echo  [ERREUR] Python n'est pas installé ou pas dans le PATH.
    echo  Téléchargez-le sur https://www.python.org/downloads/
    echo  (Cochez bien "Add Python to PATH" lors de l'installation)
    pause
    exit /b 1
)

echo  [1/4] Python trouvé.

:: ── Installation des dépendances ─────────────────────────────────────────────
echo  [2/4] Installation des dépendances (reportlab, pyinstaller)...
pip install reportlab pyinstaller --quiet --upgrade
if errorlevel 1 (
    echo  [ERREUR] Echec de l'installation des dépendances.
    pause
    exit /b 1
)
echo       OK.

:: ── Build PyInstaller ────────────────────────────────────────────────────────
echo  [3/4] Compilation de l'exécutable...
pyinstaller ^
    --onefile ^
    --console ^
    --name "LettreDeMission" ^
    --hidden-import reportlab.graphics.barcode.code128 ^
    --hidden-import reportlab.graphics.barcode.common ^
    --hidden-import reportlab.lib.styles ^
    --hidden-import reportlab.platypus ^
    lettre_mission.py

if errorlevel 1 (
    echo  [ERREUR] La compilation a échoué.
    pause
    exit /b 1
)

:: ── Résultat ─────────────────────────────────────────────────────────────────
echo  [4/4] Nettoyage des fichiers temporaires...
if exist build   rmdir /s /q build
if exist LettreDeMission.spec del /f /q LettreDeMission.spec

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║  ✓  BUILD TERMINÉ !                                      ║
echo  ║  📁  Votre exécutable est dans :  dist\LettreDeMission.exe ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.
echo  Copiez "dist\LettreDeMission.exe" où vous le souhaitez.
echo  Il est autonome (pas besoin de Python sur la machine cible).
echo.
pause
