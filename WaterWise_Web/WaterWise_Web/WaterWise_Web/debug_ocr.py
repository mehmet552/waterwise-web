
import cv2
import pytesseract
import numpy as np
import os
import re

# Set Tesseract path as in app.py
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def debug_ocr(image_path):
    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        return

    print(f"Processing: {image_path}")
    
    # Load image
    img = cv2.imread(image_path)
    if img is None:
        print("Error: Could not read image.")
        return

    # Preprocessing (Match app.py logic)
    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    text_img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    
    # Run Tesseract
    text = pytesseract.image_to_string(text_img, lang='eng', config='--oem 3 --psm 6')
    
    with open('ocr_result.txt', 'w', encoding='utf-8') as f:
        f.write("--- RAW OCR OUTPUT ---\n")
        f.write(text)
        f.write("\n----------------------\n")
        
        # Test Final Regex (Match app.py)
        pattern_price = r'(?:[OÖoö]denece[kr]|[Tt]oplam|[Gg]enel).*?(?:Tu|Tutar)?.*?(\d+[.,]?\d*)'
        match = re.search(pattern_price, text, re.IGNORECASE | re.DOTALL)
        
        if match:
            f.write(f"SUCCESS: Regex matched Price: {match.group(1)}\n")
        else:
            f.write("FAILURE: Regex did NOT match Price.\n")

    print("OCR finished. Output saved to ocr_result.txt")

# Path to the user uploaded image
img_path = r'C:\Users\Mehmet\.gemini\antigravity\brain\99365229-8d25-4315-9ad4-ea11c90c43a2\uploaded_image_0_1766266419607.jpg'
debug_ocr(img_path)
