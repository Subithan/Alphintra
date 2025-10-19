from fastapi import APIRouter
from ..schemas.ai import (
    CodeGenerationRequest, CodeGenerationResponse,
    CodeExplanationRequest, CodeExplanationResponse,
    CodeOptimizationRequest, CodeOptimizationResponse,
    CodeDebuggingRequest, CodeDebuggingResponse, TestGenerationResponse,
)
from ..services import ai_service


router = APIRouter(prefix="/api/ai", tags=["AI"])


@router.post("/generate", response_model=CodeGenerationResponse)
def generate(req: CodeGenerationRequest):
    return ai_service.generate_code(req)


@router.post("/explain", response_model=CodeExplanationResponse)
def explain(req: CodeExplanationRequest):
    return ai_service.explain_code(req)


@router.post("/optimize", response_model=CodeOptimizationResponse)
def optimize(req: CodeOptimizationRequest):
    return ai_service.optimize_code(req)


@router.post("/debug", response_model=CodeDebuggingResponse)
def debug(req: CodeDebuggingRequest):
    return ai_service.debug_code(req)


@router.post("/tests", response_model=TestGenerationResponse)
def tests(payload: dict):
    code = payload.get("code", "")
    context = payload.get("context")
    test_type = payload.get("test_type")
    return ai_service.generate_tests(code, context, test_type)
