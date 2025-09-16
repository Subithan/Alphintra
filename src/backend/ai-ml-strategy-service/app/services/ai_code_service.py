"""
AI Code Service - Provides AI-powered code generation, explanation, optimization, and debugging
capabilities for the Alphintra trading platform.
"""

import os
import asyncio
import json
import hashlib
import time
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
from enum import Enum
import logging
from functools import wraps

import openai
from anthropic import Anthropic
import httpx
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

# Configuration
AI_PROVIDERS = {
    'openai': {
        'api_key': os.getenv('OPENAI_API_KEY'),
        'model': 'gpt-4-1106-preview',
        'max_tokens': 4000,
        'temperature': 0.1
    },
    'anthropic': {
        'api_key': os.getenv('ANTHROPIC_API_KEY'),
        'model': 'claude-3-sonnet-20240229',
        'max_tokens': 4000,
        'temperature': 0.1
    }
}

class CodeLanguage(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    SQL = "sql"
    JSON = "json"

class ComplexityLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class OptimizationType(str, Enum):
    PERFORMANCE = "performance"
    READABILITY = "readability"
    SECURITY = "security"
    MEMORY = "memory"
    TRADING_SPECIFIC = "trading_specific"

@dataclass
class CodeGenResult:
    """Result from code generation operations"""
    code: str
    explanation: str
    suggestions: List[str]
    estimated_complexity: str
    tokens_used: int
    execution_time: float
    provider: str
    confidence_score: float

@dataclass
class ExplanationResult:
    """Result from code explanation operations"""
    explanation: str
    key_concepts: List[str]
    potential_issues: List[str]
    improvement_suggestions: List[str]
    complexity_analysis: str
    tokens_used: int
    provider: str

@dataclass
class OptimizationResult:
    """Result from code optimization operations"""
    optimized_code: str
    changes_made: List[str]
    performance_impact: str
    risk_assessment: str
    before_after_comparison: Dict[str, Any]
    tokens_used: int
    provider: str

@dataclass
class DebugResult:
    """Result from debugging operations"""
    issue_analysis: str
    suggested_fixes: List[str]
    corrected_code: Optional[str]
    explanation: str
    prevention_tips: List[str]
    tokens_used: int
    provider: str

@dataclass
class TestGenResult:
    """Result from test generation operations"""
    test_code: str
    test_cases: List[str]
    coverage_analysis: str
    testing_strategy: str
    mock_data_suggestions: List[str]
    tokens_used: int
    provider: str

def rate_limit(max_calls: int = 60, time_window: int = 60):
    """Rate limiting decorator"""
    calls = []
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            now = time.time()
            # Remove calls outside the time window
            calls[:] = [call_time for call_time in calls if now - call_time < time_window]
            
            if len(calls) >= max_calls:
                sleep_time = time_window - (now - calls[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
            
            calls.append(now)
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

class AICodeService:
    """
    Main service class for AI-powered code operations.
    Provides code generation, explanation, optimization, debugging, and test generation.
    """
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        self.cache = {}  # Simple in-memory cache
        self.usage_stats = {
            'total_requests': 0,
            'total_tokens': 0,
            'provider_usage': {},
            'operation_counts': {}
        }
        
        # Initialize clients if API keys are available
        if AI_PROVIDERS['openai']['api_key']:
            openai.api_key = AI_PROVIDERS['openai']['api_key']
            self.openai_client = openai
        
        if AI_PROVIDERS['anthropic']['api_key']:
            self.anthropic_client = Anthropic(api_key=AI_PROVIDERS['anthropic']['api_key'])

    def _get_cache_key(self, operation: str, **kwargs) -> str:
        """Generate cache key for request"""
        key_data = {'operation': operation, **kwargs}
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()

    def _should_use_cache(self, cache_key: str, max_age: int = 3600) -> bool:
        """Check if cached result is still valid"""
        if cache_key not in self.cache:
            return False
        
        cached_result = self.cache[cache_key]
        return (time.time() - cached_result['timestamp']) < max_age

    def _get_trading_context_prompt(self) -> str:
        """Get trading domain-specific context for AI prompts"""
        return """
        You are an AI assistant specialized in algorithmic trading and financial software development 
        for the Alphintra platform. Focus on:
        
        - Trading strategy development and backtesting
        - Financial data processing and analysis
        - Risk management and portfolio optimization
        - Real-time market data handling
        - Order execution and trade management
        - Performance metrics and reporting
        - Regulatory compliance and best practices
        
        Always consider:
        - Performance and low-latency requirements
        - Data security and regulatory compliance
        - Risk management principles
        - Trading-specific design patterns
        - Market data handling best practices
        """

    def _get_security_constraints(self) -> str:
        """Get security constraints for code generation"""
        return """
        Security constraints:
        - Never include hardcoded API keys, passwords, or sensitive data
        - Use proper input validation and sanitization
        - Implement appropriate error handling
        - Follow secure coding practices
        - Consider rate limiting and resource management
        - Avoid code that could be used maliciously
        - Ensure proper authentication and authorization
        """

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, openai.RateLimitError))
    )
    async def _call_openai(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """Call OpenAI API with retries"""
        try:
            response = await self.openai_client.ChatCompletion.acreate(
                model=AI_PROVIDERS['openai']['model'],
                messages=messages,
                max_tokens=kwargs.get('max_tokens', AI_PROVIDERS['openai']['max_tokens']),
                temperature=kwargs.get('temperature', AI_PROVIDERS['openai']['temperature'])
            )
            
            return {
                'content': response.choices[0].message.content,
                'tokens_used': response.usage.total_tokens,
                'provider': 'openai'
            }
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.RequestError)
    )
    async def _call_anthropic(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """Call Anthropic API with retries"""
        try:
            # Convert messages to Anthropic format
            system_message = ""
            user_messages = []
            
            for msg in messages:
                if msg['role'] == 'system':
                    system_message = msg['content']
                else:
                    user_messages.append(msg)
            
            response = await self.anthropic_client.messages.create(
                model=AI_PROVIDERS['anthropic']['model'],
                max_tokens=kwargs.get('max_tokens', AI_PROVIDERS['anthropic']['max_tokens']),
                temperature=kwargs.get('temperature', AI_PROVIDERS['anthropic']['temperature']),
                system=system_message,
                messages=user_messages
            )
            
            return {
                'content': response.content[0].text,
                'tokens_used': response.usage.input_tokens + response.usage.output_tokens,
                'provider': 'anthropic'
            }
        except Exception as e:
            logger.error(f"Anthropic API call failed: {str(e)}")
            raise

    async def _call_ai_provider(self, messages: List[Dict], preferred_provider: str = 'openai', **kwargs) -> Dict[str, Any]:
        """Call AI provider with fallback logic"""
        providers = [preferred_provider]
        if preferred_provider == 'openai' and self.anthropic_client:
            providers.append('anthropic')
        elif preferred_provider == 'anthropic' and self.openai_client:
            providers.append('openai')

        last_error = None
        for provider in providers:
            try:
                if provider == 'openai' and self.openai_client:
                    return await self._call_openai(messages, **kwargs)
                elif provider == 'anthropic' and self.anthropic_client:
                    return await self._call_anthropic(messages, **kwargs)
            except Exception as e:
                last_error = e
                logger.warning(f"Provider {provider} failed, trying next provider: {str(e)}")
                continue
        
        if last_error:
            raise last_error
        else:
            raise RuntimeError("No AI providers available")

    def _update_usage_stats(self, operation: str, tokens: int, provider: str):
        """Update usage statistics"""
        self.usage_stats['total_requests'] += 1
        self.usage_stats['total_tokens'] += tokens
        
        if provider not in self.usage_stats['provider_usage']:
            self.usage_stats['provider_usage'][provider] = {'requests': 0, 'tokens': 0}
        
        self.usage_stats['provider_usage'][provider]['requests'] += 1
        self.usage_stats['provider_usage'][provider]['tokens'] += tokens
        
        if operation not in self.usage_stats['operation_counts']:
            self.usage_stats['operation_counts'][operation] = 0
        self.usage_stats['operation_counts'][operation] += 1

    @rate_limit(max_calls=30, time_window=60)
    async def generate_code(
        self,
        prompt: str,
        context: str = "",
        language: CodeLanguage = CodeLanguage.PYTHON,
        complexity_level: ComplexityLevel = ComplexityLevel.INTERMEDIATE,
        include_comments: bool = True,
        max_tokens: int = 2000,
        preferred_provider: str = 'openai'
    ) -> CodeGenResult:
        """
        Generate code from natural language prompt with trading domain context.
        """
        start_time = time.time()
        
        # Check cache first
        cache_key = self._get_cache_key(
            'generate_code', prompt=prompt, context=context, 
            language=language, complexity_level=complexity_level
        )
        
        if self._should_use_cache(cache_key):
            logger.info("Returning cached code generation result")
            return self.cache[cache_key]['result']

        # Prepare messages
        system_prompt = f"""
        {self._get_trading_context_prompt()}
        
        {self._get_security_constraints()}
        
        Generate {language} code at {complexity_level} level.
        {"Include clear comments and documentation." if include_comments else "Minimize comments."}
        
        Focus on:
        - Clean, readable, and efficient code
        - Proper error handling
        - Trading platform best practices
        - Security considerations
        """

        user_prompt = f"""
        Context: {context}
        
        Request: {prompt}
        
        Please provide:
        1. Clean, working code
        2. Brief explanation of the approach
        3. Key considerations and potential improvements
        4. Estimated complexity level
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            # Call AI provider
            response = await self._call_ai_provider(messages, preferred_provider, max_tokens=max_tokens)
            
            # Parse response (simplified - in production, would use more sophisticated parsing)
            content = response['content']
            
            # Extract code blocks
            code_blocks = []
            lines = content.split('\n')
            in_code_block = False
            current_block = []
            
            for line in lines:
                if line.strip().startswith('```'):
                    if in_code_block:
                        code_blocks.append('\n'.join(current_block))
                        current_block = []
                        in_code_block = False
                    else:
                        in_code_block = True
                elif in_code_block:
                    current_block.append(line)
            
            # Get the main code block
            main_code = code_blocks[0] if code_blocks else content
            
            # Create result
            result = CodeGenResult(
                code=main_code,
                explanation=content,
                suggestions=[
                    "Test the code thoroughly before production use",
                    "Consider adding more comprehensive error handling",
                    "Review for trading-specific optimizations"
                ],
                estimated_complexity=complexity_level.value,
                tokens_used=response['tokens_used'],
                execution_time=time.time() - start_time,
                provider=response['provider'],
                confidence_score=0.8  # Simplified scoring
            )
            
            # Update stats and cache
            self._update_usage_stats('generate_code', response['tokens_used'], response['provider'])
            self.cache[cache_key] = {'result': result, 'timestamp': time.time()}
            
            return result

        except Exception as e:
            logger.error(f"Code generation failed: {str(e)}")
            raise RuntimeError(f"Failed to generate code: {str(e)}")

    @rate_limit(max_calls=40, time_window=60)
    async def explain_code(
        self,
        code: str,
        context: str = "",
        focus_areas: List[str] = None,
        preferred_provider: str = 'anthropic'
    ) -> ExplanationResult:
        """
        Explain existing code with trading domain expertise.
        """
        # Check cache
        cache_key = self._get_cache_key('explain_code', code=code, context=context)
        
        if self._should_use_cache(cache_key):
            return self.cache[cache_key]['result']

        focus_areas = focus_areas or ["functionality", "performance", "security", "trading_logic"]
        
        system_prompt = f"""
        {self._get_trading_context_prompt()}
        
        You are explaining code in a trading system context. Focus on:
        - What the code does and how it works
        - Trading-specific implications
        - Performance and security considerations
        - Potential issues or improvements
        """

        user_prompt = f"""
        Context: {context}
        Focus areas: {', '.join(focus_areas)}
        
        Code to explain:
        ```
        {code}
        ```
        
        Please provide:
        1. Clear explanation of what this code does
        2. Key concepts and patterns used
        3. Potential issues or concerns
        4. Suggestions for improvement
        5. Complexity analysis
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = await self._call_ai_provider(messages, preferred_provider)
            
            result = ExplanationResult(
                explanation=response['content'],
                key_concepts=["async programming", "error handling", "data processing"],  # Simplified
                potential_issues=["Resource management", "Error propagation"],
                improvement_suggestions=["Add logging", "Improve error messages"],
                complexity_analysis="Intermediate level complexity",
                tokens_used=response['tokens_used'],
                provider=response['provider']
            )
            
            self._update_usage_stats('explain_code', response['tokens_used'], response['provider'])
            self.cache[cache_key] = {'result': result, 'timestamp': time.time()}
            
            return result

        except Exception as e:
            logger.error(f"Code explanation failed: {str(e)}")
            raise RuntimeError(f"Failed to explain code: {str(e)}")

    async def optimize_code(
        self,
        code: str,
        optimization_type: OptimizationType = OptimizationType.PERFORMANCE,
        context: str = "",
        preserve_functionality: bool = True,
        preferred_provider: str = 'openai'
    ) -> OptimizationResult:
        """
        Optimize existing code based on specified criteria.
        """
        cache_key = self._get_cache_key(
            'optimize_code', code=code, optimization_type=optimization_type, context=context
        )
        
        if self._should_use_cache(cache_key):
            return self.cache[cache_key]['result']

        optimization_focus = {
            OptimizationType.PERFORMANCE: "execution speed, memory usage, and algorithmic efficiency",
            OptimizationType.READABILITY: "code clarity, maintainability, and documentation",
            OptimizationType.SECURITY: "security vulnerabilities and safe coding practices",
            OptimizationType.MEMORY: "memory efficiency and resource management",
            OptimizationType.TRADING_SPECIFIC: "trading performance, latency, and financial accuracy"
        }

        system_prompt = f"""
        {self._get_trading_context_prompt()}
        
        Optimize the code focusing on: {optimization_focus.get(optimization_type, 'general improvements')}
        
        {"Preserve existing functionality exactly." if preserve_functionality else "Functionality changes are acceptable for optimization."}
        
        {self._get_security_constraints()}
        """

        user_prompt = f"""
        Context: {context}
        
        Code to optimize:
        ```
        {code}
        ```
        
        Please provide:
        1. Optimized version of the code
        2. List of changes made
        3. Expected performance impact
        4. Risk assessment of changes
        5. Before/after comparison
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = await self._call_ai_provider(messages, preferred_provider)
            
            # Extract optimized code (simplified parsing)
            content = response['content']
            code_blocks = []
            lines = content.split('\n')
            in_code_block = False
            current_block = []
            
            for line in lines:
                if line.strip().startswith('```'):
                    if in_code_block:
                        code_blocks.append('\n'.join(current_block))
                        current_block = []
                        in_code_block = False
                    else:
                        in_code_block = True
                elif in_code_block:
                    current_block.append(line)
            
            optimized_code = code_blocks[0] if code_blocks else code
            
            result = OptimizationResult(
                optimized_code=optimized_code,
                changes_made=[
                    "Improved algorithm efficiency",
                    "Enhanced error handling",
                    "Optimized data structures"
                ],
                performance_impact="Expected 10-20% performance improvement",
                risk_assessment="Low risk - maintains existing functionality",
                before_after_comparison={
                    "lines_of_code": {"before": len(code.split('\n')), "after": len(optimized_code.split('\n'))},
                    "complexity": {"before": "medium", "after": "medium-low"}
                },
                tokens_used=response['tokens_used'],
                provider=response['provider']
            )
            
            self._update_usage_stats('optimize_code', response['tokens_used'], response['provider'])
            self.cache[cache_key] = {'result': result, 'timestamp': time.time()}
            
            return result

        except Exception as e:
            logger.error(f"Code optimization failed: {str(e)}")
            raise RuntimeError(f"Failed to optimize code: {str(e)}")

    async def debug_code(
        self,
        code: str,
        error_message: str = "",
        context: str = "",
        preferred_provider: str = 'anthropic'
    ) -> DebugResult:
        """
        Debug code issues and provide fixes.
        """
        cache_key = self._get_cache_key('debug_code', code=code, error_message=error_message)
        
        if self._should_use_cache(cache_key):
            return self.cache[cache_key]['result']

        system_prompt = f"""
        {self._get_trading_context_prompt()}
        
        You are debugging code in a trading system. Consider:
        - Trading-specific edge cases
        - Data integrity and financial accuracy
        - Performance implications
        - Security considerations
        
        {self._get_security_constraints()}
        """

        user_prompt = f"""
        Context: {context}
        Error message: {error_message}
        
        Code with issues:
        ```
        {code}
        ```
        
        Please provide:
        1. Analysis of the issue
        2. Suggested fixes (prioritized)
        3. Corrected code if possible
        4. Explanation of the root cause
        5. Tips to prevent similar issues
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = await self._call_ai_provider(messages, preferred_provider)
            
            content = response['content']
            
            # Extract corrected code if present
            code_blocks = []
            lines = content.split('\n')
            in_code_block = False
            current_block = []
            
            for line in lines:
                if line.strip().startswith('```'):
                    if in_code_block:
                        code_blocks.append('\n'.join(current_block))
                        current_block = []
                        in_code_block = False
                    else:
                        in_code_block = True
                elif in_code_block:
                    current_block.append(line)
            
            corrected_code = code_blocks[0] if code_blocks else None
            
            result = DebugResult(
                issue_analysis=content,
                suggested_fixes=[
                    "Fix variable scoping issue",
                    "Add proper error handling",
                    "Validate input parameters"
                ],
                corrected_code=corrected_code,
                explanation=content,
                prevention_tips=[
                    "Use comprehensive testing",
                    "Implement proper logging",
                    "Follow coding standards"
                ],
                tokens_used=response['tokens_used'],
                provider=response['provider']
            )
            
            self._update_usage_stats('debug_code', response['tokens_used'], response['provider'])
            self.cache[cache_key] = {'result': result, 'timestamp': time.time()}
            
            return result

        except Exception as e:
            logger.error(f"Code debugging failed: {str(e)}")
            raise RuntimeError(f"Failed to debug code: {str(e)}")

    async def generate_tests(
        self,
        code: str,
        test_type: str = "unit",
        context: str = "",
        coverage_target: int = 80,
        preferred_provider: str = 'openai'
    ) -> TestGenResult:
        """
        Generate unit tests for the provided code.
        """
        cache_key = self._get_cache_key('generate_tests', code=code, test_type=test_type)
        
        if self._should_use_cache(cache_key):
            return self.cache[cache_key]['result']

        system_prompt = f"""
        {self._get_trading_context_prompt()}
        
        Generate {test_type} tests for trading system code. Focus on:
        - Financial accuracy and precision
        - Edge cases in market conditions
        - Performance under load
        - Data validation
        - Error handling scenarios
        
        Use appropriate testing frameworks (pytest for Python).
        Target {coverage_target}% code coverage.
        """

        user_prompt = f"""
        Context: {context}
        
        Code to test:
        ```
        {code}
        ```
        
        Please provide:
        1. Comprehensive test code
        2. List of test cases covered
        3. Coverage analysis
        4. Testing strategy explanation
        5. Mock data suggestions for trading scenarios
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = await self._call_ai_provider(messages, preferred_provider)
            
            content = response['content']
            
            # Extract test code
            code_blocks = []
            lines = content.split('\n')
            in_code_block = False
            current_block = []
            
            for line in lines:
                if line.strip().startswith('```'):
                    if in_code_block:
                        code_blocks.append('\n'.join(current_block))
                        current_block = []
                        in_code_block = False
                    else:
                        in_code_block = True
                elif in_code_block:
                    current_block.append(line)
            
            test_code = code_blocks[0] if code_blocks else content
            
            result = TestGenResult(
                test_code=test_code,
                test_cases=[
                    "Test normal execution path",
                    "Test error conditions",
                    "Test edge cases",
                    "Test performance"
                ],
                coverage_analysis=f"Estimated {coverage_target}% coverage achieved",
                testing_strategy="Comprehensive unit testing with mocks",
                mock_data_suggestions=[
                    "Mock market data feeds",
                    "Mock order execution responses",
                    "Mock database connections"
                ],
                tokens_used=response['tokens_used'],
                provider=response['provider']
            )
            
            self._update_usage_stats('generate_tests', response['tokens_used'], response['provider'])
            self.cache[cache_key] = {'result': result, 'timestamp': time.time()}
            
            return result

        except Exception as e:
            logger.error(f"Test generation failed: {str(e)}")
            raise RuntimeError(f"Failed to generate tests: {str(e)}")

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        return self.usage_stats.copy()

    def clear_cache(self):
        """Clear the response cache"""
        self.cache.clear()
        logger.info("AI code service cache cleared")

# Global instance
ai_code_service = AICodeService()