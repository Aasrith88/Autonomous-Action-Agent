from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn

from langgraph_agent import invoke_support_agent
from setup_db import create_dummy_database

# Initialize database on server startup
create_dummy_database()

app = FastAPI(
    title="Autonomous Order & Refund Action Agent API",
    description="Stateful LangGraph ReAct agent with SQLite tool execution and business policy guardrails.",
    version="1.0"
)

class ChatRequest(BaseModel):
    thread_id: str = Field(default="ticket-001", description="Unique session ID to track conversation memory")
    message: str = Field(description="Customer message or refund request")

class ChatResponse(BaseModel):
    thread_id: str
    tools_executed: list[str]
    agent_response: str

@app.post("/api/v1/support/chat", response_model=ChatResponse)
def support_chat_endpoint(request: ChatRequest):
    try:
        result = invoke_support_agent(
            user_input=request.message,
            thread_id=request.thread_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("Starting LangGraph Action Server on http://127.0.0.1:8001")
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)