"""
QR Code Scanner Module
Extracts text (URLs) from uploaded QR code images.
"""
import cv2
import numpy as np

def extract_url_from_qr(file_bytes):
    """
    Decodes a QR code from image bytes and returns the embedded URL.
    
    Parameters:
        file_bytes (bytes): Raw bytes of the uploaded image file.
        
    Returns:
        str: The decoded string (URL) if successful, otherwise None.
    """
    try:
        # Convert bytes to numpy array
        nparr = np.frombuffer(file_bytes, np.uint8)
        
        # Decode image array into OpenCV format
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return None
            
        # Initialize the generic OpenCV QR Code detector
        detector = cv2.QRCodeDetector()
        data, bbox, straight_qrcode = detector.detectAndDecode(img)
        
        # 'data' will be an empty string if no QR code is found
        if data:
            return data.strip()
            
        return None
    except Exception as e:
        print(f"[!] QR Decode Error: {e}")
        return None
