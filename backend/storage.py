
import os
import logging

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")
SUPABASE_BUCKET_NAME = os.getenv(
    "SUPABASE_BUCKET_NAME",
    "pdf-documents"
)

if not SUPABASE_URL or not SUPABASE_SECRET_KEY:
    raise RuntimeError("Supabase environment variables are missing.")

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SECRET_KEY
)


def upload_pdf_to_storage(
    storage_path: str,
    file_content: bytes
) -> str:
    """Upload a PDF to the private Supabase bucket."""

    try:
        supabase.storage.from_(SUPABASE_BUCKET_NAME).upload(
            path=storage_path,
            file=file_content,
            file_options={
                "content-type": "application/pdf",
                "upsert": "false"
            }
        )

        logger.info("PDF uploaded to Supabase: %s", storage_path)

        return storage_path

    except Exception:
        logger.exception("Supabase PDF upload failed.")
        raise


def delete_pdf_from_storage(storage_path: str) -> None:
    """Delete a PDF from Supabase Storage."""

    try:
        supabase.storage.from_(SUPABASE_BUCKET_NAME).remove(
            [storage_path]
        )

        logger.info("PDF deleted from Supabase: %s", storage_path)

    except Exception:
        logger.exception("Supabase PDF deletion failed.")
        raise
