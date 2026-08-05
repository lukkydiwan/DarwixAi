from fastapi import FastAPI, Query ,Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chromadb
import os
from chromadb.utils import embedding_functions

app=FastAPI(title="Business Loan Knowledge Base API", description="API for querying the business loan knowledge base.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
base_dir=os.path.dirname(os.path.abspath(__file__))
chroma_path=os.path.join(base_dir, "chroma_db")
collection_name="business_loan_kb"

chroma_client=chromadb.PersistentClient(path=chroma_path)
embedding_fn = embedding_functions.DefaultEmbeddingFunction()
collection=chroma_client.get_collection(name=collection_name, embedding_function=embedding_fn)

class QueryRequest(BaseModel):
    query: str
    top_k: int = 2

class ChunkResult(BaseModel):
    record_id: str
    title: str
    content: str
    category: str
    source: str
    distance: float

class QueryResponse(BaseModel):
    query: str
    grounded: bool
    results: list[ChunkResult]

@app.post("/query")
async def query_knowledge_base(request: Request):
    payload = await request.json()
    
    try:
        tool_call = payload["message"]["toolCalls"][0]
        tool_call_id = tool_call["id"]
        
        import json
        arguments = tool_call["function"]["arguments"]
        if isinstance(arguments, str):
            arguments = json.loads(arguments)
        
        user_query = arguments.get("query", "")
        print(f" Searching KB for: '{user_query}'")
        
        results = collection.query(query_texts=[user_query], n_results=3)
        
        valid_chunks = []
        grounded = False
        
        if results and results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                distance = results["distances"][0][i]
                chunk_text = results["documents"][0][i]
                
                
                print(f" Chunk {i+1} Distance: {distance:.4f} | Text: {chunk_text[:50]}...")
                
                
                if distance < 1.7: 
                    grounded = True
                    valid_chunks.append(chunk_text)
        
        if grounded:
            bot_answer = "\n".join(valid_chunks)
            print(" Match found! Sending to bot.")
        else:
            bot_answer = "No relevant information found in the knowledge base."
            print(" No matches below threshold. Triggering fallback.")
            
        return {
            "results": [
                {
                    "toolCallId": tool_call_id,
                    "result": bot_answer
                }
            ]
        }
    except Exception as e:
        print(f" Error in /query: {e}")
        return {"error": str(e)}



@app.get("/health")
def health_check():
    return {"status": "ok", "indexed_documents": collection.count()}

import json
from datetime import datetime

@app.post("/webhook/crm")
async def save_lead(request: Request):
    payload = await request.json()
    
    try:
        tool_call = payload["message"]["toolCalls"][0]
        tool_call_id = tool_call["id"]
        
        import json
        from datetime import datetime
        
        arguments = tool_call["function"]["arguments"]
        if isinstance(arguments, str):
            lead_data = json.loads(arguments)
        else:
            lead_data = arguments
            
        filename = f"kb/data/lead_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(lead_data, f, indent=4)
            
        print(f"Lead successfully saved to {filename}")
        
        return {
            "results": [
                {
                    "toolCallId": tool_call_id,
                    "result": "Success! Lead saved to CRM."
                }
            ]
        }
    except Exception as e:
        print(f"Error in /webhook/crm: {e}")
        return {"error": str(e)}

    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)