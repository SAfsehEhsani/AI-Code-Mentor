from pydantic import BaseModel
from typing import Optional, List, Dict

class CodeInput(BaseModel):
    code: str
    language: str = "python" # Defaulting to Python for now
    # Optional: user_question for "What If" scenarios
    user_question: Optional[str] = None

class ExplanationResponse(BaseModel):
    line_by_line: Optional[Dict[int, str]] = None # Line number -> Explanation
    overall_summary: Optional[str] = None
    error: Optional[str] = None

class SuggestionResponse(BaseModel):
    suggestions: Optional[List[str]] = None
    error: Optional[str] = None

class DebugResponse(BaseModel):
    potential_bugs: Optional[List[Dict[str, str]]] = None # e.g., {'line': '5', 'issue': '...'}
    error: Optional[str] = None

class WhatIfResponse(BaseModel):
    explanation: Optional[str] = None
    modified_code: Optional[str] = None
    error: Optional[str] = None