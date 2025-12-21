"""Test OCR - scan more pages to find financial data"""
import os
os.environ['PATH'] = r'C:\Program Files (x86)\poppler-24.08.0\Library\bin;' + os.environ.get('PATH', '')

import requests
from dotenv import load_dotenv
import pytesseract
from pdf2image import convert_from_bytes
import re

load_dotenv()
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

API_KEY = os.getenv('COMPANIES_HOUSE_API_KEY')
POPPLER_PATH = r'C:\Program Files (x86)\poppler-24.08.0\Library\bin'

def main():
    print("OCR Test - Scanning pages 6-15 for financial data")
    
    doc_url = "https://document-api.company-information.service.gov.uk/document/g8NiUGl0Kc9KLS_yu24XcSlOSOepYZVEMy-iEfd7OfU/content"
    
    print("Downloading PDF...")
    pdf_response = requests.get(doc_url, auth=(API_KEY, ''), headers={'Accept': 'application/pdf'})
    print(f"Size: {len(pdf_response.content)} bytes")
    
    print("\nConverting pages 6-15 to images...")
    images = convert_from_bytes(
        pdf_response.content, 
        first_page=6, 
        last_page=15,
        dpi=150,
        poppler_path=POPPLER_PATH
    )
    print(f"Converted {len(images)} pages")
    
    print("\nRunning OCR...")
    text = ""
    for i, image in enumerate(images):
        page_text = pytesseract.image_to_string(image, lang='eng')
        text += f"\n=== PAGE {i+6} ===\n{page_text}\n"
        print(f"Page {i+6}: {len(page_text)} chars")
    
    print(f"\nTotal: {len(text)} characters")
    
    # Save full text for inspection
    with open('revolut_pages_6_15.txt', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Saved to revolut_pages_6_15.txt")
    
    # Look for numbers
    print("\nSearching for financial figures...")
    
    # Look for pound values
    pound_values = re.findall(r'[?GBP]*[\s]*([0-9,]+(?:\.[0-9]+)?)\s*(?:million|m|000)', text, re.IGNORECASE)
    if pound_values:
        print(f"Found {len(pound_values)} values with million/m/000:")
        for v in pound_values[:10]:
            print(f"  - {v}")
    
    # Look for specific keywords
    keywords = ['revenue', 'turnover', 'total assets', 'net assets', 'profit', 'loss', 'employees']
    for kw in keywords:
        if kw in text.lower():
            print(f"[FOUND] Keyword: {kw}")
            # Find context
            idx = text.lower().find(kw)
            context = text[max(0, idx-20):idx+50]
            safe_context = ''.join(c if ord(c) < 128 else '?' for c in context)
            print(f"  Context: ...{safe_context}...")

if __name__ == "__main__":
    main()
