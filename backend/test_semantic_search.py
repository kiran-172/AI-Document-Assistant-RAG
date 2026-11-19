
from backend.semantic_search import search_documents

question = "Which programming languages are used in this document?"

try:
    results = search_documents(question, top_k=3)

    print("\nSEMANTIC SEARCH SUCCESSFUL")
    print("--------------------------")
    print("Question:", question)
    print("Matching chunks:", len(results))

    for index, result in enumerate(results, start=1):

        print(f"\nResult {index}")
        print("Filename:", result["filename"])
        print("Chunk index:", result["chunk_index"])
        print("Similarity:", round(float(result["similarity"]), 4))
        print("Content:")
        print(result["content"])

except Exception as error:
    print("Semantic search failed:", error)