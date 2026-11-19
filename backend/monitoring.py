
import time

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from backend.database import engine


def get_database_monitoring():

    start_time = time.perf_counter()

    try:
        with engine.connect() as connection:

            # 1. Database information
            database_info = connection.execute(
                text("""
                    SELECT
                        current_database() AS database_name,
                        version() AS postgres_version,
                        pg_size_pretty(
                            pg_database_size(current_database())
                        ) AS database_size,
                        pg_database_size(
                            current_database()
                        ) AS database_size_bytes
                """)
            ).mappings().one()

            # 2. Database connection statistics
            connection_info = connection.execute(
                text("""
                    SELECT
                        COUNT(*) AS total_connections,
                        COUNT(*) FILTER (
                            WHERE state = 'active'
                        ) AS active_connections,
                        current_setting(
                            'max_connections'
                        )::integer AS max_connections
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                """)
            ).mappings().one()

            # 3. Document statistics
            document_info = connection.execute(
                text("""
                    SELECT
                        COUNT(*) AS total_documents,
                        COUNT(*) FILTER (
                            WHERE status = 'processed'
                        ) AS processed_documents,
                        COUNT(*) FILTER (
                            WHERE status = 'uploaded'
                        ) AS uploaded_documents,
                        COUNT(*) FILTER (
                            WHERE status = 'failed'
                        ) AS failed_documents,
                        COALESCE(
                            SUM(file_size), 0
                        ) AS total_file_size
                    FROM documents
                """)
            ).mappings().one()

            # 4. Chunk and embedding statistics
            chunk_info = connection.execute(
                text("""
                    SELECT
                        COUNT(*) AS total_chunks,
                        COUNT(embedding) AS total_embeddings,
                        COUNT(*) FILTER (
                            WHERE embedding IS NULL
                        ) AS missing_embeddings
                    FROM document_chunks
                """)
            ).mappings().one()

            # 5. Database table sizes
            table_info = connection.execute(
                text("""
                    SELECT
                        pg_size_pretty(
                            pg_total_relation_size('documents')
                        ) AS documents_table_size,
                        pg_size_pretty(
                            pg_total_relation_size('document_chunks')
                        ) AS chunks_table_size
                """)
            ).mappings().one()

            query_time = (
                time.perf_counter() - start_time
            )

            return {
                "status": "connected",

                "database": {
                    "name": database_info["database_name"],
                    "version": database_info["postgres_version"],
                    "size": database_info["database_size"],
                    "size_bytes": database_info["database_size_bytes"]
                },

                "connections": {
                    "total": connection_info["total_connections"],
                    "active": connection_info["active_connections"],
                    "maximum": connection_info["max_connections"]
                },

                "documents": {
                    "total": document_info["total_documents"],
                    "processed": document_info["processed_documents"],
                    "uploaded": document_info["uploaded_documents"],
                    "failed": document_info["failed_documents"],
                    "total_file_size_bytes": document_info["total_file_size"]
                },

                "chunks": {
                    "total": chunk_info["total_chunks"],
                    "embeddings": chunk_info["total_embeddings"],
                    "missing_embeddings": chunk_info["missing_embeddings"]
                },

                "storage": {
                    "documents_table": table_info["documents_table_size"],
                    "chunks_table": table_info["chunks_table_size"]
                },

                "monitoring_query_time_seconds": round(
                    query_time, 4
                )
            }

    except SQLAlchemyError as error:

        print(
            f"[MONITORING ERROR] {error}",
            flush=True
        )

        return {
            "status": "disconnected",
            "error": "Unable to retrieve database monitoring information."
        }
