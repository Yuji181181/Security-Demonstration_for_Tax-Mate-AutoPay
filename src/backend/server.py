import uuid
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from src.backend.agents import vulnerable_app, secure_app
from src.backend.mock_bank import bank_system
from src.data.invoices import POISONED_INVOICE_TEXT

import time
from collections import deque
from fastapi import Request

app = FastAPI(title="Tax-Mate AutoPay Backend")

# --- Simple In-Memory Rate Limiter ---
class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.timestamps = deque()

    def is_allowed(self) -> bool:
        now = time.time()
        # Remove timestamps older than the window
        while self.timestamps and now - self.timestamps[0] > self.window_seconds:
            self.timestamps.popleft()
        
        if len(self.timestamps) >= self.max_requests:
            return False
        
        self.timestamps.append(now)
        return True

# Limit to 20 requests per minute per instance
limiter = RateLimiter(max_requests=20, window_seconds=60)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Apply rate limit only to execution endpoints
    if "/run/" in request.url.path:
        if not limiter.is_allowed():
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429, 
                content={"detail": "Too many requests. Please wait a moment."}
            )
    response = await call_next(request)
    return response

class RunRequest(BaseModel):
    invoice_text: Optional[str] = POISONED_INVOICE_TEXT

class ResumeRequest(BaseModel):
    thread_id: str
    action: str  # "approve" or "reject"

@app.post("/reset")
def reset_system():
    bank_system.reset()
    return {"status": "System and Bank reset"}

@app.get("/logs")
def get_logs():
    return {"logs": bank_system.get_logs()}

@app.post("/run/vulnerable")
async def run_vulnerable(req: RunRequest):
    # 脆弱なエージェント: 最後まで一気に実行
    # ステートを持たないため、毎回新しい実行として扱う
    inputs = {"messages": [HumanMessage(content=req.invoice_text)]}
    try:
        # invokeで実行。同期的に完了まで待つ
        result = vulnerable_app.invoke(inputs)
        return {"status": "completed", "final_output": str(result["messages"][-1].content)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run/secure/start")
def start_secure(req: RunRequest):
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    inputs = {"messages": [HumanMessage(content=req.invoice_text)]}
    
    # ガードレール付きエージェントを実行（非同期/中断なしで完了まで実行）
    try:
        result = secure_app.invoke(inputs, config=config)
        final_output = str(result["messages"][-1].content)
        
        # ガードレールがブロックしたかどうかを判定するためにツールコール履歴を確認することも可能だが
        # 基本的に final_output に結果が含まれている
        
        return {
            "status": "completed",
            "thread_id": thread_id,
            "final_output": final_output
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Resume endpoint removed as HITL is replaced by LLM Guardrail

@app.get("/state/{thread_id}")
def get_state(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = secure_app.get_state(config)
    return {
        "values": str(snapshot.values),
        "next": snapshot.next
    }
