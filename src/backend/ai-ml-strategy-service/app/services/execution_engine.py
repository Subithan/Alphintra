"""
Secure code execution engine for trading strategies.
"""

import ast
import sys
import traceback
import contextlib
import io
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Callable
from decimal import Decimal
import logging
import inspect
import types
import builtins

from app.core.config import settings
from app.sdk.strategy import BaseStrategy, StrategyContext
from app.sdk.data import MarketData
from app.sdk.portfolio import Portfolio
from app.sdk.orders import OrderManager
from app.sdk.risk import RiskManager


class SecurityError(Exception):
    """Raised when code violates security constraints."""
    pass


class ExecutionTimeoutError(Exception):
    """Raised when code execution exceeds timeout."""
    pass


class CodeValidator:
    """Validates Python code for security and safety."""
    
    # Dangerous modules and functions
    BLOCKED_MODULES = {
        'os', 'sys', 'subprocess', 'shutil', 'glob', 'socket', 'urllib',
        'requests', 'http', 'ftplib', 'smtplib', 'poplib', 'imaplib',
        'telnetlib', 'pickle', 'marshal', 'shelve', 'dbm', 'sqlite3',
        'threading', 'multiprocessing', 'asyncio', 'concurrent',
        'ctypes', 'mmap', 'tempfile', 'webbrowser', '__main__'
    }
    
    BLOCKED_BUILTINS = {
        'exec', 'eval', 'compile', '__import__', 'open', 'input', 'raw_input',
        'file', 'reload', 'vars', 'locals', 'globals', 'dir', 'help',
        'exit', 'quit', 'copyright', 'credits', 'license'
    }
    
    ALLOWED_IMPORTS = {
        'math', 'statistics', 'decimal', 'fractions', 'random', 'datetime',
        'time', 'calendar', 'collections', 'itertools', 'functools',
        'operator', 'copy', 'json', 're', 'string', 'unicodedata',
        'numpy', 'pandas', 'scipy', 'sklearn', 'matplotlib', 'seaborn',
        'plotly', 'ta', 'talib'  # Technical analysis libraries
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_code(self, code: str) -> Dict[str, Any]:
        """
        Validate code for security and safety.
        
        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []
        
        try:
            # Parse the code into AST
            tree = ast.parse(code)
            
            # Analyze the AST
            self._analyze_ast(tree, errors, warnings)
            
        except SyntaxError as e:
            errors.append(f"Syntax error: {e}")
        except Exception as e:
            errors.append(f"Parse error: {e}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _analyze_ast(self, node: ast.AST, errors: List[str], warnings: List[str]):
        """Recursively analyze AST nodes for security violations."""
        
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name.split('.')[0]
                if module_name in self.BLOCKED_MODULES:
                    errors.append(f"Blocked module import: {alias.name}")
                elif module_name not in self.ALLOWED_IMPORTS:
                    warnings.append(f"Unknown module import: {alias.name}")
        
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module.split('.')[0] if node.module else ''
            if module_name in self.BLOCKED_MODULES:
                errors.append(f"Blocked module import: {module_name}")
            elif module_name not in self.ALLOWED_IMPORTS and module_name != '':
                warnings.append(f"Unknown module import: {module_name}")
        
        elif isinstance(node, ast.Call):
            # Check for dangerous function calls
            if isinstance(node.func, ast.Name):
                if node.func.id in self.BLOCKED_BUILTINS:
                    errors.append(f"Blocked builtin function: {node.func.id}")
            elif isinstance(node.func, ast.Attribute):
                # Check for dangerous method calls
                if node.func.attr in ['system', 'popen', 'spawn']:
                    errors.append(f"Blocked method call: {node.func.attr}")
        
        elif isinstance(node, ast.Attribute):
            # Check for dangerous attribute access
            if node.attr in ['__globals__', '__locals__', '__dict__', '__class__']:
                errors.append(f"Blocked attribute access: {node.attr}")
        
        elif isinstance(node, ast.FunctionDef):
            # Check function definitions
            if node.name.startswith('__') and node.name.endswith('__'):
                warnings.append(f"Magic method definition: {node.name}")
        
        # Recursively check child nodes
        for child in ast.iter_child_nodes(node):
            self._analyze_ast(child, errors, warnings)


class SandboxEnvironment:
    """Provides a sandboxed environment for code execution."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._restricted_builtins = self._create_restricted_builtins()
    
    def _create_restricted_builtins(self) -> Dict[str, Any]:
        """Create a restricted set of builtin functions."""
        safe_builtins = {}
        
        # Allow safe builtins
        safe_builtin_names = {
            'abs', 'all', 'any', 'bin', 'bool', 'bytearray', 'bytes',
            'callable', 'chr', 'classmethod', 'complex', 'dict', 'divmod',
            'enumerate', 'filter', 'float', 'format', 'frozenset', 'getattr',
            'hasattr', 'hash', 'hex', 'id', 'int', 'isinstance', 'issubclass',
            'iter', 'len', 'list', 'map', 'max', 'min', 'next', 'object',
            'oct', 'ord', 'pow', 'property', 'range', 'repr', 'reversed',
            'round', 'set', 'setattr', 'slice', 'sorted', 'staticmethod',
            'str', 'sum', 'super', 'tuple', 'type', 'zip'
        }
        
        for name in safe_builtin_names:
            if hasattr(builtins, name):
                safe_builtins[name] = getattr(builtins, name)
        
        # Add safe print function
        safe_builtins['print'] = self._safe_print
        
        return safe_builtins
    
    def _safe_print(self, *args, **kwargs):
        """Safe print function that captures output."""
        # Redirect to string buffer instead of stdout
        output = io.StringIO()
        print(*args, file=output, **kwargs)
        
        # Log the output
        message = output.getvalue().strip()
        if message:
            self.logger.info(f"Strategy output: {message}")
        
        return message
    
    def create_sandbox_globals(self, strategy_context: StrategyContext) -> Dict[str, Any]:
        """Create a global namespace for sandbox execution."""
        
        # Start with restricted builtins
        sandbox_globals = {
            '__builtins__': self._restricted_builtins,
            '__name__': '__sandbox__',
            '__file__': '<sandbox>',
        }
        
        # Add allowed modules
        allowed_modules = {
            'math': __import__('math'),
            'statistics': __import__('statistics'),
            'decimal': __import__('decimal'),
            'datetime': __import__('datetime'),
            'time': __import__('time'),
            'random': __import__('random'),
            'json': __import__('json'),
            're': __import__('re'),
            'collections': __import__('collections'),
            'itertools': __import__('itertools'),
            'functools': __import__('functools'),
        }
        
        # Try to import optional modules
        optional_modules = ['numpy', 'pandas', 'scipy', 'sklearn']
        for module_name in optional_modules:
            try:
                allowed_modules[module_name] = __import__(module_name)
            except ImportError:
                pass  # Module not available
        
        sandbox_globals.update(allowed_modules)
        
        # Add SDK components
        from app.sdk import (
            BaseStrategy, MarketData, Portfolio, OrderManager, RiskManager,
            TechnicalIndicators, OrderType, OrderStatus, OrderSide
        )
        
        sandbox_globals.update({
            'BaseStrategy': BaseStrategy,
            'MarketData': MarketData,
            'Portfolio': Portfolio,
            'OrderManager': OrderManager,
            'RiskManager': RiskManager,
            'TechnicalIndicators': TechnicalIndicators,
            'OrderType': OrderType,
            'OrderStatus': OrderStatus,
            'OrderSide': OrderSide,
            'Decimal': Decimal,
        })
        
        # Add strategy context components
        if strategy_context:
            sandbox_globals.update({
                'data': strategy_context.market_data,
                'portfolio': strategy_context.portfolio,
                'orders': strategy_context.order_manager,
                'risk': strategy_context.risk_manager,
                'context': strategy_context,
            })
        
        return sandbox_globals


class ExecutionEngine:
    """Manages strategy code execution with security and monitoring."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validator = CodeValidator()
        self.sandbox = SandboxEnvironment()
        
        # Execution tracking
        self.active_executions: Dict[str, Dict] = {}
        self.execution_history: List[Dict] = []
        
        # Performance limits
        self.max_execution_time = settings.CODE_EXECUTION_TIMEOUT
        self.max_memory_mb = 256  # MB
        self.max_iterations = 1000000
    
    def validate_strategy_code(self, code: str) -> Dict[str, Any]:
        """Validate strategy code before execution."""
        return self.validator.validate_code(code)
    
    def compile_strategy(self, code: str, strategy_name: str = "Strategy") -> Dict[str, Any]:
        """
        Compile strategy code and extract the strategy class.
        
        Returns:
            Dictionary with compilation results
        """
        try:
            # Validate code first
            validation = self.validate_strategy_code(code)
            if not validation["valid"]:
                return {
                    "success": False,
                    "error": "Code validation failed",
                    "details": validation
                }
            
            # Compile the code
            compiled_code = compile(code, f"<strategy:{strategy_name}>", "exec")
            
            # Execute in sandbox to extract classes
            sandbox_globals = self.sandbox.create_sandbox_globals(None)
            exec(compiled_code, sandbox_globals)
            
            # Find strategy classes
            strategy_classes = []
            for name, obj in sandbox_globals.items():
                if (isinstance(obj, type) and 
                    issubclass(obj, BaseStrategy) and 
                    obj != BaseStrategy):
                    strategy_classes.append({
                        "name": name,
                        "class": obj,
                        "info": obj().get_strategy_info() if hasattr(obj, 'get_strategy_info') else {}
                    })
            
            if not strategy_classes:
                return {
                    "success": False,
                    "error": "No strategy class found that inherits from BaseStrategy"
                }
            
            return {
                "success": True,
                "strategy_classes": strategy_classes,
                "compiled_code": compiled_code,
                "warnings": validation.get("warnings", [])
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Compilation failed: {str(e)}",
                "traceback": traceback.format_exc()
            }
    
    def execute_strategy(self, strategy_code: str, strategy_context: StrategyContext,
                        execution_id: str = None) -> Dict[str, Any]:
        """
        Execute a strategy with the given context.
        
        Args:
            strategy_code: The strategy code to execute
            strategy_context: Context with market data, portfolio, etc.
            execution_id: Unique identifier for this execution
            
        Returns:
            Dictionary with execution results
        """
        execution_id = execution_id or f"exec_{int(time.time())}"
        
        start_time = datetime.now()
        
        # Track execution
        execution_info = {
            "id": execution_id,
            "start_time": start_time,
            "status": "running",
            "strategy_id": strategy_context.strategy_id,
            "user_id": strategy_context.user_id
        }
        self.active_executions[execution_id] = execution_info
        
        try:
            # Compile strategy
            compilation_result = self.compile_strategy(strategy_code)
            if not compilation_result["success"]:
                raise Exception(f"Compilation failed: {compilation_result['error']}")
            
            # Get the strategy class
            strategy_classes = compilation_result["strategy_classes"]
            if not strategy_classes:
                raise Exception("No strategy class found")
            
            # Use the first strategy class found
            strategy_class = strategy_classes[0]["class"]
            
            # Create strategy instance
            strategy_instance = strategy_class()
            strategy_instance.set_context(strategy_context)
            
            # Execute with timeout
            result = self._execute_with_timeout(
                strategy_instance, 
                strategy_context, 
                self.max_execution_time
            )
            
            execution_info["status"] = "completed"
            execution_info["result"] = result
            
            return {
                "success": True,
                "execution_id": execution_id,
                "result": result,
                "warnings": compilation_result.get("warnings", []),
                "execution_time": (datetime.now() - start_time).total_seconds()
            }
            
        except ExecutionTimeoutError:
            execution_info["status"] = "timeout"
            return {
                "success": False,
                "execution_id": execution_id,
                "error": "Execution timeout",
                "execution_time": (datetime.now() - start_time).total_seconds()
            }
            
        except Exception as e:
            execution_info["status"] = "error"
            execution_info["error"] = str(e)
            
            return {
                "success": False,
                "execution_id": execution_id,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "execution_time": (datetime.now() - start_time).total_seconds()
            }
            
        finally:
            # Move to history
            if execution_id in self.active_executions:
                execution_info["end_time"] = datetime.now()
                self.execution_history.append(execution_info.copy())
                del self.active_executions[execution_id]
    
    def _execute_with_timeout(self, strategy: BaseStrategy, context: StrategyContext, 
                            timeout_seconds: int) -> Dict[str, Any]:
        """Execute strategy with timeout protection."""
        
        result = {"status": "unknown"}
        exception_container = [None]
        
        def target():
            try:
                # Initialize strategy
                if not strategy.is_initialized:
                    strategy.initialize()
                    strategy.is_initialized = True
                
                # Run strategy logic
                strategy.is_running = True
                
                # Simulate market data processing
                # In a real implementation, this would iterate through historical data
                # For now, just call on_bar once
                strategy.on_bar()
                
                strategy.is_running = False
                
                # Finalize
                strategy.finalize()
                
                result["status"] = "completed"
                result["metrics"] = context.metrics
                result["variables"] = context.variables
                result["portfolio_stats"] = context.portfolio.get_performance_stats()
                result["order_stats"] = context.order_manager.get_order_stats()
                
            except Exception as e:
                exception_container[0] = e
                result["status"] = "error"
                result["error"] = str(e)
        
        # Run in thread with timeout
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout_seconds)
        
        if thread.is_alive():
            # Thread is still running, execution timed out
            raise ExecutionTimeoutError(f"Execution exceeded {timeout_seconds} seconds")
        
        if exception_container[0]:
            raise exception_container[0]
        
        return result
    
    def stop_execution(self, execution_id: str) -> bool:
        """Stop a running execution."""
        if execution_id in self.active_executions:
            # In a real implementation, this would need more sophisticated
            # thread termination mechanisms
            execution_info = self.active_executions[execution_id]
            execution_info["status"] = "stopped"
            execution_info["end_time"] = datetime.now()
            
            self.execution_history.append(execution_info.copy())
            del self.active_executions[execution_id]
            return True
        
        return False
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an execution."""
        if execution_id in self.active_executions:
            return self.active_executions[execution_id].copy()
        
        # Check history
        for execution in self.execution_history:
            if execution["id"] == execution_id:
                return execution.copy()
        
        return None
    
    def get_active_executions(self) -> List[Dict[str, Any]]:
        """Get all currently active executions."""
        return list(self.active_executions.values())
    
    def cleanup_old_executions(self, max_age_hours: int = 24):
        """Clean up old execution history."""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        self.execution_history = [
            execution for execution in self.execution_history
            if execution.get("end_time", datetime.now()) > cutoff_time
        ]
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        total_executions = len(self.execution_history)
        
        if total_executions == 0:
            return {
                "total_executions": 0,
                "success_rate": 0,
                "average_execution_time": 0,
                "active_executions": len(self.active_executions)
            }
        
        successful = len([e for e in self.execution_history if e.get("status") == "completed"])
        
        # Calculate average execution time
        execution_times = []
        for execution in self.execution_history:
            if "start_time" in execution and "end_time" in execution:
                duration = (execution["end_time"] - execution["start_time"]).total_seconds()
                execution_times.append(duration)
        
        avg_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        return {
            "total_executions": total_executions,
            "successful_executions": successful,
            "success_rate": (successful / total_executions * 100) if total_executions > 0 else 0,
            "average_execution_time": avg_time,
            "active_executions": len(self.active_executions),
            "timeout_executions": len([e for e in self.execution_history if e.get("status") == "timeout"]),
            "error_executions": len([e for e in self.execution_history if e.get("status") == "error"])
        }