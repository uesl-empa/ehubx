@echo off
setlocal

cd /d "%~dp0.."

poetry run sphinx-build -b html -E -a docs/source public/html
if errorlevel 1 (
    echo HTML documentation build failed.
    exit /b 1
)

where latexmk >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: latexmk was not found.
    echo Install MiKTeX or TeX Live and ensure latexmk is available on PATH.
    exit /b 1
)

poetry run sphinx-build -M latexpdf docs/source public
if errorlevel 1 (
    echo PDF documentation build failed.
    exit /b 1
)

echo.
echo Documentation successfully built.
