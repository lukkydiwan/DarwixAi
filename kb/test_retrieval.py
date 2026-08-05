import os
import chromadb

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")

def run_retrieval_test():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    
    try:
        collection = client.get_collection("business_loan_kb")
    except Exception as e:
        print(f"Error connecting to Chroma collection: {e}")
        return

    queries = [
        "What documents do I need to qualify for a business loan?",
        "Is there a penalty for early payoff or prepayment?",
        "What is the maximum loan amount available?",
        "How long does the approval process take?",
        "Do you accept cryptocurrency for loan repayments?"
    ]

    output_lines = ["# Question 2: Retrieval Testing Results\n"]

    for i, query in enumerate(queries, 1):
        results = collection.query(
            query_texts=[query],
            n_results=1
        )
        
        output_lines.append(f"## Query {i}: {query}")
        
        if results['documents'] and len(results['documents'][0]) > 0:
            chunk = results['documents'][0][0]
            metadata = results['metadatas'][0][0]
            distance = results['distances'][0][0]
            
            output_lines.append(f"- **Retrieved Chunk/Record:** {chunk[:200]}...")
            output_lines.append(f"- **Source Reference:** {metadata.get('source', 'Unknown')} (Category: {metadata.get('category', 'Unknown')})")
            output_lines.append(f"- **Distance (Lower is better):** {distance:.4f}")
            output_lines.append(f"- **Relevance Explanation:** [TODO: Add 1 sentence explaining why this matches]")
            output_lines.append(f"- **Verdict:** Correct / Partially Correct / Incorrect\n")
        else:
            output_lines.append("- **Result:** No relevant chunks found.\n")


    output_path = os.path.join(BASE_DIR, "retrieval_results.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
    
    print(f"Successfully generated 5-query report at: {output_path}")
    print("Open the markdown file to fill in the 'Relevance Explanation' and 'Verdict' fields.")

if __name__ == "__main__":
    run_retrieval_test()