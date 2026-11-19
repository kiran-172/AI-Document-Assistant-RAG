
from backend.document_loader import extract_text_from_pdf
from backend.text_chunker import split_text_into_chunks

pdf_path = r"E:\AI-Document-Assistant\documents\Bharath_P_Updated_Resume.pdf"

text = extract_text_from_pdf(pdf_path)

chunks = split_text_into_chunks(text)

print("TEXT CHUNKING SUCCESSFUL")
print("Total chunks:", len(chunks))

for i, chunk in enumerate(chunks, start=1):
    print(f"\nCHUNK {i}")
    print(chunk)
