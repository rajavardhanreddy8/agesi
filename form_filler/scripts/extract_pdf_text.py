import pypdf
import sys

def extract_text(pdf_path):
    try:
        reader = pypdf.PdfReader(pdf_path)
        text = ""
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            print(f"--- Page {i+1} ---")
            print(page_text)
            text += page_text + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

if __name__ == "__main__":
    pdf_path = "fill form format.pdf"
    print(f"Extracting text from: {pdf_path}")
    extract_text(pdf_path)
