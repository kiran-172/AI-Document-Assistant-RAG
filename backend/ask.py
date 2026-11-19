
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from backend.database import SessionLocal
from backend.rag_pipeline import generate_answer

router = APIRouter(
    prefix="/documents",
    tags=["Document Questions"]
)

class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=3, ge=1, le=10)
    document_id: str | None = None

# 1. Ask questions about documents
@router.post("/ask")
def ask_question(request: QuestionRequest):

    try:
        return generate_answer(
            question=request.question,
            top_k=request.top_k,
            document_id=request.document_id
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:
        print("RAG API error:", str(error))

        raise HTTPException(
            status_code=500,
            detail="Unable to generate an answer. Please try again."
        )

# 2. Get all uploaded documents
@router.get("/list")
def list_documents():

    db = SessionLocal()

    try:
        result = db.execute(
            text("""
                SELECT
                    d.id,
                    d.filename,
                    d.status,
                    d.created_at,
                    COUNT(c.id) AS total_chunks
                FROM documents d
                LEFT JOIN document_chunks c
                    ON d.id = c.document_id
                GROUP BY
                    d.id,
                    d.filename,
                    d.status,
                    d.created_at
                ORDER BY d.created_at DESC
            """)
        )

        documents = []

        for row in result.mappings():
            documents.append({
                "document_id": str(row["id"]),
                "filename": row["filename"],
                "status": row["status"],
                "total_chunks": row["total_chunks"],
                "created_at": row["created_at"].isoformat()
            })

        return {
            "total_documents": len(documents),
            "documents": documents
        }

    except Exception as error:
        print("Document list error:", str(error))

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve uploaded documents."
        )

    finally:
        db.close()

# 3. Get individual document details
@router.get("/details/{document_id}")
def get_document_details(document_id: str):

    db = SessionLocal()

    try:
        # Validate document ID
        try:
            UUID(document_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid document ID."
            )

        # Get document information
        document = db.execute(
            text("""
                SELECT
                    id,
                    filename,
                    content_type,
                    file_size,
                    status,
                    created_at
                FROM documents
                WHERE id = CAST(:document_id AS UUID)
            """),
            {"document_id": document_id}
        ).mappings().first()

        if not document:
            raise HTTPException(
                status_code=404,
                detail="Document not found."
            )

        # Get document chunks
        chunks = db.execute(
            text("""
                SELECT
                    chunk_index,
                    content
                FROM document_chunks
                WHERE document_id = CAST(:document_id AS UUID)
                ORDER BY chunk_index
            """),
            {"document_id": document_id}
        ).mappings().all()

        return {
            "document_id": str(document["id"]),
            "filename": document["filename"],
            "content_type": document["content_type"],
            "file_size": document["file_size"],
            "status": document["status"],
            "created_at": document["created_at"].isoformat(),
            "total_chunks": len(chunks),
            "chunks": [
                {
                    "chunk_index": chunk["chunk_index"],
                    "content_preview": chunk["content"][:300]
                }
                for chunk in chunks
            ]
        }

    except HTTPException:
        raise

    except Exception as error:
        print("Document details error:", str(error))

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve document details."
        )

    finally:
        db.close()