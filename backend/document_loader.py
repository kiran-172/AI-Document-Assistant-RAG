
from pypdf import PdfReader

def extract_text_from_pdf(file_path, password=None):

    reader = PdfReader(file_path)

    # Check PDF encryption
    if reader.is_encrypted:
        if password is None:
            raise ValueError(
                "This PDF is password-protected. Please provide its password."
            )

        result = reader.decrypt(password)

        if not result:
            raise ValueError("Incorrect PDF password.")

    extracted_text = []

    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""

        extracted_text.append(page_text)

    return "\n".join(extracted_text)