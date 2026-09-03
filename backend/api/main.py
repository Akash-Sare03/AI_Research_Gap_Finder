# backend/api/main.py

import os
import shutil
import uvicorn
import re
import json
import traceback
from typing import List, Optional, Dict, Any
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Response, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..core.config import Config
from ..core.auth import (
    user_store,
    create_session_token,
    decode_session_token,
    validate_groq_api_key,
    mask_api_key,
    get_current_user,
    get_current_user_optional,
    get_user_llm_key,
    guest_quota
)
from ..services.research_service import research_service

app = FastAPI(
    title="AI Research Gap Finder API",
    description="Full-stack AI Research Analyst backend with Real Authentication, Google OAuth, User Isolation, Grounded RAG, and Citation Graph.",
    version="2.2.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Global Exception Handlers (Graceful Public-Deployment Errors)
# -----------------------------------------------------------------------------
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"status": "error", "error_code": "VALIDATION_ERROR", "detail": str(exc)}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    err_str = str(exc)
    traceback.print_exc()
    
    if "429" in err_str or "rate_limit" in err_str.lower():
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "status": "error",
                "error_code": "RATE_LIMIT_EXCEEDED",
                "detail": "You have reached your Groq API free tier rate limit. Please wait a moment before trying again, or update your API key in Settings."
            }
        )
    elif "401" in err_str or "invalid_api_key" in err_str.lower():
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "status": "error",
                "error_code": "INVALID_API_KEY",
                "detail": "Invalid or expired Groq API key. Please check or update your key in Settings."
            }
        )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "error_code": "INTERNAL_ERROR",
            "detail": f"An unexpected error occurred: {err_str}"
        }
    )

# -----------------------------------------------------------------------------
# Pydantic Schemas
# -----------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class GoogleAuthRequest(BaseModel):
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None
    credential: Optional[str] = None

class SetApiKeyRequest(BaseModel):
    api_key: str

class VerifyKeyRequest(BaseModel):
    api_key: str

class AnalyzeRequest(BaseModel):
    query: str

class QARequest(BaseModel):
    question: str
    paper_id: Optional[str] = None

