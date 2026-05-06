# Claude Project Context: PhishGuard AI

## 1. What This Project Is

This repository is a local AI-powered phishing URL detection system called **PhishGuard AI**. It classifies a URL as either **Legitimate** or **Phishing** using handcrafted URL features, a custom **Genetic Algorithm** for feature selection, and a **soft-voting ensemble** made of:

- Random Forest
- XGBoost
- LightGBM

It also includes a **Flask web application** with a modern frontend and a **QR code scanning** flow so users can upload an image containing a QR code, extract the embedded URL, and run the same phishing analysis on it.

The project is intentionally **local-first**:

- no external phishing APIs
- no DNS/WHOIS lookups
- no page-content scraping
- no remote threat-intelligence dependency during prediction

The entire classification flow operates on the URL string itself.

---

## 2. Current Workspace State

- Workspace path: `e:\D7B_47_sem4\ai mini project`
- This folder is **not a Git repository** right now.
- The project already contains a trained model and generated artifacts:
  - `models/model.pkl`
  - `models/selected_features.json`
  - `plots/confusion_matrix.png`
  - `plots/roc_curve.png`
  - `plots/feature_importance.png`
  - `plots/ga_evolution.png`
- Existing project docs:
  - `README.md`
  - `project_documentation.md`
  - `PhishGuard_AI_Report.md`
  - `PhishGuard_AI_Report.html`

Meaningful repo files:

- `requirements.txt`
- `run_all.bat`
- `test_urls.py`
- `data/download_datasets.py`
- `data/raw/urls.csv`
- `data/processed/features.csv`
- `src/__init__.py`
- `src/utils.py`
- `src/feature_engineering.py`
- `src/genetic_algorithm.py`
- `src/train.py`
- `src/predict.py`
- `src/qr_scanner.py`
- `app/app.py`
- `app/templates/index.html`
- `app/static/style.css`
- `app/static/script.js`

Ignore `__pycache__` files for reasoning.

---

## 3. High-Level Architecture

There are two major flows:

### A. Training Flow

1. Create curated and synthetic URL dataset.
2. Extract 33 numeric features from each URL.
3. Split data into train/test.
4. Run a custom Genetic Algorithm on the training set to select the best feature subset.
5. Train a soft-voting ensemble on the selected features.
6. Evaluate the ensemble.
7. Save the trained model, selected feature metadata, and plots.

### B. Inference Flow

1. User enters a URL in the frontend or uploads a QR code image.
2. If QR image is uploaded, OpenCV decodes the QR content into a URL.
3. Backend normalizes the URL if the scheme is missing.
4. `predict.py` extracts features.
5. Only GA-selected features are kept.
6. Feature vector is scaled.
7. Voting ensemble predicts phishing vs legitimate and class probabilities.
8. Heuristic risk-factor messages are attached.
9. Frontend renders verdict, confidence, risk meter, feature values, and probability bars.

---

## 4. Machine Learning Pipeline

## 4.1 Dataset Creation

File: `data/download_datasets.py`

This file builds the dataset entirely in code.

It contains:

- a long curated list of legitimate URLs
- a long curated list of phishing URLs
- synthetic URL variation generation for both classes

The generator creates examples such as:

- brand impersonation
- suspicious TLD usage
- subdomain abuse
- IP-based URLs
- keyword stuffing
- URL shortener abuse
- encoded URLs
- `@`-symbol tricks
- redirect-like patterns

The script then:

- deduplicates the URLs
- balances both classes
- saves raw labels to `data/raw/urls.csv`
- extracts features for every URL
- saves final feature matrix to `data/processed/features.csv`

### Current observed dataset stats

- Total samples: `750`
- Legitimate samples: `375`
- Phishing samples: `375`
- Feature columns: `33`
- Label column: `1`

So `features.csv` has 34 columns total: 33 features + `label`.

---

## 4.2 Feature Engineering

File: `src/feature_engineering.py`

