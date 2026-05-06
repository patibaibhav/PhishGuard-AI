"""
Single URL Prediction for Phishing Detection
Loads the trained model and predicts whether a URL is phishing or legitimate.
"""

import os
import sys
import joblib
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.feature_engineering import extract_features, FEATURE_NAMES


def load_model():
    """Load trained model from disk."""
    model_path = os.path.join(PROJECT_ROOT, "models", "model.pkl")
    if not os.path.exists(model_path):
        print(f"[!] Model not found at {model_path}")
        print("[!] Run 'python src/train.py' first!")
        sys.exit(1)

    model_data = joblib.load(model_path)
    return model_data


def predict_url(url, model_data=None):
    """
    Predict whether a URL is phishing or legitimate.

    Parameters:
        url (str): URL to analyze
        model_data (dict): Loaded model data (optional, loads from disk if None)

    Returns:
        dict: Prediction results with probability and feature analysis
    """
    if model_data is None:
        model_data = load_model()

    model = model_data['model']
    scaler = model_data['scaler']
    selected_indices = model_data['selected_indices']
    selected_features = model_data['selected_features']

    # --- Pre-flight Validation (Catch blatant garbage strings) ---
    import re
    from urllib.parse import urlparse
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    
    # Reject hostnames with invalid characters (e.g. semicolons, commas, spaces)
    if not hostname or re.search(r'[^a-zA-Z0-9.\-_]', hostname):
        return {
            'url': url,
            'prediction': 'Phishing',
            'is_phishing': True,
            'confidence': 100.0,
            'phishing_probability': 100.0,
            'legitimate_probability': 0.0,
            'risk_factors': ['Malformed or invalid domain name structure (Gibberish)'],
            'risk_level': 'Dangerous',
            'features': {f: 0 for f in selected_features},
            'all_features': {},
            'num_features_used': 0,
        }

    # Extract all 33 features
    features = extract_features(url)

    # Create feature vector in correct order
    feature_vector = np.array([features[name] for name in FEATURE_NAMES])

    # Select GA-optimized features
    feature_vector_selected = feature_vector[selected_indices].reshape(1, -1)

    # Scale
    feature_vector_scaled = scaler.transform(feature_vector_selected)

    # Predict
    prediction = model.predict(feature_vector_scaled)[0]
    probabilities = model.predict_proba(feature_vector_scaled)[0]

    # Interpret
    is_phishing = bool(prediction == 1)
    confidence = probabilities[1] if is_phishing else probabilities[0]

    # Identify key risk factors
    risk_factors = []
    if features.get('has_ip_address', 0): risk_factors.append("Uses IP address instead of domain")
    if features.get('suspicious_tld', 0): risk_factors.append("Suspicious TLD detected (.tk, .ml, etc.)")
    if features.get('has_phishing_keywords', 0) > 2: risk_factors.append(f"Contains {features['has_phishing_keywords']} phishing keywords")
    if features.get('num_at_symbol', 0) > 0: risk_factors.append("Contains @ symbol (redirect trick)")
    if features.get('has_shortener', 0): risk_factors.append("URL shortener detected")
    if not features.get('has_https', 0): risk_factors.append("No HTTPS encryption")
    if features.get('has_redirect', 0): risk_factors.append("Double-slash redirect detected")
    if features.get('has_port', 0): risk_factors.append("Non-standard port used")
    if features.get('num_subdomains', 0) > 3: risk_factors.append(f"Excessive subdomains ({features['num_subdomains']})")
    if features.get('url_length', 0) > 75: risk_factors.append(f"Unusually long URL ({features['url_length']} chars)")
    if features.get('shannon_entropy', 0) > 4.5: risk_factors.append(f"High entropy ({features['shannon_entropy']:.2f}) — may be obfuscated")
    if features.get('has_encoding', 0): risk_factors.append("Contains percent-encoded characters")
    if features.get('url_similarity_score', 1) < 0.3: risk_factors.append("Visually similar to a known brand domain")

    # Build feature details for UI
    feature_details = {}
    for name in selected_features:
        feature_details[name] = features.get(name, 0)

    result = {
        'url': url,
        'prediction': 'Phishing' if is_phishing else 'Legitimate',
        'is_phishing': is_phishing,
        'confidence': round(float(confidence) * 100, 2),
        'phishing_probability': round(float(probabilities[1]) * 100, 2),
        'legitimate_probability': round(float(probabilities[0]) * 100, 2),
        'risk_factors': risk_factors,
        'risk_level': _get_risk_level(probabilities[1]),
        'features': feature_details,
        'all_features': {name: features[name] for name in FEATURE_NAMES},
        'num_features_used': len(selected_features),
    }

    return result


def _get_risk_level(phishing_prob):
    """Categorize risk level."""
    if phishing_prob < 0.2:
        return 'Safe'
    elif phishing_prob < 0.4:
        return 'Low Risk'
    elif phishing_prob < 0.6:
        return 'Medium Risk'
    elif phishing_prob < 0.8:
        return 'High Risk'
    else:
        return 'Dangerous'


# ========================
# CLI TEST
# ========================
if __name__ == "__main__":
    test_urls = [
        ("https://www.google.com", "Should be legitimate"),
        ("https://www.amazon.com/dp/B08N5WRWNW", "Should be legitimate"),
        ("http://paypal-secure-login.tk/verify", "Should be phishing"),
        ("http://192.168.1.1/banking/login", "Should be phishing"),
        ("http://g00gle-security.com/alert/signin", "Should be phishing"),
    ]

    print("\n" + "=" * 70)
    print("  URL PHISHING DETECTION — Prediction Test")
    print("=" * 70)

    model_data = load_model()

    for url, expected in test_urls:
        result = predict_url(url, model_data)
        status = "✓" if (
            (result['is_phishing'] and "phishing" in expected.lower()) or
            (not result['is_phishing'] and "legitimate" in expected.lower())
        ) else "✗"

        print(f"\n  {status} URL: {url}")
        print(f"    Prediction: {result['prediction']} ({result['confidence']:.1f}% confidence)")
        print(f"    Risk Level: {result['risk_level']}")
        if result['risk_factors']:
            print(f"    Risk Factors:")
            for factor in result['risk_factors']:
                print(f"      ⚠ {factor}")

    print("\n" + "=" * 70)