# -----------------------------------------------------------------------------
# Real Authentication & Google OAuth Endpoints
# -----------------------------------------------------------------------------
@app.post("/api/auth/register")
def register_user(req: RegisterRequest):
    """Register a new user with real salted password hashing and 7-day session token."""
    email = req.email.strip().lower()
    if not email or "@" not in email or "." not in email:
        raise HTTPException(status_code=400, detail="Please provide a valid email address.")
    
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long.")
    
    try:
        user = user_store.register_user(email, req.password, req.name)
        token = create_session_token(email, expires_days=Config.SESSION_EXPIRE_DAYS)
        return {
            "status": "success",
            "token": token,
            "user": user
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/login")
def login_user(req: LoginRequest):
    """Sign in an existing user with email and password."""
    email = req.email.strip().lower()
    if not email or not req.password:
        raise HTTPException(status_code=400, detail="Email and password are required.")
    
    user = user_store.authenticate_user(email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password. Please check your credentials.")
    
    token = create_session_token(email, expires_days=Config.SESSION_EXPIRE_DAYS)
    return {
        "status": "success",
        "token": token,
        "user": user
    }

@app.post("/api/auth/google")
def google_auth(req: GoogleAuthRequest):
    """Sign in or register a user seamlessly via Google OAuth Identity."""
    email = req.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Valid Google email required.")
    
    user = user_store.authenticate_google_user(email, req.name, req.picture)
    token = create_session_token(email, expires_days=Config.SESSION_EXPIRE_DAYS)
    return {
        "status": "success",
        "token": token,
        "user": user
    }

@app.get("/api/auth/me")
def get_auth_me(user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Get authenticated user profile and API key status."""
    if not user:
        return {
            "authenticated": False,
            "user": None,
            "system_has_fallback_key": bool(Config.GROQ_API_KEY)
        }
    
    return {
        "authenticated": True,
        "user": user,
        "system_has_fallback_key": bool(Config.GROQ_API_KEY)
    }

@app.get("/api/auth/guest-status")
def get_guest_status(request: Request, user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Check remaining free preview operations for guest mode."""
    from datetime import datetime
    max_ops = getattr(guest_quota, "max_free_ops", 12)
    if user and user.get("has_api_key"):
        return {"is_unlimited": True, "remaining": "unlimited", "used": 0, "max": max_ops}
    
    client_ip = request.client.host if request.client else "unknown_client"
    client_id = user['email'] if user else f"guest_{client_ip}"
    today_str = datetime.now().strftime("%Y-%m-%d")
    record = guest_quota._usage.get(client_id, {"date": today_str, "count": 0})
    if record["date"] != today_str:
        count = 0
    else:
        count = record["count"]
    
    remaining = max(0, max_ops - count)
    return {
        "is_unlimited": False,
        "remaining": remaining,
        "used": count,
        "max": max_ops
    }

@app.post("/api/auth/verify-key")
def test_groq_key(req: VerifyKeyRequest):
    """Test a Groq API key in real-time before saving."""
    return validate_groq_api_key(req.api_key)

@app.post("/api/auth/set-api-key")
def set_user_api_key(req: SetApiKeyRequest, user: Dict[str, Any] = Depends(get_current_user)):
    """Validate and securely save personal Groq API key for the authenticated user."""
    clean_key = req.api_key.strip()
    if not clean_key:
        raise HTTPException(status_code=400, detail="API key cannot be empty.")
    
    val_res = validate_groq_api_key(clean_key)
    if not val_res.get("valid", False):
        raise HTTPException(status_code=400, detail=val_res.get("message", "Invalid API key"))
    
    updated_user = user_store.set_user_api_key(user["email"], clean_key)
    return {
        "status": "success",
        "message": "Your Groq API key has been verified and saved securely.",
        "masked_key": mask_api_key(clean_key)
    }

@app.post("/api/auth/logout")
def logout_user():
    """Log out and instruct client to clear session tokens."""
    return {"status": "success", "message": "Logged out successfully."}

# -----------------------------------------------------------------------------
# Paper Ingestion & Storage Endpoints (User Workspace Scoped)
# -----------------------------------------------------------------------------
@app.get("/api/health")
def get_health():
    """Health check endpoint exposing system status, LLM model, and vector store status."""
    stats = research_service.get_stats()
    return {
        "status": "healthy",
        "configured_model": Config.LLM_MODEL,
        "embedding_model": Config.EMBEDDING_MODEL,
        "total_papers": stats.get("total_papers", 0),
        "total_chunks": stats.get("total_chunks", 0),
        "vector_store_health": stats.get("status", "healthy")
    }

@app.post("/api/upload")
async def upload_paper(
    file: UploadFile = File(...),
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """
    Upload and ingest a single PDF paper with user workspace isolation and SHA-256 deduplication.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    upload_dir = Path(Config.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    temp_path = upload_dir / file.filename

    try:
        content = await file.read()
        
        # Validate file size
        max_bytes = Config.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(status_code=413, detail=f"File exceeds maximum allowable size of {Config.MAX_UPLOAD_SIZE_MB}MB.")
        
        # Check PDF header magic bytes
        if not content.startswith(b"%PDF-"):
            raise HTTPException(status_code=400, detail="The uploaded file is not a valid or readable PDF format.")
        
        with open(temp_path, "wb") as buffer:
            buffer.write(content)
        
        user_id = user["email"] if user else "guest"
        result = research_service.process_and_ingest_pdf(str(temp_path), user_id=user_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

@app.post("/api/upload/batch")
async def upload_batch_papers(
    files: List[UploadFile] = File(...),
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Upload and ingest multiple PDF papers with workspace isolation."""
    results = []
    upload_dir = Path(Config.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    user_id = user["email"] if user else "guest"

    for file in files:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": "Only PDF files supported."
            })
            continue
        
        temp_path = upload_dir / file.filename
        try:
            content = await file.read()
            if not content.startswith(b"%PDF-"):
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": "Invalid PDF file header."
                })
                continue
            
            with open(temp_path, "wb") as buffer:
                buffer.write(content)
            
            res = research_service.process_and_ingest_pdf(str(temp_path), user_id=user_id)
            results.append(res)
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": str(e)
            })

    return {"results": results, "total_processed": len(results)}

@app.get("/api/papers")
def list_papers(user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Retrieve list of papers scoped to the current user's workspace."""
    user_id = user["email"] if user else None
    papers = research_service.get_all_papers(user_id=user_id)
    return {"papers": papers, "count": len(papers)}

@app.delete("/api/papers/{paper_id}")
def delete_paper(
    paper_id: str,
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Delete a paper from the vector store scoped to the user."""
    user_id = user["email"] if user else None
    success = research_service.delete_paper(paper_id, user_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Paper '{paper_id}' could not be deleted.")
    return {"status": "success", "message": f"Paper '{paper_id}' deleted successfully."}

# -----------------------------------------------------------------------------
# Research RAG, Analysis & Novel Discovery Endpoints (With User Scoped Keys)
# -----------------------------------------------------------------------------
@app.post("/api/qa")
@app.post("/ask")
@app.post("/api/ask")
def answer_paper_question(req: QARequest, api_key: Optional[str] = Depends(get_user_llm_key)):
    """Grounded RAG Question Answering using the authenticated user's personal Groq API key."""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    
    result = research_service.answer_question(req.question, req.paper_id, api_key=api_key)
    if not result.get("success", False):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to answer question."))
    return result

@app.get("/api/papers/{paper_id}/analysis")
def get_paper_deep_analysis(paper_id: str, api_key: Optional[str] = Depends(get_user_llm_key)):
    """Get complete 9-section academic analysis for a specific paper."""
    result = research_service.get_paper_analysis(paper_id, api_key=api_key)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("error", "Analysis failed"))
    return result

@app.get("/api/papers/{paper_id}/novel-discovery")
def get_paper_novel_discovery(paper_id: str, api_key: Optional[str] = Depends(get_user_llm_key)):
    """Execute Enhanced Novel Discovery Engine (Elite Auditing Team perspective)."""
    result = research_service.get_novel_discovery(paper_id, api_key=api_key)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("error", "Discovery failed"))
    return result

