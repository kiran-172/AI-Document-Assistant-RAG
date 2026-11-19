
import os
import math

from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY is missing from .env")

# Initialize Gemini client
client = genai.Client(api_key=API_KEY)

MODEL_NAME = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768


def create_embedding(text: str, task_type: str) -> list[float]:

    if not text or not text.strip():
        raise ValueError("Text cannot be empty")

    result = client.models.embed_content(
        model=MODEL_NAME,
        contents=text,
        config=types.EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=EMBEDDING_DIMENSIONS
        )
    )

    embedding = result.embeddings[0].values

    # Normalize embedding vector
    magnitude = math.sqrt(sum(value * value for value in embedding))

    if magnitude == 0:
        raise ValueError("Generated embedding has zero magnitude")

    return [value / magnitude for value in embedding]


# For PDF document chunks
def generate_embedding(text: str) -> list[float]:

    return create_embedding(
        text,
        "RETRIEVAL_DOCUMENT"
    )


# For user questions
def generate_query_embedding(text: str) -> list[float]:

    return create_embedding(
        text,
        "RETRIEVAL_QUERY"
    )
