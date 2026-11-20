
import time
from uuid import UUID

from sqlalchemy import text

from backend.database import SessionLocal
from backend.embeddings import generate_query_embedding


def search_documents(
    question: str,
    top_k: int = 3,
    document_id: str | None = None,
    user_id: str | None = None
):

    if not question or not question.strip():
        raise ValueError("Search question cannot be empty.")

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    # Validate authenticated user ID
    if not user_id:
        raise ValueError("Authenticated user ID is required.")

    try:
        UUID(user_id)
    except ValueError:
        raise ValueError("Invalid user ID.")

    # Validate optional document ID
    if document_id:
        try:
            UUID(document_id)
        except ValueError:
            raise ValueError("Invalid document ID.")

    # Step 1: Generate query embedding
    embedding_start = time.perf_counter()

    query_embedding = generate_query_embedding(question)

    embedding_time = time.perf_counter() - embedding_start

    print(
        f"[TIMING] Query embedding: {embedding_time:.2f} seconds",
        flush=True
    )

    embedding_string = (
        "[" + ",".join(str(value) for value in query_embedding) + "]"
    )

    db = SessionLocal()

    try:
        # Step 2: Search only the authenticated user's documents
        db_start = time.perf_counter()

        result = db.execute(
            text("""
                SELECT
                    d.filename,
                    c.document_id,
                    c.chunk_index,
                    c.content,
                    1 - (
                        c.embedding <=> CAST(:query_embedding AS vector)
                    ) AS similarity
                FROM document_chunks c
                INNER JOIN documents d
                    ON d.id = c.document_id
                WHERE
                    c.embedding IS NOT NULL

                    AND d.user_id = CAST(:user_id AS UUID)

                    AND (
                        CAST(:document_id AS UUID) IS NULL
                        OR c.document_id = CAST(:document_id AS UUID)
                    )

                ORDER BY
                    c.embedding <=> CAST(:query_embedding AS vector)

                LIMIT :top_k
            """),
            {
                "query_embedding": embedding_string,
                "user_id": user_id,
                "document_id": document_id,
                "top_k": top_k
            }
        )

        search_results = [dict(row) for row in result.mappings()]

        # Debug: Display retrieved document filenames
        print(
            "\n[DEBUG] Retrieved user-specific document sources:",
            flush=True
        )

        for item in search_results:
            print(
                f"Filename: {item['filename']} | "
                f"Chunk: {item['chunk_index']} | "
                f"Similarity: {item['similarity']:.4f}",
                flush=True
            )

        db_time = time.perf_counter() - db_start

        print(
            f"[TIMING] PostgreSQL search: {db_time:.2f} seconds",
            flush=True
        )

        print(
            f"[TIMING] Retrieved chunks: {len(search_results)}",
            flush=True
        )

        return search_results

    finally:
        db.close()
