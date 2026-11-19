
from backend.rag_pipeline import generate_answer

question = "Which programming languages are mentioned in this document?"

try:
    result = generate_answer(
        question,
        top_k=3
    )

    print("\nRAG ANSWER GENERATION SUCCESSFUL")
    print("--------------------------------")

    print("\nQuestion:")
    print(result["question"])

    print("\nAI Answer:")
    print(result["answer"])

    print("\nSources:")

    for source in result["sources"]:
        print("----------------------------")
        print("Filename:", source["filename"])
        print("Chunk:", source["chunk_index"])
        print("Similarity:", source["similarity"])

except Exception as error:
    print("RAG processing failed:", error)
