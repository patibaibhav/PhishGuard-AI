# PhishGuard AI: Project Documentation

This document explains the architecture and contents of the **PhishGuard AI** URL Phishing Detection project. It details the purpose of every file and explains what each function does. The files are presented in chronological order according to the natural workflow and creation process of the project—from environment setup and data collection to model training and the final web interface.

---

## Core Features highlights

- **Mathematical Feature Engineering**: Extracts 33 discrete numerical traits purely from URL strings without 3rd party API lookups.
- **Genetic Algorithm Optimization**: Selects the most predictive properties autonomously to eliminate noise and maximize unseen data generalization.
- **Machine Learning Ensemble**: Fuses Random Forest, XGBoost, and LightGBM prediction outputs for top-grade accuracy.
- **QR Code Scanning Integration**: Contains a dedicated computer vision pipeline to decode user-uploaded QR images locally to thwart hidden "quishing" cyberthreats.
  - *How it operates*: The UI posts image bytes via a hidden HTML form to the backend (`/scan-qr`); these bytes are ingested into a lightweight `numpy` buffer. The `opencv-python` engine then processes this buffer without saving any files to disk, identifies the positional finder patterns of the QR code, extracts the binary payload, decodes the embedded string, and feeds the resulting URL instantly into the Machine Learning prediction pipeline.
- **Modern Full-Stack Web Dashboard**: Packages the complex backend logic into an aesthetic visual framework featuring animated UI confidence gauges and detailed "Risk Factor" contextual flags.

---

## 1. Environment Setup

### `requirements.txt`
**Purpose**: Specifies all the Python dependencies required to run the project. This is the first file created to ensure the environment is correctly set up for data processing, machine learning, and web serving.
- **Key contents**: Lists libraries like `flask`, `pandas`, `scikit-learn`, `xgboost`, `lightgbm`, and `opencv-python-headless` for computer vision routines.

---

## 2. Data Collection & Preparation

### `data/download_datasets.py`
**Purpose**: Prepares and downloads the dataset. It creates programmatic variations of legitimate and phishing URLs to amplify the dataset size, saves the raw data, and subsequently extracts numerical features out from those raw URLs to prepare for model training.
- `generate_dataset_variations()`: Generates thousands of synthetic but realistic URL variations (both legitimate and phishing) based on established patterns (e.g., typosquatting, subdomain abuse, IP padding).
- `create_dataset()`: Combines hardcoded base URLs with generated variations, balances the two classes (legitimate vs phishing), and saves them to `data/raw/urls.csv`.
- `extract_and_save_features(raw_file)`: Iterates over the raw CSV, passes each URL to the feature extraction module, and saves the purely mathematical representation to `data/processed/features.csv`.

---

## 3. Core Feature Engineering

### `src/utils.py`
**Purpose**: Contains independent helper functions that calculate specific mathematical or lexical metrics about strings.
- `shannon_entropy(text)`: Calculates the unpredictability/entropy of a string. High entropy can indicate obfuscation.
- `levenshtein_distance(s1, s2)`: Calculates the minimum number of single-character edits required to change one word into the other.
- `similarity_to_brands(domain)`: Checks how similar a domain name is to known top-tier brand names (uses edit distance). Detects typosquatting (e.g., `paypall.com`).
- `count_vowels(text)` & `count_consonants(text)`: Basic character counters.
- `has_ip_pattern(text)`: Uses regex to detect if text contains a raw IP network address.
- `count_repeated_chars(text)`: Counts sequences of 3 or more repeated characters, a common sign of a randomly generated or suspicious domain.

### `src/feature_engineering.py`
**Purpose**: The core engine that translates a single string URL into exactly 33 numerical features used by the AI model. No external network request is made; it's purely mathematical.
- `_shannon_entropy(text)`, `_levenshtein_distance(s1, s2)`, `_brand_similarity(domain)`, `_count_repeated(text)`: Internal redundancy/wrappers holding logic similar to `utils.py` specifically configured for the module without cross-imports.
- `extract_features(url)`: Safely parses the URL using `urllib` and computes 33 independent features spanning across Lexical (counts, lengths), Keyword (phishing keywords, brand name hits), Structural (HTTPS, IP as host), and Statistical (entropy, consonant ratios) domains. Returns a dictionary.
- `extract_feature_vector(url)`: Wraps `extract_features` to return the features as an ordered list/array.

---

## 4. Artificial Intelligence & Optimization

### `src/genetic_algorithm.py`
**Purpose**: Contains a custom implementation of a Genetic Algorithm (GA). It mimics the process of natural selection to figure out which combination of the 33 extracted features yields the most predictive model. By dropping noisy features, it optimizes the model's accuracy.
- `GeneticAlgorithm (class)`: The main object state encapsulating evolution logic.
  - `__init__(X, y, feature_names, config)`: Configures hyperparameters, establishes population sizes and mutation rates.
  - `initialize_population()`: Generates random initial subsets of features (chromosomes).
  - `calculate_fitness(chromosome)`: Assigns a "fitness" score to a chromosome by training a quick Random Forest on that feature subset and measuring the **F1-Score**.
  - `tournament_selection(population, fitness_scores)`: Randomly picks subsets to compete and select the strongest parent.
  - `crossover(parent1, parent2)`: Combines two parent subsets to create a new "child" feature set.
  - `mutate(chromosome)`: Randomly adds or drops a feature mimicking genetic mutation.
  - `apply_elitism(...)`: Preserves the top absolute best chromosomes into the next generation.
  - `evolve()`: The main loop repeating the simulation for a number of generations to track down the global best feature mask.
