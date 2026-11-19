
from backend.embeddings import generate_query_embedding

question = "Which programming languages are used in this document?"

try:
    embedding = generate_query_embedding(question)

    print("\nQUERY EMBEDDING SUCCESSFUL")
    print("--------------------------")
    print("Question:", question)
    print("Model: gemini-embedding-001")
    print("Task type: RETRIEVAL_QUERY")
    print("Vector dimensions:", len(embedding))
    print("First 5 values:", embedding[:5])

except Exception as error:
    print("Query embedding failed:", error)
