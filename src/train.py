"""
Training Pipeline for URL Phishing Detection

Full pipeline:
1. Load dataset (features.csv)
2. Run Genetic Algorithm for feature selection
3. Train Voting Ensemble with GA-selected features
4. Evaluate and save model
"""

import os
import sys
import json
import warnings
import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    roc_curve, accuracy_score, precision_score, recall_score, f1_score
)
from sklearn.preprocessing import StandardScaler

from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

warnings.filterwarnings('ignore')

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.feature_engineering import FEATURE_NAMES
from src.genetic_algorithm import GeneticAlgorithm, save_ga_results


# ========================
# CONFIGURATION
# ========================

DATA_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "features.csv")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
PLOTS_DIR = os.path.join(PROJECT_ROOT, "plots")

RANDOM_STATE = 42
TEST_SIZE = 0.2


def load_data():
    """Load processed features CSV."""
    print("\n[1/5] Loading dataset...")

    if not os.path.exists(DATA_PATH):
        print(f"  [!] Features file not found: {DATA_PATH}")
        print(f"  [!] Run 'python data/download_datasets.py' first!")
        sys.exit(1)

    df = pd.read_csv(DATA_PATH)
    print(f"  Loaded {len(df)} samples with {len(df.columns)-1} features")
    print(f"  Class distribution:")
    print(f"    Legitimate (0): {(df['label'] == 0).sum()}")
    print(f"    Phishing  (1): {(df['label'] == 1).sum()}")

    X = df.drop('label', axis=1).values
    y = df['label'].values
    feature_names = [col for col in df.columns if col != 'label']

    return X, y, feature_names


def run_genetic_algorithm(X_train, y_train, feature_names):
    """Run GA for feature selection."""
    print("\n[2/5] Running Genetic Algorithm for feature selection...")

    ga = GeneticAlgorithm(
        X_train, y_train, feature_names,
        config={
            'population_size': 40,
            'num_generations': 30,
            'crossover_rate': 0.8,
            'mutation_rate': 0.03,
            'tournament_size': 5,
            'elitism_count': 2,
            'min_features': 5,
            'early_stop_patience': 10,
            'cv_folds': 5,
            'random_seed': RANDOM_STATE,
        }
    )

    results = ga.evolve()

    # Save results
    os.makedirs(MODELS_DIR, exist_ok=True)
    save_ga_results(results, MODELS_DIR)

    return results


def train_ensemble(X_train, X_test, y_train, y_test, selected_indices, feature_names):
    """Train Voting Ensemble with GA-selected features."""
    print("\n[3/5] Training Voting Ensemble...")

    # Subset to GA-selected features
    X_train_sel = X_train[:, selected_indices]
    X_test_sel = X_test[:, selected_indices]
    selected_names = [feature_names[i] for i in selected_indices]

    print(f"  Using {len(selected_indices)} features (selected by GA)")

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_sel)
    X_test_scaled = scaler.transform(X_test_sel)

    # Define individual models
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_split=5,
        class_weight='balanced',
        random_state=RANDOM_STATE,
        n_jobs=-1
    )

    xgb = XGBClassifier(
        n_estimators=200,
        learning_rate=0.1,
        max_depth=8,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=RANDOM_STATE,
        eval_metric='logloss',
        verbosity=0,
        n_jobs=-1
    )

    lgbm = LGBMClassifier(
        n_estimators=200,
        learning_rate=0.1,
        num_leaves=50,
        max_depth=10,
        class_weight='balanced',
        random_state=RANDOM_STATE,
        verbose=-1,
        n_jobs=-1
    )

    # Voting Ensemble (soft voting = probability-based)
    ensemble = VotingClassifier(
        estimators=[
            ('rf', rf),
            ('xgb', xgb),
            ('lgbm', lgbm)
        ],
        voting='soft'
    )

    print("  Training Random Forest + XGBoost + LightGBM ensemble...")
    ensemble.fit(X_train_scaled, y_train)
    print("  Training complete!")

    return ensemble, scaler, X_train_scaled, X_test_scaled, selected_names


def evaluate_model(ensemble, X_test_scaled, y_test, selected_names):
    """Evaluate model performance."""
    print("\n[4/5] Evaluating model...")

    y_pred = ensemble.predict(X_test_scaled)
    y_proba = ensemble.predict_proba(X_test_scaled)[:, 1]

    # Metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_proba)

    print("\n  " + "=" * 50)
    print("  MODEL PERFORMANCE")
    print("  " + "=" * 50)
    print(f"  Accuracy:    {accuracy:.4f}  ({accuracy*100:.2f}%)")
    print(f"  Precision:   {precision:.4f}")
    print(f"  Recall:      {recall:.4f}")
    print(f"  F1-Score:    {f1:.4f}")
    print(f"  ROC-AUC:     {roc_auc:.4f}")
    print("  " + "=" * 50)

    print("\n  Classification Report:")
    print(classification_report(y_test, y_pred,
                                target_names=['Legitimate', 'Phishing']))

    # ---- Individual model performance ----
    print("  Individual Model Performance:")
    for name, model in ensemble.named_estimators_.items():
        pred = model.predict(X_test_scaled)
        acc = accuracy_score(y_test, pred)
        f1_ind = f1_score(y_test, pred)
        print(f"    {name:6s}  ->  Accuracy: {acc:.4f}  |  F1: {f1_ind:.4f}")

    # ---- Generate plots ----
    generate_plots(y_test, y_pred, y_proba, ensemble, selected_names, X_test_scaled)

    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'roc_auc': roc_auc,
    }