This is the core feature extractor. It parses a URL using `urllib.parse` and computes **33 handcrafted features**.

### Exact feature names

1. `url_length`
2. `hostname_length`
3. `path_length`
4. `num_dots`
5. `num_hyphens`
6. `num_underscores`
7. `num_slashes`
8. `num_at_symbol`
9. `num_digits`
10. `digit_ratio`
11. `num_special_chars`
12. `has_ip_address`
13. `has_https`
14. `num_subdomains`
15. `suspicious_tld`
16. `has_port`
17. `has_phishing_keywords`
18. `has_brand_name`
19. `shannon_entropy`
20. `vowel_ratio`
21. `consonant_ratio`
22. `longest_word_length`
23. `avg_word_length`
24. `has_redirect`
25. `has_shortener`
26. `has_anchor`
27. `has_encoding`
28. `query_param_count`
29. `query_length`
30. `path_token_count`
31. `tld_in_path`
32. `repeated_chars`
33. `url_similarity_score`

### Feature groups

- Lexical: counts, lengths, digits, punctuation
- Structural: HTTPS, subdomains, ports, redirect-like patterns
- Suspicion heuristics: suspicious TLD, shortener, anchor, encoding, keywords
- Statistical: Shannon entropy, vowel/consonant ratio
- Brand impersonation: similarity to known brand names using edit distance

### Helper constants inside `feature_engineering.py`

- `SUSPICIOUS_TLDS`
- `PHISHING_KEYWORDS`
- `BRAND_NAMES`
- `URL_SHORTENERS`
- `FEATURE_NAMES`

### Important implementation details

- The feature extractor does **not** make network requests.
- IP detection is regex-based.
- Brand similarity is implemented with a normalized Levenshtein distance.
- `has_redirect` checks whether there is a second `//` after the scheme.
- `tld_in_path` checks for tokens like `.com`, `.net`, `.org`, `.php`, `.html`, `.aspx`, `.jsp` inside the path.

### Technical note

`src/utils.py` contains similar helper logic for entropy, Levenshtein, brand similarity, vowel/consonant counts, IP detection, and repeated-character detection, but `feature_engineering.py` mostly duplicates that logic internally instead of importing from `utils.py`.

This means there is some duplication risk between:

- `src/utils.py`
- `src/feature_engineering.py`

---

## 4.3 Genetic Algorithm

File: `src/genetic_algorithm.py`

This is a custom Genetic Algorithm implementation built from scratch. It uses binary chromosomes where each gene corresponds to whether a feature is included.

### Chromosome meaning

- `1` = keep the feature
- `0` = drop the feature

### GA operations

- random population initialization
- tournament selection
- single-point crossover
- bit-flip mutation
- elitism
- early stopping

### Fitness function

The GA does **not** evaluate the full final ensemble during search.

Instead, fitness is computed by:

- taking the selected feature subset
- training a temporary `RandomForestClassifier`
- computing mean cross-validated **F1-score**

So GA optimization is based on Random Forest F1, not direct ensemble performance.

### Config used in this project

- `population_size`: 40
- `num_generations`: 30
- `crossover_rate`: 0.8
- `mutation_rate`: 0.03
- `tournament_size`: 5
- `elitism_count`: 2
- `min_features`: 5
- `early_stop_patience`: 10
- `cv_folds`: 5
- `random_seed`: 42

### Current saved GA results

From `models/selected_features.json`:

- best fitness: `1.0`
- total features: `33`
- selected features: `18`
- dropped features: `15`
- total GA run time: `318.7` seconds
- generations completed before early stop: `11`

### Selected features

- `num_dots`
- `num_hyphens`
- `num_underscores`
- `num_slashes`
- `digit_ratio`
- `has_https`
- `suspicious_tld`
- `has_phishing_keywords`
- `has_brand_name`
- `shannon_entropy`
- `vowel_ratio`
- `longest_word_length`
- `avg_word_length`
- `has_redirect`
- `has_anchor`
- `query_param_count`
- `tld_in_path`
- `url_similarity_score`

