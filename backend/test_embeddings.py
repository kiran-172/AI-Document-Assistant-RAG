print("TEST EMBEDDINGS FILE STARTED")
from backend.embeddings import generate_embedding

sample_text = """
Python is a programming language.
PostgreSQL is a relational database.
"""

try:
    embedding = generate_embedding(sample_text)

    print("\nGEMINI EMBEDDING SUCCESSFUL")
    print("---------------------------")
    print("Model: gemini-embedding-001")
    print("Vector dimensions:", len(embedding))
    print("First 5 values:", embedding[:5])
    print("Embedding generated successfully!")

except Exception as error:
    print("Embedding generation failed:", error)
