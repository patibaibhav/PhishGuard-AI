@echo off
echo ============================================================
echo   PhishGuard AI - URL Phishing Detection
echo   One-Click Setup and Launch
echo ============================================================
echo.

REM Step 1: Install dependencies
echo [1/4] Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [!] Failed to install dependencies!
    pause
    exit /b 1
)
echo [+] Dependencies installed!
echo.

REM Step 2: Download and prepare dataset
echo [2/4] Preparing dataset...
python data/download_datasets.py
if %errorlevel% neq 0 (
    echo [!] Failed to prepare dataset!
    pause
    exit /b 1
)
echo [+] Dataset ready!
echo.

REM Step 3: Train the model (GA + Ensemble)
echo [3/4] Training ML model with Genetic Algorithm optimization...
python src/train.py
if %errorlevel% neq 0 (
    echo [!] Training failed!
    pause
    exit /b 1
)
echo [+] Model trained!
echo.

REM Step 4: Launch web app
echo [4/4] Launching web interface...
echo.
echo ============================================================
echo   Open http://localhost:5000 in your browser
echo   Press Ctrl+C to stop the server
echo ============================================================
echo.
python app/app.py
pause