### Dropped features

- `url_length`
- `hostname_length`
- `path_length`
- `num_at_symbol`
- `num_digits`
- `num_special_chars`
- `has_ip_address`
- `num_subdomains`
- `has_port`
- `consonant_ratio`
- `has_shortener`
- `has_encoding`
- `query_length`
- `path_token_count`
- `repeated_chars`

---

## 4.4 Final Ensemble

File: `src/train.py`

The final model is a `VotingClassifier` using **soft voting**. That means the three base models contribute probabilities, not just hard labels.

### Base models

#### Random Forest

- `n_estimators=200`
- `max_depth=15`
- `min_samples_split=5`
- `class_weight='balanced'`
- `random_state=42`
- `n_jobs=-1`

#### XGBoost

- `n_estimators=200`
- `learning_rate=0.1`
- `max_depth=8`
- `subsample=0.8`
- `colsample_bytree=0.8`
- `random_state=42`
- `eval_metric='logloss'`
- `verbosity=0`
- `n_jobs=-1`

#### LightGBM

- `n_estimators=200`
- `learning_rate=0.1`
- `num_leaves=50`
- `max_depth=10`
- `class_weight='balanced'`
- `random_state=42`
- `verbose=-1`
- `n_jobs=-1`

### Preprocessing

- Train/test split: `80/20`
- Stratified split: yes
- `random_state=42`
- Feature scaling: `StandardScaler`

Note: scaling is applied even though all three models are tree-based. That is not strictly necessary for tree ensembles, but it is part of the current saved pipeline and must remain consistent with the saved model.

### Saved model contents

`models/model.pkl` stores a dictionary containing:

- `model`
- `scaler`
- `selected_indices`
- `selected_features`
- `all_feature_names`
- `metrics`

---

## 4.5 Current Saved Metrics

From the existing saved model:

- Accuracy: `1.0`
- Precision: `1.0`
- Recall: `1.0`
- F1-score: `1.0`
- ROC-AUC: `1.0`

Observed confusion matrix on the current test split:

- True Legitimate: `75`
- False Phishing on Legitimate: `0`
- False Legitimate on Phishing: `0`
- True Phishing: `75`

### Important caveat

These metrics are likely optimistic because:

- the dataset is curated and partly synthetic
- phishing patterns are generated programmatically
- train/test data likely share strong structural regularities

So the project currently performs perfectly on its internal split, but that should not be treated as a real-world benchmark without external validation.

---

## 5. Inference Logic

File: `src/predict.py`

This is the runtime prediction entry point.

### `load_model()`

- loads `models/model.pkl`
- exits with a message if the model file does not exist

### `predict_url(url, model_data=None)`

Flow:

1. Load model if not provided.
2. Extract `model`, `scaler`, `selected_indices`, `selected_features`.
3. Perform a pre-flight URL validity check.
4. If hostname is missing or contains invalid characters, return a hardcoded phishing result:
   - prediction: `Phishing`
   - confidence: `100%`
   - risk level: `Dangerous`
   - risk factor: malformed or gibberish domain
5. Otherwise, extract all 33 features.
6. Select only GA-approved features.
7. Scale the feature vector.
8. Call `model.predict()` and `model.predict_proba()`.
9. Convert the result into a UI-friendly dictionary.
10. Attach heuristic risk-factor strings.

### Risk-level mapping

Defined by `_get_risk_level(phishing_prob)`:

- `< 0.2` -> `Safe`
- `< 0.4` -> `Low Risk`
- `< 0.6` -> `Medium Risk`
- `< 0.8` -> `High Risk`
- otherwise -> `Dangerous`

### Heuristic risk-factor messages

These are added independently of the model's internal reasoning and are derived from feature thresholds:

