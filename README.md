# PhishGuard AI — URL Phishing Detection

An AI-powered URL safety checker that uses Machine Learning and Genetic Algorithm optimization to detect phishing URLs in real-time.

## Features

- **33 URL Features** extracted purely from URL strings (no API calls)
- **Genetic Algorithm** for feature selection — evolves optimal feature subset
- **Voting Ensemble** — Random Forest + XGBoost + LightGBM
- **Premium Web UI** with dark mode, animated risk meter, and feature breakdown
- **QR Code Scanner** — Built-in computer vision to detect and extract malicious URLs hidden inside uploaded QR codes
- **No external APIs** — everything runs locally

## Tech Stack

| Component | Technology |
|-----------|-----------|
| ML Models | scikit-learn, XGBoost, LightGBM |
| Optimization | Custom Genetic Algorithm |
| Backend | Flask (Python) |
| Frontend | HTML5, CSS3, JavaScript |
| Data Processing | Pandas, NumPy |

## Quick Start

### Option 1: One-Click (Windows)
```bash
run_all.bat
```

### Option 2: Step by Step
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download and prepare dataset
python data/download_datasets.py

# 3. Train the model (runs GA + trains ensemble)
python src/train.py

# 4. Launch web app
python app/app.py
```

Then open **http://localhost:5000** in your browser.

## Project Structure

```
├── data/
│   ├── download_datasets.py    # Dataset preparation
│   ├── raw/                    # Raw URL data
│   └── processed/              # Extracted features
├── src/
│   ├── feature_engineering.py  # 33 URL feature extraction
│   ├── genetic_algorithm.py    # GA for feature selection
│   ├── train.py                # Training pipeline
│   ├── predict.py              # Single URL prediction
│   ├── qr_scanner.py           # QR Code image decoding
│   └── utils.py                # Helper functions
├── models/
│   ├── model.pkl               # Trained model
│   └── selected_features.json  # GA-selected features
├── plots/                      # Generated evaluation plots
├── app/
│   ├── app.py                  # Flask web server
│   ├── templates/index.html    # Web UI
│   └── static/                 # CSS + JS
├── requirements.txt
├── run_all.bat
└── README.md
```

## How It Works

### Feature Extraction
33 features are extracted from each URL:
- **Lexical**: URL length, dots, hyphens, digits, special chars
- **Structural**: IP address detection, HTTPS, subdomains, ports
- **Keyword**: Phishing terms, brand impersonation
- **Statistical**: Shannon entropy, vowel/consonant ratios
- **Similarity**: Levenshtein distance to known brands

### QR Code Vision System
- The user uploads an image containing a QR Code via the web dashboard.
- The image bytes are transmitted backend securely without local disk saving via an in-memory buffer.
- `opencv-python` reconstructs the image into an array and algorithmically pinpoints the finder patterns of the QR symbol to decode the text.
- The extracted URL is returned to the frontend and immediately passed into the URL feature analysis model pipeline.

### Genetic Algorithm (Feature Selection)
- Population of 40 chromosomes, each a binary mask over 33 features
- Tournament selection, single-point crossover, bit-flip mutation
- Fitness = 5-fold cross-validation F1-score
- Runs for 30 generations with early stopping
- Typically selects 18-25 most relevant features

### Ensemble Model
Three classifiers combined via soft voting:
1. **Random Forest** (200 trees, balanced weights)
2. **XGBoost** (gradient boosting, 200 estimators)
3. **LightGBM** (leaf-wise growth, 200 estimators)

## Results

Expected performance after GA optimization:
- Accuracy: ≥ 95%
- F1-Score: ≥ 95%
- ROC-AUC: ≥ 0.98