- `save_ga_results(results, output_dir)`: Outputs the final identified optimal feature JSON metadata to disk.

### `src/train.py`
**Purpose**: The central pipeline that orchestrates dataset loading, feature optimization, ensemble training, evaluation, and saves the final production model.
- `load_data()`: Loads `features.csv` into memory using Pandas.
- `run_genetic_algorithm(X_train, y_train, feature_names)`: Invokes the GA class to find the best features.
- `train_ensemble(...)`: Subsets the dataset to only include the GA-selected features mapping, standardizes the scales, and trains a Soft Voting Classifier comprising **Random Forest**, **XGBoost**, and **LightGBM**.
- `evaluate_model(...)`: Runs test data through the trained ensemble to calculate Accuracy, Precision, Recall, F1, and AUC.
- `generate_plots(...)`: Utilizing Matplotlib to output Confusion Matrices, ROC Curves, and Feature Importance bar charts to the `plots/` directory.
- `save_model(...)`: Uses `joblib` to pickle the ensemble classifier, the standard scaler, and the exact names/order of the optimized features.
- `main()`: Orchestrates the execution of the entire sequence step-by-step.

---

## 5. Inference & Prediction Core

### `src/predict.py`
**Purpose**: Exposes a clean, robust function to take any user-provided URL and rapidly predict its risk. This acts as the bridge connecting the Backend logic to the saved Model Artifacts.
- `load_model()`: Safe loader validating if the `.pkl` models exist correctly.
- `predict_url(url, model_data)`: Carries out multiple steps:
  1. Performs structural pre-flight validation to catch basic gibberish upfront.
  2. Extracts the 33 mathematical features using `feature_engineering.py`.
  3. Filters down to the subset selected by the Genetic Algorithm during training.
  4. Runs the vector through the Scaler and the Model.
  5. Formats the model's boolean decision and percentage probabilities into a UI-friendly dictionary.
  6. Automatically identifies and attaches English "Risk Factors" explaining *why* it thinks it's a scam.
- `_get_risk_level(phishing_prob)`: Helper classifying continuous percentage probabilities into "Safe", "Low Risk", "Medium Risk", "High Risk", or "Dangerous" categories.

### `src/qr_scanner.py`
**Purpose**: An independent feature module handling computer vision. Decodes user-uploaded QR code images to extract hidden URLs.
- `extract_url_from_qr(file_bytes)`: Converts incoming raw image bytes into an OpenCV matrix, detects the QR code boundary, and decodes the embedded text (URL) to be passed into the prediction engine.

### `test_urls.py`
**Purpose**: A simple command-line interface script for quickly validating the prediction framework works.
- `main()`: Feeds a static array of mock Phishing and Mock Safe websites into the `predict_url` engine and prints the verdicts exactly as a backend server would see them.

---

## 6. Full Stack Web Application

### `app/app.py`
**Purpose**: The backend HTTP web server powered by Flask. It serves the webpages and listens to API predictions requested by users interacting with the page.
- `serve_plots(filename)`: Route exposing previously generated data science plots to the frontend dashboard.
- `index()`: The root route that serves the base `index.html` UI markup.
- `predict()`: The asynchronous JSON API route mapping the HTTP request to the internal `predict_url` engine from `src/predict.py`. Returns prediction dictionaries.
- `scan_qr()`: The JSON API route handling QR code image uploads, passing them to the vision module, and returning extracted URLs.
- `model_info()`: Returns metadata details (like what features the Genetic Algorithm locked onto) useful for the UI dashboard.

### `app/templates/index.html` & `app/static/style.css`
**Purpose**: The structure and design aesthetics of the web application. Features a modern dark UI pattern, animated visual gauges, and risk grids.

### `app/static/script.js`
**Purpose**: Client-side logic for the user interface.
- `scanURL(url)`: Prevents overlapping clicks, fires UI load animations, requests the URL prediction from `/predict`, and pipes the returned JSON object into rendering.
- Utilities & Animations (`animateStep`, `renderResults`, `animateCounter`): In charge of the visual flares like incrementing the confidence level pie chart, rendering risk text to appropriate colors, and printing out detected risk factors.

---

## 7. Deployment & Documentation

### `run_all.bat`
**Purpose**: Windows batch script designed for extreme ease-of-use deployment.
- Automates and chains sequentially: the dependency installation -> dataset compilation -> GA model training -> launching the active web server.

### `README.md`
**Purpose**: Standard open-source markdown representation detailing what the repository does, the tech stack (Flask, LightGBM, Custom GA), expected performance, and instructions on executing `run_all.bat`.
