import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_ollama.chat_models import ChatOllama
from typing import List, Dict
import uuid

# Initialize FastAPI application
app = FastAPI(title="AI Product Owner Agent")

# Configure LangChain with Ollama
llm = ChatOllama(model="llama3:latest")

# Define prompt template for the agent
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an AI-powered Product Owner Assistant. Your goal is to clarify software features and generate documentation. When a user describes a feature:
    1. Analyze the feature and, if vague, ask up to 3 specific clarifying questions.
    2. Update a Markdown document with the provided information, including 'Feature', 'Details', and 'Pending Questions' sections.
    3. Maintain conversation context for iterative refinement.
    Respond in JSON with:
    - 'response': Text with your response or questions.
    - 'markdown': Updated Markdown document.
    If the feature is clear, confirm and update the Markdown without questions."""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])

# Create LangChain chain
chain = prompt | llm

# Store session context in memory (simple in-memory storage for MVP)
sessions: Dict[str, List] = {}

# Pydantic models for input/output validation
class FeatureInput(BaseModel):
    session_id: str | None = None
    feature: str

class AgentOutput(BaseModel):
    session_id: str
    response: str
    markdown: str

# Endpoint to process feature input
@app.post("/process_feature", response_model=AgentOutput)
async def process_feature(input: FeatureInput):
    try:
        # Generate or use session_id
        session_id = input.session_id or str(uuid.uuid4())
        
        # Initialize session if it doesn't exist
        if session_id not in sessions:
            sessions[session_id] = []
        
        # Retrieve session history
        chat_history = sessions[session_id]
        
        # Invoke LangChain chain
        result = await chain.ainvoke({
            "chat_history": chat_history,
            "input": input.feature
        })
        
        # Parse response (assumes Ollama returns valid JSON)
        import json
        output = json.loads(result.content)
        
        # Update history
        chat_history.append(HumanMessage(content=input.feature))
        chat_history.append(AIMessage(content=json.dumps(output)))
        
        # Limit history to avoid token overflow (optional)
        if len(chat_history) > 20:
            chat_history = chat_history[-20:]
        
        # Save updated history
        sessions[session_id] = chat_history
        
        return AgentOutput(
            session_id=session_id,
            response=output["response"],
            markdown=output["markdown"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to clear session (optional)
@app.delete("/clear_session/{session_id}")
async def clear_session(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
        return {"message": f"Session {session_id} deleted"}
    raise HTTPException(status_code=404, detail="Session not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)