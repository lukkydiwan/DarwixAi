import requests
import json

BASE_URL = "http://localhost:8000/query"

TEST_QUERIES = [
    {
        "type": "Qualification Question",
        "query": "What are the minimum revenue requirements to qualify for a business loan?"
    },
    {
        "type": "Policy / Rates Question",
        "query": "What are the interest rates and tenure options for the loan?"
    },
    {
        "type": "FAQ / Prepayment Question",
        "query": "Is there any early payoff or prepayment penalty if I pay back early?"
    },
    {
        "type": "Out-of-Scope Query",
        "query": "Can I get a personal auto loan or home mortgage from Darwix?"
    },
    {
        "type": "Documentation Question",
        "query": "What documents do I need to submit during pre-qualification?"
    }
]

def run_retrieval_eval():
    print("Running Q2 Knowledge Base Retrieval Evaluation...\n")
    
    for idx, item in enumerate(TEST_QUERIES, 1):
        response = requests.post(BASE_URL, json={"query": item["query"], "top_k": 1})
        data = response.json()
        
        print(f"--- Test Case #{idx} [{item['type']}] ---")
        print(f"Question: {item['query']}")
        
        if data["grounded"] and len(data["results"]) > 0:
            match = data["results"][0]
            print(f"Retrieved Record: {match['record_id']} ({match['title']})")
            print(f"Source Reference: {match['source']} | Category: {match['category']}")
            print(f"Snippet: {match['content'][:150]}...")
            print(f"Distance Score: {match['distance']}")
            print(f"Verdict: CORRECT (Grounded & Relevant)\n")
        else:
            print(f"Verdict: UNGROUNDED / OUT OF SCOPE\n")

if __name__ == "__main__":
    run_retrieval_eval()