from fastapi import FastAPI, Query
from pydantic import BaseModel
import chromadb
from chromadb.utils import embedding_functions

app=FastAPI(title="Business Loan Knowledge Base API", description="API for querying the business loan knowledge base.")

chroma_path="D:/CHODER/Drawix/kb/chroma_db"
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

@app.post("/query", response_model=QueryResponse)
def query_kb(payload: QueryRequest):
    results=collection.query(query_texts=[payload.query], n_results=payload.top_k)
    chunks=[]
    grounded=False

    if results and results["ids"] and len(results["ids"][0]) >0:
        for i in range(len(results["ids"][0])):
            distance=results["distances"][0][i]
            if distance < 1.2:
                grounded=True
                chunks.append(ChunkResult(
                    record_id=results["ids"][0][i],
                    title=results["metadatas"][0][i].get("title", ""),
                    category=results["metadatas"][0][i].get("category", ""),
                    content=results["documents"][0][i],
                    source=results["metadatas"][0][i].get("source", ""),
                    distance=round(distance, 4)
                ))

    return QueryResponse(query=payload.query, grounded=grounded, results=chunks)

@app.get("/health")
def health_check():
    return {"status": "ok", "indexed_documents": collection.count()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)