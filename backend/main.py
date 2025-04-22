from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware # To allow frontend requests

from backend.models.schemas import (
    CodeInput, ExplanationResponse, SuggestionResponse,
    DebugResponse, WhatIfResponse
)
from backend.core.llm_services import (
    get_code_explanation, get_code_suggestions,
    get_code_debugging_info, answer_what_if_question
)

app = FastAPI(
    title="AI Code Mentor API",
    description="API for the AI-Powered Code Mentor application.",
    version="0.1.0",
)

# --- CORS Middleware ---
# Allow requests from your Streamlit frontend (adjust origins if needed)
origins = [
    "http://localhost",
    "http://localhost:8501", # Default Streamlit port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)

# --- API Endpoints ---
@app.get("/")
async def read_root():
    return {"message": "Welcome to the AI Code Mentor API"}

@app.post("/explain", response_model=ExplanationResponse)
async def explain_code(payload: CodeInput):
    """Explains the provided code."""
    if not payload.code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No code provided")
    result = await get_code_explanation(payload.code)
    if result.get("error"):
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    return ExplanationResponse(**result)

@app.post("/suggest", response_model=SuggestionResponse)
async def suggest_improvements(payload: CodeInput):
    """Suggests improvements for the provided code."""
    if not payload.code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No code provided")
    result = await get_code_suggestions(payload.code)
    if result.get("error"):
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    return SuggestionResponse(**result)

@app.post("/debug", response_model=DebugResponse)
async def debug_code(payload: CodeInput):
    """Identifies potential bugs in the provided code."""
    if not payload.code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No code provided")
    result = await get_code_debugging_info(payload.code)
    if result.get("error"):
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    return DebugResponse(**result)

@app.post("/whatif", response_model=WhatIfResponse)
async def what_if_scenario(payload: CodeInput):
    """Answers a 'what if' question about the code."""
    if not payload.code or not payload.user_question:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code and user question required")
    result = await answer_what_if_question(payload.code, payload.user_question)
    if result.get("error"):
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    return WhatIfResponse(**result)

# --- Run Instruction (for development) ---
# To run the backend: uvicorn backend.main:app --reload --port 8000