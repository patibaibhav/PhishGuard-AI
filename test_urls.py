import sys
import os
import json

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.predict import load_model, predict_url

def main():
    print("Loading optimized GA model...")
    model = load_model()
    
    test_urls = [
        "https://www.github.com",
        "https://www.netflix.com/browse",
        "https://www.apple.com/iphone",
        "http://secure-login-paypal.tk",
        "http://bofa-update.online/security",
        "https://192.168.1.1/login.php",
        "http://netflix-billing-update.com/login"
    ]
    
    print("\n--- Testing Custom URLs ---")
    for url in test_urls:
        res = predict_url(url, model)
        icon = "[PHISH]" if res['is_phishing'] else "[SAFE]"
        print(f"{icon} {url:40s} => {res['risk_level']} (Prob: {res['phishing_probability']:.2f}%)")
        print(f"    Features Triggered: {', '.join(res['risk_factors'][:2]) if res['risk_factors'] else 'None'}")
        print()

if __name__ == "__main__":
    main()