@app.get("/api/papers/{paper_id}/autonomous-discovery")
def get_paper_autonomous_discovery(paper_id: str, force_reload: bool = False, api_key: Optional[str] = Depends(get_user_llm_key)):
    """Execute 5-Stage Scientific Multi-Agent Actor-Critic Orchestration with Ontological Knowledge Graphs."""
    result = research_service.get_autonomous_agent_discovery(paper_id, api_key=api_key, force_reload=force_reload)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("error", "Autonomous discovery failed"))
    return result

@app.get("/api/papers/{paper_id}/metrics")
def get_paper_metrics_data(paper_id: str):
    """Extract performance metrics, tested benchmarks, and mentioned models."""
    result = research_service.get_paper_metrics(paper_id)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("error", "Metrics extraction failed"))
    return result

@app.get("/api/papers/{paper_id}/citations")
def get_paper_citations_data(paper_id: str):
    """Extract citation network, internal numbered references, and author-year citations."""
    result = research_service.get_paper_citations(paper_id)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("error", "Citations extraction failed"))
    return result

@app.get("/api/papers/{paper_id}/simplified-summary")
def get_paper_simplified_summary(paper_id: str, api_key: Optional[str] = Depends(get_user_llm_key)):
    """Get plain-English simplified summary with visual flowchart, cards, and priority badges."""
    result = research_service.get_simplified_summary(paper_id, api_key=api_key)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("error", "Simplified summary failed"))
    return result

@app.get("/api/papers/{paper_id}/compare")
def get_paper_online_comparison(paper_id: str, api_key: Optional[str] = Depends(get_user_llm_key)):
    """Search online for similar literature, extract keywords, and generate comparative review."""
    result = research_service.get_online_comparison(paper_id, api_key=api_key)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("error", "Comparison failed"))
    return result

@app.get("/api/papers/{paper_id}/export/pdf")
def export_paper_report_pdf(paper_id: str):
    """Download comprehensive research gap report as a beautifully formatted PDF."""
    try:
        pdf_bytes = research_service.export_paper_report(paper_id, format="pdf")
        if isinstance(pdf_bytes, dict) and pdf_bytes.get("status") == "error":
            raise HTTPException(status_code=404, detail=pdf_bytes.get("error", "PDF generation failed"))
        
        safe_filename = re.sub(r'[^a-zA-Z0-9_-]', '_', paper_id)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="research_report_{safe_filename}.pdf"',
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"PDF generation error: {str(e)}")

@app.get("/api/papers/{paper_id}/export/{export_format}")
def export_paper_report_file(paper_id: str, export_format: str = "markdown"):
    """Download comprehensive research gap report as Markdown (.md) or PDF (.pdf)."""
    if export_format.lower() == "pdf":
        return export_paper_report_pdf(paper_id)
    
    try:
        result = research_service.export_paper_report(paper_id, format=export_format)
        if isinstance(result, dict) and result.get("status") == "error":
            raise HTTPException(status_code=404, detail=result.get("error", "Export failed"))
        
        safe_filename = re.sub(r'[^a-zA-Z0-9_-]', '_', paper_id)
        return Response(
            content=str(result),
            media_type="text/markdown; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="research_report_{safe_filename}.md"',
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")

@app.post("/api/analyze")
def analyze_research_gaps(req: AnalyzeRequest, api_key: Optional[str] = Depends(get_user_llm_key)):
    """Execute autonomous LangGraph multi-stage reasoning workflow across all indexed papers."""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    return research_service.analyze_gaps(req.query)

@app.get("/api/stats")
def get_system_stats():
    """Retrieve corpus statistics, total chunks, and system health."""
    return research_service.get_stats()

# -----------------------------------------------------------------------------
# Static Files & Frontend SPA Mounting
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
FRONTEND_DIR = BASE_DIR / "frontend"

target_static_dir = str(FRONTEND_DIST) if FRONTEND_DIST.exists() and (FRONTEND_DIST / "index.html").exists() else str(FRONTEND_DIR)

if os.path.exists(target_static_dir) and os.path.exists(os.path.join(target_static_dir, "index.html")):
    app.mount("/", StaticFiles(directory=target_static_dir, html=True), name="frontend")
else:
    @app.get("/")
    def read_root():
        return {
            "message": "AI Research Gap Finder API is running.",
            "docs_url": "/docs",
            "health_url": "/api/health"
        }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
