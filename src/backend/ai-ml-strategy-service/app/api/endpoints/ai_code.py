"""
AI Code API Endpoints - RESTful API for AI-powered code operations
"""

from typing import Optional, List, Dict, Any
import logging
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from datetime import datetime

from app.services.ai_code_service import (
    ai_code_service,
    CodeLanguage,
    ComplexityLevel,
    OptimizationType
)
from app.core.auth import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["AI Code"])
security = HTTPBearer()

# Request Models
class CodeGenerationRequest(BaseModel):
    """Request model for code generation"""
    prompt: str = Field(..., min_length=10, max_length=2000, description="Natural language description of the code to generate")
    context: str = Field("", max_length=5000, description="Additional context for code generation")
    language: CodeLanguage = Field(CodeLanguage.PYTHON, description="Programming language for generated code")
    complexity_level: ComplexityLevel = Field(ComplexityLevel.INTERMEDIATE, description="Target complexity level")
    include_comments: bool = Field(True, description="Whether to include code comments")
    max_tokens: int = Field(2000, ge=100, le=4000, description="Maximum tokens for AI response")
    preferred_provider: str = Field("openai", description="Preferred AI provider (openai/anthropic)")

    @validator('prompt')
    def validate_prompt(cls, v):
        if not v.strip():
            raise ValueError("Prompt cannot be empty")
        return v.strip()

class CodeExplanationRequest(BaseModel):
    """Request model for code explanation"""
    code: str = Field(..., min_length=10, max_length=10000, description="Code to explain")
    context: str = Field("", max_length=5000, description="Additional context")
    focus_areas: List[str] = Field(
        default_factory=lambda: ["functionality", "performance", "security"],
        description="Areas to focus on in explanation"
    )
    preferred_provider: str = Field("anthropic", description="Preferred AI provider")

    @validator('code')
    def validate_code(cls, v):
        if not v.strip():
            raise ValueError("Code cannot be empty")
        return v.strip()

class CodeOptimizationRequest(BaseModel):
    """Request model for code optimization"""
    code: str = Field(..., min_length=10, max_length=10000, description="Code to optimize")
    optimization_type: OptimizationType = Field(
        OptimizationType.PERFORMANCE,
        description="Type of optimization to perform"
    )
    context: str = Field("", max_length=5000, description="Additional context")
    preserve_functionality: bool = Field(True, description="Whether to preserve exact functionality")
    preferred_provider: str = Field("openai", description="Preferred AI provider")

class CodeDebuggingRequest(BaseModel):
    """Request model for code debugging"""
    code: str = Field(..., min_length=10, max_length=10000, description="Code to debug")
    error_message: str = Field("", max_length=2000, description="Error message if available")
    context: str = Field("", max_length=5000, description="Additional context")
    preferred_provider: str = Field("anthropic", description="Preferred AI provider")

class TestGenerationRequest(BaseModel):
    """Request model for test generation"""
    code: str = Field(..., min_length=10, max_length=10000, description="Code to generate tests for")
    test_type: str = Field("unit", description="Type of tests to generate")
    context: str = Field("", max_length=5000, description="Additional context")
    coverage_target: int = Field(80, ge=50, le=100, description="Target code coverage percentage")
    preferred_provider: str = Field("openai", description="Preferred AI provider")

# Response Models
class CodeGenerationResponse(BaseModel):
    """Response model for code generation"""
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

class CodeExplanationResponse(BaseModel):
    """Response model for code explanation"""
    success: bool
    explanation: str
    key_concepts: List[str]
    potential_issues: List[str]
    improvement_suggestions: List[str]
    complexity_analysis: str
    tokens_used: int
    provider: str
    request_id: str

class CodeOptimizationResponse(BaseModel):
    """Response model for code optimization"""
    success: bool
    optimized_code: str
    changes_made: List[str]
    performance_impact: str
    risk_assessment: str
    before_after_comparison: Dict[str, Any]
    tokens_used: int
    provider: str
    request_id: str

class CodeDebuggingResponse(BaseModel):
    """Response model for code debugging"""
    success: bool
    issue_analysis: str
    suggested_fixes: List[str]
    corrected_code: Optional[str]
    explanation: str
    prevention_tips: List[str]
    tokens_used: int
    provider: str
    request_id: str

class TestGenerationResponse(BaseModel):
    """Response model for test generation"""
    success: bool
    test_code: str
    test_cases: List[str]
    coverage_analysis: str
    testing_strategy: str
    mock_data_suggestions: List[str]
    tokens_used: int
    provider: str
    request_id: str

