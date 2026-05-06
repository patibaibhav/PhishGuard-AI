"""
Flask Web Server for URL Phishing Detection
Serves the web UI and handles prediction API requests.
"""

import os
import sys
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from flask import Flask, render_template, request, jsonify, send_from_directory
from src.predict import load_model, predict_url

# Set up Flask app with explicit template and static folders
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'templates')
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')
app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)

# Load model once at startup
print("[*] Loading trained model...")
try:
    model_data = load_model()
    print("[+] Model loaded successfully!")
    print(f"[+] Using {model_data.get('selected_features', ['']).__len__()} GA-selected features")
except Exception as e:
    print(f"[!] Error loading model: {e}")
    print("[!] Make sure to run 'python src/train.py' first!")
    model_data = None

PLOTS_DIR = os.path.join(PROJECT_ROOT, "plots")

@app.route('/plots/<path:filename>')
def serve_plots(filename):
    """Serve generated plots."""
    return send_from_directory(PLOTS_DIR, filename)


@app.route('/')
@app.route('/index')
@app.route('/index.html')
def index():
    """Serve the main web page."""
    print("[DEBUG] Index route called")
    try:
        template_path = os.path.join(TEMPLATES_DIR, 'index.html')
        print(f"[DEBUG] Template path: {template_path}")
        print(f"[DEBUG] File exists: {os.path.exists(template_path)}")
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"[DEBUG] Loaded {len(content)} bytes from template")
            return content
    except Exception as e:
        print(f"[ERROR] Failed to load template: {e}")
        print(f"[ERROR] Template dir: {TEMPLATES_DIR}")
        import traceback
        traceback.print_exc()
        return f"<h1>Error loading template</h1><p>{str(e)}</p>", 500


@app.route('/predict', methods=['POST'])
def predict():
    """Handle URL prediction requests."""
    if model_data is None:
        return jsonify({
            'error': 'Model not loaded. Run training first.',
            'success': False
        }), 500

    data = request.get_json()
    url = data.get('url', '').strip()

    if not url:
        return jsonify({
            'error': 'No URL provided',
            'success': False
        }), 400

    # Add scheme if missing
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    try:
        result = predict_url(url, model_data)
        result['success'] = True
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'Prediction error: {str(e)}',
            'success': False
        }), 500


@app.route('/scan-qr', methods=['POST'])
def scan_qr():
    """Handle QR code image uploads and decode them."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part', 'success': False}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file', 'success': False}), 400
        
    try:
        file_bytes = file.read()
        from src.qr_scanner import extract_url_from_qr
        decoded_url = extract_url_from_qr(file_bytes)
        
        if decoded_url:
            return jsonify({'url': decoded_url, 'success': True})
        else:
            return jsonify({'error': 'No valid QR code found in the image. Please ensure the image is clear.', 'success': False}), 400
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Server error during QR decoding', 'success': False}), 500


@app.route('/model-info', methods=['GET'])
def model_info():
    """Return model metadata."""
    if model_data is None:
        return jsonify({'error': 'Model not loaded'}), 500

    info = {
        'selected_features': model_data.get('selected_features', []),
        'num_features': len(model_data.get('selected_features', [])),
        'total_features': len(model_data.get('all_feature_names', [])),
        'metrics': model_data.get('metrics', {}),
    }
    return jsonify(info)


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("  URL Phishing Detection — Web Interface")
    print("  Open http://localhost:5000 in your browser")
    print("=" * 60 + "\n")
    app.run(debug=False, host='0.0.0.0', port=5000)
