
@app.post("/query")
async def query_kb(request: Request):
    payload = await request.json()
    try:
        tool_call = payload["message"]["toolCalls"][0]
        tool_call_id = tool_call["id"]
        
        import json
        arguments = tool_call["function"]["arguments"]
        if isinstance(arguments, str):
            arguments = json.loads(arguments)
        
        user_query = arguments.get("query", "")
        
        results = collection.query(query_texts=[user_query], n_results=3)
        
        valid_chunks = []
        grounded = False
        
        if results and results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                distance = results["distances"][0][i]
                if distance < 1.5:
                    grounded = True
                    valid_chunks.append(results["documents"][0][i])
        
        
        if grounded:
            bot_answer = "\n".join(valid_chunks)
        else:
            bot_answer = "No relevant information found in the knowledge base."
            
        return {
            "results": [
                {
                    "toolCallId": tool_call_id,
                    "result": bot_answer
                }
            ]
        }
    except Exception as e:
        print(f"Error in /query: {e}")
        return {"error": str(e)}
