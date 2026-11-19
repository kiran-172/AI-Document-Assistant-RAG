
from backend.document_loader import extract_text_from_pdf

pdf_path = r"E:\AI-Document-Assistant\documents\Bharath_P_Updated_Resume.pdf"

try:
    text = extract_text_from_pdf(pdf_path)

    print("\nPDF EXTRACTION SUCCESSFUL")
    print("-------------------------")
    print(text[:3000])

except Exception as e:
    print("PDF Extraction Failed:", e)
