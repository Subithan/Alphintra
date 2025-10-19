from pydantic import BaseModel
from typing import List, Optional, Any


class CodeGenerationRequest(BaseModel):
    prompt: str
    context: Optional[str] = None
    language: Optional[str] = None
    complexity_level: Optional[str] = "intermediate"
    include_comments: Optional[bool] = True
    max_tokens: Optional[int] = 1024
    preferred_provider: Optional[str] = None


class CodeGenerationResponse(BaseModel):
    success: bool
    code: str
    explanation: str
    suggestions: List[str]
    estimated_complexity: str
    tokens_used: int
    execution_time: float
    provider: str
    confidence_score: float
    request_id: str


class CodeExplanationRequest(BaseModel):
    code: str
    context: Optional[str] = None
    focus_areas: Optional[List[str]] = None
    preferred_provider: Optional[str] = None


class CodeExplanationResponse(BaseModel):
    success: bool
    explanation: str
    key_concepts: List[str]
    potential_issues: List[str]
    improvement_suggestions: List[str]
    complexity_analysis: str
    tokens_used: int
    provider: str
    request_id: str


class CodeOptimizationRequest(BaseModel):
    code: str
    optimization_type: Optional[str] = "performance"
    context: Optional[str] = None
    preserve_functionality: Optional[bool] = True
    preferred_provider: Optional[str] = None


class CodeOptimizationResponse(BaseModel):
    success: bool
    optimized_code: str
    changes_made: List[str]
    performance_impact: str
    risk_assessment: str
    before_after_comparison: Any | None
    tokens_used: int
    provider: str
    request_id: str


class CodeDebuggingRequest(BaseModel):
    code: str
    error_message: Optional[str] = None
    context: Optional[str] = None
    preferred_provider: Optional[str] = None


class CodeDebuggingResponse(BaseModel):
    success: bool
    issue_analysis: str
    suggested_fixes: List[str]
    corrected_code: Optional[str] = None
    explanation: str
    prevention_tips: List[str]
    tokens_used: int
    provider: str
    request_id: str


class TestGenerationResponse(BaseModel):
    success: bool
    test_code: str
    test_cases: List[str]
    coverage_analysis: str
    testing_strategy: str
    mock_data_suggestions: List[str]
    tokens_used: int
    provider: str
    request_id: str
