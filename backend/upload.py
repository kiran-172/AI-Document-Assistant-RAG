
import json
import uuid
import logging
import re

from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException
from sqlalchemy import text

from backend.database import SessionLocal
from backend.document_loader import extract_text_from_pdf
from backend.text_chunker import split_text_into_chunks
from backend.embeddings import generate_embedding


# --------------------------------------------------
# Logging Configuration
# --------------------------------------------------

logger = logging.getLogger(__name__)


# --------------------------------------------------
# Router Configuration
# --------------------------------------------------

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


# --------------------------------------------------
# Upload Configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

UPLOAD_DIR = PROJECT_ROOT / "documents"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
CHUNK_SIZE = 1024 * 1024  # Read 1 MB at a time

EXPECTED_EMBEDDING_DIMENSIONS = 768


# --------------------------------------------------
# Safe Filename Handling
# --------------------------------------------------

def get_safe_original_filename(filename: str | None) -> str:
    """Return a safe original filename for display."""

    original = (filename or "document.pdf").replace("\\", "/")

    original = original.split("/")[-1]

    # Remove control characters
    original = re.sub(r"[\x00-\x1f\x7f]", "", original)

    original = original.strip()

    if not original:
        original = "document.pdf"

    return original[:255]


# --------------------------------------------------
# PDF Upload API
# --------------------------------------------------

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):

    original_filename = get_safe_original_filename(file.filename)

    extension = Path(original_filename).suffix.lower()

    # Step 1: Validate file extension
    if extension != ".pdf":

        await file.close()

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported currently."
        )

    document_id = str(uuid.uuid4())

    # Generate a unique storage filename
    safe_filename = f"{document_id}.pdf"

    file_path = UPLOAD_DIR / safe_filename

    size = 0

    db = None

    try:

        # --------------------------------------------------
        # Step 2: Save PDF with 20 MB size validation
        # --------------------------------------------------

        with file_path.open("wb") as buffer:

            while True:

                chunk = await file.read(CHUNK_SIZE)

                if not chunk:
                    break

                size += len(chunk)

                if size > MAX_FILE_SIZE:

                    raise HTTPException(
                        status_code=413,
                        detail="File size exceeds the 20 MB limit."
                    )

                buffer.write(chunk)

        # --------------------------------------------------
        # Step 3: Validate Empty File
        # --------------------------------------------------

        if size == 0:

            raise HTTPException(
                status_code=400,
                detail="The uploaded PDF file is empty."
            )

        # --------------------------------------------------
        # Step 4: Validate Actual PDF Content
        # --------------------------------------------------

        with file_path.open("rb") as uploaded_file:

            file_header = uploaded_file.read(1024)

        if b"%PDF-" not in file_header:

            raise HTTPException(
                status_code=400,
                detail="Invalid PDF file. Please upload a valid PDF."
            )

        # --------------------------------------------------
        # Step 5: Extract PDF Text
        # --------------------------------------------------

        extracted_text = extract_text_from_pdf(str(file_path))

        if not extracted_text or not extracted_text.strip():

            raise HTTPException(
                status_code=422,
                detail="No readable text found in the PDF."
            )

        # --------------------------------------------------
        # Step 6: Split Extracted Text into Chunks
        # --------------------------------------------------

        chunks = split_text_into_chunks(
            extracted_text,
            chunk_size=500,
            chunk_overlap=50
        )

        if not chunks:

            raise HTTPException(
                status_code=422,
                detail="Unable to create text chunks from this PDF."
            )

        # --------------------------------------------------
        # Step 7: Connect to PostgreSQL Database
        # --------------------------------------------------

        db = SessionLocal()

        # --------------------------------------------------
        # Step 8: Save Document Metadata
        # --------------------------------------------------

        db.execute(
            text("""
                INSERT INTO documents (
                    id,
                    filename,
                    file_path,
                    content_type,
                    file_size,
                    status
                )
                VALUES (
                    CAST(:document_id AS UUID),
                    :filename,
                    :file_path,
                    :content_type,
                    :file_size,
                    :status
                )
            """),
            {
                "document_id": document_id,
                "filename": original_filename,
                "file_path": str(file_path),
                "content_type": "application/pdf",
                "file_size": size,
                "status": "processing"
            }
        )

        # --------------------------------------------------
        # Step 9: Generate Embeddings and Save Chunks
        # --------------------------------------------------

        for index, chunk in enumerate(chunks):

            embedding = generate_embedding(chunk)

            # Validate embedding dimensions
            if len(embedding) != EXPECTED_EMBEDDING_DIMENSIONS:

                raise ValueError(
                    "Unexpected embedding dimensions."
                )

            # Convert embedding into pgvector format
            embedding_string = (
                "[" + ",".join(str(value) for value in embedding) + "]"
            )

            chunk_metadata = json.dumps({
                "source": safe_filename,
                "chunk_index": index
            })

            db.execute(
                text("""
                    INSERT INTO document_chunks (
                        document_id,
                        chunk_index,
                        content,
                        embedding,
                        metadata
                    )
                    VALUES (
                        CAST(:document_id AS UUID),
                        :chunk_index,
                        :content,
                        CAST(:embedding AS vector),
                        CAST(:metadata AS jsonb)
                    )
                """),
                {
                    "document_id": document_id,
                    "chunk_index": index,
                    "content": chunk,
                    "embedding": embedding_string,
                    "metadata": chunk_metadata
                }
            )

        # --------------------------------------------------
        # Step 10: Update Document Status
        # --------------------------------------------------

        db.execute(
            text("""
                UPDATE documents
                SET status = :status
                WHERE id = CAST(:document_id AS UUID)
            """),
            {
                "status": "processed",
                "document_id": document_id
            }
        )

        # --------------------------------------------------
        # Step 11: Commit Database Transaction
        # --------------------------------------------------

        db.commit()

        # --------------------------------------------------
        # Step 12: Return Upload Response
        # --------------------------------------------------

        return {
            "message": "PDF uploaded and processed successfully",
            "document_id": document_id,
            "filename": original_filename,
            "stored_filename": safe_filename,
            "file_size": size,
            "total_chunks": len(chunks),
            "embeddings_dimensions": EXPECTED_EMBEDDING_DIMENSIONS,
            "status": "processed"
        }

    # --------------------------------------------------
    # HTTP Exception Handling
    # --------------------------------------------------

    except HTTPException:

        if db is not None:
            db.rollback()

        file_path.unlink(missing_ok=True)

        raise

    # --------------------------------------------------
    # General Exception Handling
    # --------------------------------------------------

    except Exception:

        if db is not None:
            db.rollback()

        logger.exception(
            "Document processing failed. Document ID: %s",
            document_id
        )

        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail="Document processing failed. Please try again."
        )

    # --------------------------------------------------
    # Resource Cleanup
    # --------------------------------------------------

    finally:

        if db is not None:
            db.close()

        await file.close()