- Uses IP address instead of domain
- Suspicious TLD detected
- Contains phishing keywords
- Contains `@` symbol
- URL shortener detected
- No HTTPS encryption
- Double-slash redirect detected
- Non-standard port used
- Excessive subdomains
- Unusually long URL
- High entropy
- Contains percent-encoded characters
- Visually similar to a known brand domain

### Important caveat in current logic

The `url_similarity_score` rule can produce a risk factor even for a legitimate well-known domain like `https://www.google.com`, because low edit distance to a known brand is treated as suspicious. That means the current risk-factor explanation layer can sometimes produce confusing output for truly legitimate brand domains.

This is an explanation-layer issue, not necessarily a classification issue.

---

## 6. QR Scanning

File: `src/qr_scanner.py`

The QR pipeline is intentionally simple:

1. Read uploaded file bytes.
2. Convert bytes to NumPy array.
3. Decode image using OpenCV.
4. Use `cv2.QRCodeDetector().detectAndDecode(img)`.
5. Return the decoded string if present.
6. Return `None` on failure.

There is no multi-QR support, no advanced preprocessing pipeline, and no image persistence. Everything is processed in memory.

---

## 7. Flask Backend

File: `app/app.py`

The backend is a single Flask app.

### Startup behavior

At startup it tries to load the trained model once and keep it in memory in `model_data`.

If model loading fails:

- it logs the error
- sets `model_data = None`

### Routes

#### `GET /`
#### `GET /index`
#### `GET /index.html`

Serves the main HTML UI.

Implementation detail:

- It does **not** currently use `render_template()`.
- It manually opens `app/templates/index.html` and returns the file content.

That is unusual for Flask, but it works for this project.

#### `POST /predict`

Expected JSON body:

```json
{ "url": "https://example.com" }
```

Behavior:

- validates input
- if scheme is missing, prepends `http://`
- calls `predict_url()`
- returns JSON result with `success: true`

Error responses:

- `400` if no URL
- `500` if no model loaded or prediction fails

#### `POST /scan-qr`

Expected form-data:

- key: `file`

Behavior:

- reads uploaded image
- calls `extract_url_from_qr()`
- returns decoded URL if successful

Error cases:

- missing file
- empty filename
- no valid QR detected
- server error during decode

#### `GET /model-info`

Returns model metadata:

- selected features
- number of selected features
- total feature count
- saved metrics

#### `GET /plots/<filename>`

Serves plot images from the `plots` folder.

---

## 8. Frontend UI

Files:

- `app/templates/index.html`
- `app/static/style.css`
- `app/static/script.js`

The frontend is a custom HTML/CSS/JS single-page dashboard.

## 8.1 Main UI Sections

### Header

- app name: `PhishGuard AI`
- badges: `ML Powered`, `GA Optimized`

### Scanner card

- URL text input
- analyze button
- QR upload button
- quick test buttons

Quick test URLs:

- `https://www.google.com`
- `https://www.amazon.com`
- `http://paypal-secure-login.tk/verify`
- `http://192.168.1.1/banking/login`

### Scanning overlay

Shows a 3-step animation:

1. extracting URL features
2. running through GA-selected features
3. ensemble model prediction

### Results section

- verdict card
- confidence ring
- risk meter
- risk factors list
- feature analysis panel
- probability bars
- scan-another button

### Architecture section

Shows:

- `plots/ga_evolution.png`
- `plots/feature_importance.png`

### Tech section

Displays summary cards for:

- Genetic Algorithm
- Random Forest
- XGBoost
- 33 URL Features

### Footer

Mentions Random Forest + XGBoost + LightGBM and Genetic Algorithm.

---

## 8.2 Frontend Behavior

File: `app/static/script.js`

### State

- single boolean: `isScanning`

### Key functions

#### Form submission

- prevents default submit
- calls `scanURL(url)`

#### `testURL(url)`

- inserts one of the quick test URLs
- triggers scan

#### QR upload flow

- listens for file selection on hidden input
- POSTs image to `/scan-qr`
- if decode succeeds, auto-populates input
- immediately calls `scanURL(decoded_url)`

