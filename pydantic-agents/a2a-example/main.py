from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from typing import Optional
import asyncio

# Initialize Pydantic AI agent with Gemini
model = GeminiModel('gemini-2.5-flash', provider='google-vertex')
agent = Agent(model, instructions='Be fun!')

# Create FastAPI instance
app = FastAPI(title="AI Chat API", description="FastAPI with Pydantic AI Agent", version="1.0.0")

# Pydantic models for requests/responses
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    user_message: str

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the AI Chat API! Use /chat to interact with the agent."}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "ready"}

# Chat endpoint using the Pydantic AI agent
@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    try:
        # Run the agent with the user's message
        result = await agent.run(request.message)
        
        return ChatResponse(
            response=result.data,
            user_message=request.message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

# Stream chat endpoint (for streaming responses)
@app.post("/chat/stream")
async def stream_chat(request: ChatRequest):
    try:
        # For streaming, you might want to use Server-Sent Events
        # This is a simple non-streaming version
        result = await agent.run(request.message)
        return {"response": result.data, "user_message": request.message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

# Get agent info
@app.get("/agent/info")
async def get_agent_info():
    return {
        "model": "gemini-2.5-flash",
        "provider": "google-vertex",
        "instructions": "Be fun!",
        "status": "active"
    }

# Example of using the agent with different instructions
@app.post("/chat/custom")
async def chat_with_custom_instructions(request: ChatRequest, instructions: str):
    try:
        # Create a temporary agent with custom instructions
        custom_agent = Agent(model, instructions=instructions)
        result = await custom_agent.run(request.message)
        
        return {
            "response": result.data,
            "user_message": request.message,
            "custom_instructions": instructions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)