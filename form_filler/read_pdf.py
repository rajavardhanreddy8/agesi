from pdfminer.high_level import extract_text
import os

pdf_path = r'c:\Users\admin\Documents\outing\agent 4.0\form_filler\documents\Consent Form.pdf'

if os.path.exists(pdf_path):
    text = extract_text(pdf_path)
    print("--- PDF CONTENT START ---")
    print(text)
    print("--- PDF CONTENT END ---")
else:
    print(f"File not found: {pdf_path}")