class UsageStatsResponse(BaseModel):
    """Response model for usage statistics"""
    total_requests: int
    total_tokens: int
    provider_usage: Dict[str, Dict[str, int]]
    operation_counts: Dict[str, int]
    timestamp: datetime

# Dependency for authentication
async def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get authenticated user from token"""
    try:
        # In production, implement proper JWT validation
        user = await get_current_user(credentials.credentials)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return user
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

# Utility function to generate request IDs
def generate_request_id() -> str:
    """Generate unique request ID"""
    import uuid
    return str(uuid.uuid4())

# API Endpoints

@router.post("/generate", response_model=CodeGenerationResponse)
async def generate_code(
    request: CodeGenerationRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_authenticated_user)
):
    """
    Generate code from natural language prompt
    
    This endpoint uses AI to generate code based on a natural language description.
    It's optimized for trading and financial applications with domain-specific context.
    """
    request_id = generate_request_id()
    
    try:
        logger.info(f"Code generation request {request_id} from user {user.id}")
        
        # Call AI service
        result = await ai_code_service.generate_code(
            prompt=request.prompt,
            context=request.context,
            language=request.language,
            complexity_level=request.complexity_level,
            include_comments=request.include_comments,
            max_tokens=request.max_tokens,
            preferred_provider=request.preferred_provider
        )
        
        # Log usage for monitoring
        background_tasks.add_task(
            log_ai_usage,
            user_id=user.id,
            operation="generate_code",
            tokens_used=result.tokens_used,
            provider=result.provider,
            request_id=request_id
        )
        
        return CodeGenerationResponse(
            success=True,
            code=result.code,
            explanation=result.explanation,
            suggestions=result.suggestions,
            estimated_complexity=result.estimated_complexity,
            tokens_used=result.tokens_used,
            execution_time=result.execution_time,
            provider=result.provider,
            confidence_score=result.confidence_score,
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"Code generation failed for request {request_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code generation failed: {str(e)}"
        )

@router.post("/explain", response_model=CodeExplanationResponse)
async def explain_code(
    request: CodeExplanationRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_authenticated_user)
):
    """
    Explain existing code with AI analysis
    
    This endpoint analyzes code and provides detailed explanations,
    focusing on trading domain concepts and patterns.
    """
    request_id = generate_request_id()
    
    try:
        logger.info(f"Code explanation request {request_id} from user {user.id}")
        
        result = await ai_code_service.explain_code(
            code=request.code,
            context=request.context,
            focus_areas=request.focus_areas,
            preferred_provider=request.preferred_provider
        )
        
        background_tasks.add_task(
            log_ai_usage,
            user_id=user.id,
            operation="explain_code",
            tokens_used=result.tokens_used,
            provider=result.provider,
            request_id=request_id
        )
        
        return CodeExplanationResponse(
            success=True,
            explanation=result.explanation,
            key_concepts=result.key_concepts,
            potential_issues=result.potential_issues,
            improvement_suggestions=result.improvement_suggestions,
            complexity_analysis=result.complexity_analysis,
            tokens_used=result.tokens_used,
            provider=result.provider,
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"Code explanation failed for request {request_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code explanation failed: {str(e)}"
        )

@router.post("/optimize", response_model=CodeOptimizationResponse)
async def optimize_code(
    request: CodeOptimizationRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_authenticated_user)
):
    """
    Optimize existing code using AI analysis
    
    This endpoint analyzes code and provides optimized versions
    focusing on performance, readability, security, or trading-specific improvements.
    """
    request_id = generate_request_id()
    
    try:
        logger.info(f"Code optimization request {request_id} from user {user.id}")
        
        result = await ai_code_service.optimize_code(
            code=request.code,
            optimization_type=request.optimization_type,
            context=request.context,
            preserve_functionality=request.preserve_functionality,
            preferred_provider=request.preferred_provider
        )
        
        background_tasks.add_task(
            log_ai_usage,
            user_id=user.id,
            operation="optimize_code",
            tokens_used=result.tokens_used,
            provider=result.provider,
            request_id=request_id
        )
        
        return CodeOptimizationResponse(
            success=True,
            optimized_code=result.optimized_code,
            changes_made=result.changes_made,
            performance_impact=result.performance_impact,
            risk_assessment=result.risk_assessment,
            before_after_comparison=result.before_after_comparison,
            tokens_used=result.tokens_used,
            provider=result.provider,
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"Code optimization failed for request {request_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code optimization failed: {str(e)}"
        )

@router.post("/debug", response_model=CodeDebuggingResponse)
async def debug_code(
    request: CodeDebuggingRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_authenticated_user)
):
    """
    Debug code issues using AI analysis
    
    This endpoint analyzes problematic code and provides debugging assistance,
    including issue identification, fix suggestions, and corrected code.
    """
    request_id = generate_request_id()
    
    try:
        logger.info(f"Code debugging request {request_id} from user {user.id}")
        
        result = await ai_code_service.debug_code(
            code=request.code,
            error_message=request.error_message,
            context=request.context,
            preferred_provider=request.preferred_provider
        )
        
        background_tasks.add_task(
            log_ai_usage,
            user_id=user.id,
            operation="debug_code",
            tokens_used=result.tokens_used,
            provider=result.provider,
            request_id=request_id
        )
        
        return CodeDebuggingResponse(
            success=True,
            issue_analysis=result.issue_analysis,
            suggested_fixes=result.suggested_fixes,
            corrected_code=result.corrected_code,
            explanation=result.explanation,
            prevention_tips=result.prevention_tips,
            tokens_used=result.tokens_used,
            provider=result.provider,
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"Code debugging failed for request {request_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code debugging failed: {str(e)}"
        )

@router.post("/tests", response_model=TestGenerationResponse)
async def generate_tests(
    request: TestGenerationRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_authenticated_user)
):
    """
    Generate unit tests for code using AI
    
    This endpoint generates comprehensive test suites for provided code,
    with focus on trading system testing patterns and edge cases.
    """
    request_id = generate_request_id()
    
    try:
        logger.info(f"Test generation request {request_id} from user {user.id}")
        
        result = await ai_code_service.generate_tests(
            code=request.code,
            test_type=request.test_type,
            context=request.context,
            coverage_target=request.coverage_target,
            preferred_provider=request.preferred_provider
        )
        
        background_tasks.add_task(
            log_ai_usage,
            user_id=user.id,
            operation="generate_tests",
            tokens_used=result.tokens_used,
            provider=result.provider,
            request_id=request_id
        )
        
        return TestGenerationResponse(
            success=True,
            test_code=result.test_code,
            test_cases=result.test_cases,
            coverage_analysis=result.coverage_analysis,
            testing_strategy=result.testing_strategy,
            mock_data_suggestions=result.mock_data_suggestions,
            tokens_used=result.tokens_used,
            provider=result.provider,
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"Test generation failed for request {request_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test generation failed: {str(e)}"
        )

@router.get("/usage", response_model=UsageStatsResponse)
async def get_usage_stats(
    user: User = Depends(get_authenticated_user)
):
    """
    Get AI service usage statistics
    
    Returns current usage statistics including token consumption,
    provider usage, and operation counts.
    """
    try:
        logger.info(f"Usage stats request from user {user.id}")
        
        stats = ai_code_service.get_usage_stats()
        
        return UsageStatsResponse(
            total_requests=stats['total_requests'],
            total_tokens=stats['total_tokens'],
            provider_usage=stats['provider_usage'],
            operation_counts=stats['operation_counts'],
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Failed to get usage stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve usage statistics: {str(e)}"
        )

@router.delete("/cache")
async def clear_cache(
    user: User = Depends(get_authenticated_user)
):
    """
    Clear AI service cache
    
    Clears the internal response cache. Useful for forcing fresh AI responses
    or during development/testing.
    """
    try:
        logger.info(f"Cache clear request from user {user.id}")
        
        ai_code_service.clear_cache()
        
        return {"success": True, "message": "AI service cache cleared successfully"}
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )

# Background task for logging AI usage
async def log_ai_usage(
    user_id: int,
    operation: str,
    tokens_used: int,
    provider: str,
    request_id: str
):
    """Log AI usage for monitoring and billing"""
    try:
        # In production, this would save to database
        usage_data = {
            "user_id": user_id,
            "operation": operation,
            "tokens_used": tokens_used,
            "provider": provider,
            "request_id": request_id,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"AI usage logged: {usage_data}")
        
        # TODO: Save to database for usage tracking and billing
        # await usage_repository.create_usage_record(usage_data)
        
    except Exception as e:
        logger.error(f"Failed to log AI usage: {str(e)}")

# Health check endpoint
@router.get("/health")
async def health_check():
    """Check AI service health"""
    try:
        stats = ai_code_service.get_usage_stats()
        
        return {
            "status": "healthy",
            "total_requests": stats['total_requests'],
            "providers_available": len([p for p in ['openai', 'anthropic'] if ai_code_service.openai_client or ai_code_service.anthropic_client]),
            "cache_size": len(ai_code_service.cache),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is not healthy"
        )