#### `scanURL(url)`

- prevents concurrent scans
- resets previous visual state
- shows loading animation
- performs `/predict` fetch
- calls `renderResults(data)` on success

#### `renderResults(data)`

Updates:

- verdict card styles
- verdict icon and label
- confidence ring animation
- risk meter indicator
- risk-level text color
- risk-factors list
- feature-analysis grid
- probability bars

#### `toggleFeatures()`

- expands/collapses feature-analysis body

#### `resetScanner()`

- clears results and resets UI state

#### Keyboard shortcut

- `Ctrl+K` or `Cmd+K` focuses the URL input

### Feature-analysis rendering

The frontend uses only `data.features`, which corresponds to the **selected feature subset**, not all 33 features.

It highlights some features using hand-coded thresholds:

- suspicious TLD
- phishing keywords
- `@` symbol
- shortener
- redirect
- port
- encoding
- many subdomains
- long URL
- high entropy

It marks some values as safe:

- HTTPS present
- no IP address
- no suspicious TLD

---

## 8.3 Frontend Styling

File: `app/static/style.css`

### Visual style

- premium dark theme
- blurred glassmorphism cards
- neon accent palette
- animated background orbs
- gradients and glow effects
- `Inter` and `JetBrains Mono` from Google Fonts

### Responsive behavior

There are responsive rules for:

- tablet and mobile layout
- stacked header
- column-based input wrapper on smaller screens
- single-column feature grid on smaller screens
- 2-column tech grid on narrower screens
- single-column architecture images on smaller screens

### UI element groups styled in CSS

- header and badges
- scanner card
- scanning overlay
- verdict card
- confidence ring
- risk meter
- risk factors
- feature analysis
- probability bars
- architecture section
- tech grid
- footer

---

## 9. Known Inconsistencies and Technical Debt

These are important if Claude is going to modify or reason about the codebase.

### 1. UI copy mismatch: 15 vs 18 features

In `app/templates/index.html`, the architecture section text says the GA reduces 33 features down to **15** most predictive traits.

That is stale.

The actual saved model currently uses **18** selected features.

### 2. Encoding / mojibake issues in text

Some strings in HTML, JS, README, and console output show garbled characters such as:

- `â€”`
- `âœ…`
- `âš `

This suggests encoding issues, likely UTF-8 text being interpreted with a different code page in some environments.

### 3. `src/utils.py` is mostly redundant

The project has helper functions in `src/utils.py`, but `src/feature_engineering.py` reimplements much of the same logic internally.

### 4. `requests` is imported in `data/download_datasets.py`

`requests` is listed in `requirements.txt` and imported in dataset prep, but the current dataset generator appears to operate from local hardcoded URL lists and does not actually use `requests`.

### 5. Index route bypasses Flask template rendering

`app/app.py` manually reads and returns the HTML file instead of using `render_template()`.

### 6. Model explanation heuristics are imperfect

The risk-factor list is feature-threshold based and can generate misleading explanations on otherwise legitimate URLs.

### 7. Perfect model metrics are suspiciously strong

The saved metrics are all `1.0`, which strongly suggests the internal dataset is too easy or overly synthetic for real-world claims.

### 8. Very limited testing

There is no formal test suite.

The only explicit test-like file is:

- `test_urls.py`

This file just loads the model and prints predictions for a few example URLs.

---

## 10. Current Example Outputs

Observed predictions from the saved model:

### Legitimate example

URL:

`https://www.google.com`

Observed result:

- prediction: `Legitimate`
- risk level: `Safe`
- phishing probability: `0.04%`

### Phishing example

URL:

`http://paypal-secure-login.tk/verify`

Observed result:

- prediction: `Phishing`
- risk level: `Dangerous`
- phishing probability: `99.98%`

Example risk factors:

- suspicious TLD
- phishing keywords
- no HTTPS

### `@`-symbol phishing example

URL:

`http://www.google.com@evil.com/login`