def generate_plots(y_test, y_pred, y_proba, ensemble, selected_names, X_test_scaled):
    """Generate evaluation plots."""
    os.makedirs(PLOTS_DIR, exist_ok=True)

    # 1. Confusion Matrix
    fig, ax = plt.subplots(figsize=(8, 6))
    cm = confusion_matrix(y_test, y_pred)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=['Legitimate', 'Phishing'],
                yticklabels=['Legitimate', 'Phishing'], ax=ax)
    ax.set_xlabel('Predicted')
    ax.set_ylabel('Actual')
    ax.set_title('Confusion Matrix')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'confusion_matrix.png'), dpi=150)
    plt.close()

    # 2. ROC Curve
    fig, ax = plt.subplots(figsize=(8, 6))
    fpr, tpr, _ = roc_curve(y_test, y_proba)
    roc_auc = roc_auc_score(y_test, y_proba)
    ax.plot(fpr, tpr, color='#4F46E5', lw=2, label=f'ROC Curve (AUC = {roc_auc:.4f})')
    ax.plot([0, 1], [0, 1], color='gray', lw=1, linestyle='--')
    ax.set_xlabel('False Positive Rate')
    ax.set_ylabel('True Positive Rate')
    ax.set_title('ROC Curve')
    ax.legend(loc='lower right')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'roc_curve.png'), dpi=150)
    plt.close()

    # 3. Feature Importance (from Random Forest)
    fig, ax = plt.subplots(figsize=(10, 8))
    rf_model = ensemble.named_estimators_['rf']
    importances = rf_model.feature_importances_
    indices = np.argsort(importances)

    ax.barh(range(len(indices)), importances[indices], color='#4F46E5')
    ax.set_yticks(range(len(indices)))
    ax.set_yticklabels([selected_names[i] for i in indices])
    ax.set_xlabel('Feature Importance')
    ax.set_title('Feature Importance (Random Forest)')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'feature_importance.png'), dpi=150)
    plt.close()

    print(f"  [+] Plots saved to: {PLOTS_DIR}/")


def save_model(ensemble, scaler, selected_indices, feature_names, metrics, ga_results):
    """Save trained model and metadata."""
    print("\n[5/5] Saving model...")

    os.makedirs(MODELS_DIR, exist_ok=True)

    # Save model
    model_data = {
        'model': ensemble,
        'scaler': scaler,
        'selected_indices': selected_indices,
        'selected_features': [feature_names[i] for i in selected_indices],
        'all_feature_names': feature_names,
        'metrics': metrics,
    }

    model_path = os.path.join(MODELS_DIR, "model.pkl")
    joblib.dump(model_data, model_path)
    print(f"  [+] Model saved to: {model_path}")

    # Save GA fitness history plot
    os.makedirs(PLOTS_DIR, exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    generations = range(1, len(ga_results['history']['best_fitness']) + 1)

    ax1.plot(generations, ga_results['history']['best_fitness'], 'b-', label='Best F1', linewidth=2)
    ax1.plot(generations, ga_results['history']['avg_fitness'], 'r--', label='Avg F1', linewidth=1)
    ax1.set_xlabel('Generation')
    ax1.set_ylabel('F1-Score')
    ax1.set_title('GA Fitness Over Generations')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2.plot(generations, ga_results['history']['num_features_selected'], 'g-', linewidth=2)
    ax2.set_xlabel('Generation')
    ax2.set_ylabel('Number of Features')
    ax2.set_title('Features Selected Over Generations')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'ga_evolution.png'), dpi=150)
    plt.close()
    print(f"  [+] GA evolution plot saved to: {PLOTS_DIR}/ga_evolution.png")

    return model_path


# ========================
# MAIN
# ========================

def main():
    print()
    print("=" * 70)
    print("  URL PHISHING DETECTION -- Training Pipeline")
    print("  Model: Voting Ensemble (RF + XGBoost + LightGBM)")
    print("  Optimization: Genetic Algorithm (Feature Selection)")
    print("=" * 70)

    # Step 1: Load data
    X, y, feature_names = load_data()

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    print(f"  Train: {len(X_train)} samples  |  Test: {len(X_test)} samples")

    # Step 2: Genetic Algorithm
    ga_results = run_genetic_algorithm(X_train, y_train, feature_names)
    selected_indices = ga_results['selected_indices']

    # Step 3: Train ensemble
    ensemble, scaler, X_train_scaled, X_test_scaled, selected_names = \
        train_ensemble(X_train, X_test, y_train, y_test, selected_indices, feature_names)

    # Step 4: Evaluate
    metrics = evaluate_model(ensemble, X_test_scaled, y_test, selected_names)

    # Step 5: Save
    save_model(ensemble, scaler, selected_indices, feature_names, metrics, ga_results)

    print("\n" + "=" * 70)
    print("  [OK] TRAINING COMPLETE")
    print(f"  [OK] Model accuracy: {metrics['accuracy']*100:.2f}%")
    print(f"  [OK] GA selected {len(selected_indices)}/{len(feature_names)} features")
    print("  [OK] Run 'python app/app.py' to start the web interface")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
