import uuid
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from src.backend.agents import vulnerable_app, secure_app, hitl_app
from src.backend.mock_bank import bank_system
from src.backend.context import user_role_var
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
    role: str = "ADMIN"  # "ADMIN" or "READ_ONLY"

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

@app.get("/audit")
def audit_logs():
    return {"anomalies": bank_system.audit_logs()}

@app.post("/run/vulnerable")
async def run_vulnerable(req: RunRequest):
    # Set User Role in Context
    token = user_role_var.set(req.role)
    
    # 脆弱なエージェント: 最後まで一気に実行
    # ステートを持たないため、毎回新しい実行として扱う
    inputs = {"messages": [HumanMessage(content=req.invoice_text)]}
    try:

        # invokeで実行。同期的に完了まで待つ
        # Recursion limitを明示的に指定（デフォルト25だが、無限ループ対策に入れておく）
        result = vulnerable_app.invoke(inputs, {"recursion_limit": 20})
        return {"status": "completed", "final_output": str(result["messages"][-1].content)}
    except Exception as e:
        # GraphRecursionError もここでキャッチされる（ImportError回避のため文字列チェック等も有効だが、
        # ここでは traceback を出してデバッグしやすくしつつ、500エラーの内容をリッチにする）
        # import traceback
        # traceback.print_exc()  # デバッグ用（本番では不要）
        
        # RecursionErrorの場合は、攻撃成功として扱う（ループするほど従順だったとみなす）
        if "Recursion" in type(e).__name__ or "recursion" in str(e).lower():
             return {
                 "status": "completed", 
                 "final_output": "Agent execution stopped due to recursion limit. This usually indicates the agent successfully entered an instruction loop (Attack Successful)."
             }
             

             
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")
    finally:
        user_role_var.reset(token)

@app.post("/run/secure/start")
def start_secure(req: RunRequest):
    # Set User Role in Context
    token = user_role_var.set(req.role)

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
    finally:
        user_role_var.reset(token)

# --- HITL Endpoints (Human-in-the-Loop) ---

@app.post("/run/hitl/start")
def start_hitl(req: RunRequest):
    """HITL付きエージェントを開始"""
    token = user_role_var.set(req.role)
    
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    inputs = {"messages": [HumanMessage(content=req.invoice_text)]}
    
    try:
        result = hitl_app.invoke(inputs, config=config)
        final_output = str(result["messages"][-1].content)
        
        # 承認待ち状態かチェック
        is_pending = any("承認待ち" in str(msg.content) for msg in result["messages"] if hasattr(msg, 'content'))
        
        return {
            "status": "pending_approval" if is_pending else "completed",
            "thread_id": thread_id,
            "final_output": final_output,
            "messages": [{"type": msg.type, "content": str(msg.content)} for msg in result["messages"][-3:]]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        user_role_var.reset(token)

class ApprovalRequest(BaseModel):
    thread_id: str
    approved: bool  # True = 承認, False = 拒否

@app.post("/run/hitl/approve")
def approve_hitl(req: ApprovalRequest):
    """承認待ちの操作を承認または拒否"""
    config = {"configurable": {"thread_id": req.thread_id}}
    
    try:
        # 現在の状態を取得
        snapshot = hitl_app.get_state(config)
        
        if req.approved:
            # 承認: ツールを実行
            # 承認待ちメッセージを削除して、ツール実行を続行
            # 簡易実装: 新しいメッセージで続行を指示
            result = hitl_app.invoke(
                {"messages": [HumanMessage(content="承認されました。処理を続行してください。")]},
                config=config
            )
            return {
                "status": "approved",
                "final_output": str(result["messages"][-1].content)
            }
        else:
            # 拒否: 処理を中止
            return {
                "status": "rejected",
                "final_output": "操作が拒否されました。処理を中止します。"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/state/{thread_id}")
def get_state(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = secure_app.get_state(config)
    return {
        "values": str(snapshot.values),
        "next": snapshot.next
    }