Observed result:

- prediction: `Phishing`
- risk level: `Dangerous`
- phishing probability: `93.57%`

---

## 11. Command / Run Workflow

### One-click Windows flow

File: `run_all.bat`

It does:

1. `pip install -r requirements.txt`
2. `python data/download_datasets.py`
3. `python src/train.py`
4. `python app/app.py`

### Manual flow

1. Install dependencies
2. Prepare dataset
3. Train model
4. Launch Flask app

Useful commands:

```powershell
pip install -r requirements.txt
python data/download_datasets.py
python src/train.py
python app/app.py
python test_urls.py
```

Web app URL:

`http://localhost:5000`

---

## 12. File-by-File Project Map

### Top-level

- `README.md`: public-facing project summary and quick-start instructions
- `project_documentation.md`: internal descriptive documentation of the project
- `requirements.txt`: Python dependencies
- `run_all.bat`: one-click Windows setup and launch
- `test_urls.py`: simple CLI smoke test for prediction
- `PhishGuard_AI_Report.md`: report draft
- `PhishGuard_AI_Report.html`: printable report

### Data

- `data/download_datasets.py`: dataset generator and feature extraction runner
- `data/raw/urls.csv`: labeled raw URL dataset
- `data/processed/features.csv`: engineered numeric features + labels

### Models

- `models/model.pkl`: saved ensemble model + scaler + metadata
- `models/selected_features.json`: GA output and selected-feature metadata

### Plots

- `plots/confusion_matrix.png`
- `plots/roc_curve.png`
- `plots/feature_importance.png`
- `plots/ga_evolution.png`

### Source

- `src/__init__.py`: package marker
- `src/utils.py`: helper utilities
- `src/feature_engineering.py`: main feature extraction logic
- `src/genetic_algorithm.py`: GA implementation
- `src/train.py`: training, evaluation, save pipeline
- `src/predict.py`: inference logic
- `src/qr_scanner.py`: QR decode helper

### Web app

- `app/app.py`: Flask server
- `app/templates/index.html`: page structure
- `app/static/style.css`: all frontend styling
- `app/static/script.js`: frontend interaction logic

---

## 13. What Claude Should Preserve If It Modifies This Project

If Claude is asked to change the project, these are the important invariants:

- Keep the project **local-first** unless explicitly asked to add network intelligence.
- Preserve the same end-to-end prediction flow unless retraining is intentional.
- If the model changes, keep frontend copy, metrics, and selected-feature counts in sync.
- If features change, retraining is required.
- If `selected_features` changes, update any UI text or docs that mention a hardcoded count.
- Preserve QR upload -> decode -> auto-scan behavior unless intentionally redesigning UX.
- Keep JSON response shape from `/predict` stable unless frontend is updated too.
- Be careful with encoding so UI strings stop showing mojibake.

---

## 14. Recommended Prompt Framing for Claude

If you want Claude to work well on this repo, give it this guidance:

- This is a Python + Flask phishing URL detector.
- The ML pipeline uses 33 handcrafted URL features, GA feature selection, and a soft-voting RF/XGBoost/LightGBM ensemble.
- The current saved model uses 18 selected features.
- The dataset is curated + synthetic and current metrics are perfect on the internal split.
- The frontend includes QR upload and auto-scanning of decoded URLs.
- There are stale UI strings and encoding issues that may need cleanup.
- There is no robust test suite, only `test_urls.py`.
- The repo already contains trained artifacts and plots.

---

## 15. Short Summary

This project is a complete phishing URL detection mini-product:

- synthetic + curated dataset generation
- handcrafted feature extraction
- custom GA feature selection
- ensemble model training
- saved model artifacts and plots
- Flask API
- polished dark-mode frontend
- QR decoding for quishing detection

Its main strengths are modularity, local execution, and end-to-end completeness.

Its main weaknesses are synthetic data reliance, stale UI copy, encoding glitches, duplicate utility logic, and lack of formal testing.

