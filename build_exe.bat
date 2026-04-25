@echo off
:: ============================================================
::  GST Invoice Extractor — Windows .exe Builder
::  Run this once on your Windows machine.
::  Output:  dist\GST_Invoice_Extractor\GST_Invoice_Extractor.exe
:: ============================================================

title GST Invoice Extractor — Build

echo.
echo  ===================================================
echo   GST Invoice Extractor — Building Windows .exe
echo  ===================================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Install from https://python.org
    pause & exit /b 1
)

echo  [1/4] Creating virtual environment...
python -m venv .build_venv
call .build_venv\Scripts\activate.bat

echo  [2/4] Installing dependencies...
pip install --upgrade pip -q
pip install streamlit pdfplumber openpyxl pandas altair pyinstaller -q

echo  [3/4] Running PyInstaller...
pyinstaller gstin_extractor.spec --clean --noconfirm

echo  [4/4] Cleaning up build artefacts...
rmdir /s /q build 2>nul
rmdir /s /q .build_venv 2>nul
del /q *.log 2>nul

echo.
echo  ===================================================
echo   BUILD COMPLETE
echo   Your app is at:
echo   dist\GST_Invoice_Extractor\GST_Invoice_Extractor.exe
echo  ===================================================
echo.
pause
