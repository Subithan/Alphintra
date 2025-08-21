"""
Code analysis service for syntax checking, validation, and autocompletion.
"""

import ast
import inspect
import keyword
import re
from typing import Dict, List, Optional, Any, Tuple, Set
import logging
import builtins

from app.services.execution_engine import CodeValidator
from app.sdk import BaseStrategy, MarketData, Portfolio, OrderManager, RiskManager


class CodeCompletionItem:
    """Represents a code completion item."""
    
    def __init__(self, label: str, kind: str, detail: str = "", 
                 documentation: str = "", insert_text: str = None):
        self.label = label
        self.kind = kind  # 'function', 'method', 'property', 'variable', 'class', 'module', 'keyword'
        self.detail = detail
        self.documentation = documentation
        self.insert_text = insert_text or label
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "kind": self.kind,
            "detail": self.detail,
            "documentation": self.documentation,
            "insert_text": self.insert_text
        }


class CodeAnalysisService:
    """Service for code analysis, validation, and autocompletion."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validator = CodeValidator()
        
        # SDK analysis
        self._analyze_sdk()
        
        # Keywords and built-ins
        self.python_keywords = keyword.kwlist
        self.builtin_functions = dir(builtins)
        
        # Code patterns for suggestions
        self.common_patterns = self._get_common_patterns()
    
    def _analyze_sdk(self):
        """Analyze the SDK to build completion items."""
        self.sdk_completions = {}
        
        # Analyze BaseStrategy
        self.sdk_completions['BaseStrategy'] = self._analyze_class(BaseStrategy)
        
        # Analyze SDK components
        self.sdk_completions['MarketData'] = self._analyze_class(MarketData)
        self.sdk_completions['Portfolio'] = self._analyze_class(Portfolio)
        self.sdk_completions['OrderManager'] = self._analyze_class(OrderManager)
        self.sdk_completions['RiskManager'] = self._analyze_class(RiskManager)
        
        # Common context variables
        self.context_completions = [
            CodeCompletionItem("data", "variable", "MarketData", "Access to market data and indicators"),
            CodeCompletionItem("portfolio", "variable", "Portfolio", "Portfolio management and positions"),
            CodeCompletionItem("orders", "variable", "OrderManager", "Order management and execution"),
            CodeCompletionItem("risk", "variable", "RiskManager", "Risk management and limits"),
            CodeCompletionItem("context", "variable", "StrategyContext", "Full strategy context"),
            CodeCompletionItem("log", "method", "log(message, level='INFO')", "Log a message"),
            CodeCompletionItem("get_parameter", "method", "get_parameter(name, default=None)", "Get strategy parameter"),
            CodeCompletionItem("set_variable", "method", "set_variable(name, value)", "Set strategy variable"),
            CodeCompletionItem("get_variable", "method", "get_variable(name, default=None)", "Get strategy variable"),
            CodeCompletionItem("record_metric", "method", "record_metric(name, value)", "Record custom metric")
        ]
    
    def _analyze_class(self, cls) -> List[CodeCompletionItem]:
        """Analyze a class to extract completion items."""
        completions = []
        
        # Get class methods and properties
        for name, member in inspect.getmembers(cls):
            if name.startswith('_'):
                continue
            
            if inspect.ismethod(member) or inspect.isfunction(member):
                # Get method signature
                try:
                    sig = inspect.signature(member)
                    params = []
                    for param_name, param in sig.parameters.items():
                        if param_name == 'self':
                            continue
                        
                        param_str = param_name
                        if param.default != inspect.Parameter.empty:
                            if isinstance(param.default, str):
                                param_str += f'="{param.default}"'
                            else:
                                param_str += f'={param.default}'
                        elif param.annotation != inspect.Parameter.empty:
                            param_str += f': {param.annotation.__name__ if hasattr(param.annotation, "__name__") else param.annotation}'
                        
                        params.append(param_str)
                    
                    signature = f"{name}({', '.join(params)})"
                    doc = inspect.getdoc(member) or ""
                    
                    completions.append(CodeCompletionItem(
                        label=name,
                        kind="method",
                        detail=signature,
                        documentation=doc,
                        insert_text=f"{name}(${{1}})"  # LSP snippet format
                    ))
                except Exception:
                    # Fallback for methods without inspectable signatures
                    completions.append(CodeCompletionItem(
                        label=name,
                        kind="method",
                        detail=f"{name}()",
                        documentation=inspect.getdoc(member) or ""
                    ))
            
            elif inspect.isdatadescriptor(member) or not callable(member):
                # Property or variable
                completions.append(CodeCompletionItem(
                    label=name,
                    kind="property",
                    detail=str(type(member).__name__),
                    documentation=inspect.getdoc(member) or ""
                ))
        
        return completions
    
    def _get_common_patterns(self) -> List[CodeCompletionItem]:
        """Get common code patterns and snippets."""
        return [
            CodeCompletionItem(
                label="initialize_method",
                kind="snippet",
                detail="def initialize(self):",
                documentation="Initialize strategy method template",
                insert_text="""def initialize(self):
    \"\"\"Initialize strategy variables and parameters.\"\"\"
    # Get parameters
    ${1:# parameter = self.get_parameter("parameter_name", default_value)}
    
    # Initialize variables
    ${2:# self.set_variable("variable_name", initial_value)}
    
    self.log("Strategy initialized")"""
            ),
            CodeCompletionItem(
                label="on_bar_method",
                kind="snippet",
                detail="def on_bar(self):",
                documentation="Main strategy logic method template",
                insert_text="""def on_bar(self):
    \"\"\"Execute strategy logic for each bar.\"\"\"
    # Get current data
    ${1:current_price = self.data.get_current_price("BTCUSD")}
    
    # Strategy logic
    ${2:# Add your trading logic here}
    
    # Record metrics
    ${3:# self.record_metric("metric_name", value)}"""
            ),
            CodeCompletionItem(
                label="market_order",
                kind="snippet",
                detail="Market order template",
                documentation="Place a market order",
                insert_text='self.orders.market_order("${1:BTCUSD}", ${2:quantity}, "${3:buy}")'
            ),
            CodeCompletionItem(
                label="limit_order",
                kind="snippet",
                detail="Limit order template", 
                documentation="Place a limit order",
                insert_text='self.orders.limit_order("${1:BTCUSD}", ${2:quantity}, "${3:buy}", ${4:price})'
            ),
            CodeCompletionItem(
                label="get_position",
                kind="snippet",
                detail="Get position template",
                documentation="Get current position for symbol",
                insert_text='position = self.portfolio.get_position("${1:BTCUSD}")'
            ),
            CodeCompletionItem(
                label="sma_indicator",
                kind="snippet",
                detail="Simple Moving Average",
                documentation="Calculate Simple Moving Average",
                insert_text='sma = self.data.sma("${1:BTCUSD}", ${2:20})'
            ),
            CodeCompletionItem(
                label="ema_indicator",
                kind="snippet",
                detail="Exponential Moving Average",
                documentation="Calculate Exponential Moving Average", 
                insert_text='ema = self.data.ema("${1:BTCUSD}", ${2:20})'
            ),
            CodeCompletionItem(
                label="rsi_indicator",
                kind="snippet",
                detail="RSI Indicator",
                documentation="Calculate Relative Strength Index",
                insert_text='rsi = self.data.rsi("${1:BTCUSD}", ${2:14})'
            ),
            CodeCompletionItem(
                label="bollinger_bands",
                kind="snippet",
                detail="Bollinger Bands",
                documentation="Calculate Bollinger Bands",
                insert_text='bb = self.data.bollinger_bands("${1:BTCUSD}", ${2:20}, ${3:2.0})'
            ),
            CodeCompletionItem(
                label="strategy_class",
                kind="snippet",
                detail="Strategy class template",
                documentation="Complete strategy class template",
                insert_text="""class ${1:MyStrategy}(BaseStrategy):
    def __init__(self):
        super().__init__(
            name="${2:My Strategy}",
            description="${3:Strategy description}"
        )
        self.author = "${4:Your Name}"
        self.tags = [${5:"tag1", "tag2"}]
        self.category = "${6:custom}"
    
    def initialize(self):
        \"\"\"Initialize strategy.\"\"\"
        ${7:# Add initialization code}
        pass
    
    def on_bar(self):
        \"\"\"Main strategy logic.\"\"\"
        ${8:# Add strategy logic}
        pass"""
            )
        ]
    
    def validate_code(self, code: str) -> Dict[str, Any]:
        """
        Comprehensive code validation.
        
        Args:
            code: Python code to validate
            
        Returns:
            Validation result with errors, warnings, and suggestions
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": [],
            "metrics": {}
        }
        
        try:
            # Basic syntax validation using AST
            tree = ast.parse(code)
            
            # Security validation
            security_result = self.validator.validate_code(code)
            result["errors"].extend(security_result.get("errors", []))
            result["warnings"].extend(security_result.get("warnings", []))
            
            # Strategy-specific validation
            strategy_validation = self._validate_strategy_structure(tree)
            result["errors"].extend(strategy_validation.get("errors", []))
            result["warnings"].extend(strategy_validation.get("warnings", []))
            result["suggestions"].extend(strategy_validation.get("suggestions", []))
            
            # Code quality checks
            quality_checks = self._analyze_code_quality(tree, code)
            result["warnings"].extend(quality_checks.get("warnings", []))
            result["suggestions"].extend(quality_checks.get("suggestions", []))
            result["metrics"] = quality_checks.get("metrics", {})
            
            # Set overall validity
            result["valid"] = len(result["errors"]) == 0
            
        except SyntaxError as e:
            result["valid"] = False
            result["errors"].append({
                "type": "SyntaxError",
                "message": str(e),
                "line": e.lineno,
                "column": e.offset
            })
        except Exception as e:
            result["valid"] = False
            result["errors"].append({
                "type": "ValidationError",
                "message": f"Validation failed: {str(e)}"
            })
        
        return result
    
    def _validate_strategy_structure(self, tree: ast.AST) -> Dict[str, List]:
        """Validate strategy-specific structure."""
        errors = []
        warnings = []
        suggestions = []
        
        # Find strategy classes
        strategy_classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if inherits from BaseStrategy
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == "BaseStrategy":
                        strategy_classes.append(node)
                        break
        
        if not strategy_classes:
            warnings.append("No strategy class found that inherits from BaseStrategy")
        elif len(strategy_classes) > 1:
            warnings.append("Multiple strategy classes found - only one will be used")
        
        # Validate strategy class structure
        for strategy_class in strategy_classes:
            class_validation = self._validate_strategy_class(strategy_class)
            errors.extend(class_validation.get("errors", []))
            warnings.extend(class_validation.get("warnings", []))
            suggestions.extend(class_validation.get("suggestions", []))
        
        return {
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions
        }
    
    def _validate_strategy_class(self, class_node: ast.ClassDef) -> Dict[str, List]:
        """Validate individual strategy class."""
        errors = []
        warnings = []
        suggestions = []
        
        # Check for required methods
        methods = {node.name: node for node in class_node.body if isinstance(node, ast.FunctionDef)}
        
        required_methods = ["initialize", "on_bar"]
        for method_name in required_methods:
            if method_name not in methods:
                errors.append(f"Required method '{method_name}' not found in strategy class")
        
        # Check method signatures
        if "initialize" in methods:
            init_method = methods["initialize"]
            if len(init_method.args.args) != 1:  # Should only have 'self'
                warnings.append("initialize() method should not take additional parameters")
        
        if "on_bar" in methods:
            on_bar_method = methods["on_bar"]
            if len(on_bar_method.args.args) != 1:  # Should only have 'self'
                warnings.append("on_bar() method should not take additional parameters")
        
        # Check for common patterns
        has_parameter_usage = False
        has_variable_usage = False
        has_logging = False
        
        for node in ast.walk(class_node):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "get_parameter":
                    has_parameter_usage = True
                elif node.func.attr == "set_variable" or node.func.attr == "get_variable":
                    has_variable_usage = True
                elif node.func.attr == "log":
                    has_logging = True
        
        if not has_parameter_usage:
            suggestions.append("Consider using self.get_parameter() to make your strategy configurable")
        
        if not has_variable_usage:
            suggestions.append("Consider using self.set_variable() and self.get_variable() for state management")
        
        if not has_logging:
            suggestions.append("Consider adding self.log() calls for debugging and monitoring")
        
        return {
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions
        }
    
    def _analyze_code_quality(self, tree: ast.AST, code: str) -> Dict[str, Any]:
        """Analyze code quality and provide suggestions."""
        warnings = []
        suggestions = []
        metrics = {}
        
        lines = code.split('\n')
        metrics["line_count"] = len(lines)
        metrics["non_empty_lines"] = len([line for line in lines if line.strip()])
        
        # Complexity analysis
        complexity = self._calculate_complexity(tree)
        metrics["complexity"] = complexity
        
        if complexity > 10:
            warnings.append(f"High complexity ({complexity}) - consider breaking down into smaller methods")
        
        # Check for long methods
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                method_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                if method_lines > 50:
                    warnings.append(f"Method '{node.name}' is very long ({method_lines} lines) - consider refactoring")
        
        # Check for magic numbers
        magic_numbers = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                if node.value not in [0, 1, -1, 100] and abs(node.value) > 1:
                    magic_numbers.append(node.value)
        
        if magic_numbers:
            suggestions.append(f"Consider using named constants for magic numbers: {set(magic_numbers)}")
        
        # Check for TODO/FIXME comments
        todo_pattern = re.compile(r'#.*\b(TODO|FIXME|XXX|HACK)\b', re.IGNORECASE)
        todos = []
        for i, line in enumerate(lines, 1):
            if todo_pattern.search(line):
                todos.append(f"Line {i}: {line.strip()}")
        
        if todos:
            suggestions.extend([f"TODO/FIXME found: {todo}" for todo in todos])
        
        return {
            "warnings": warnings,
            "suggestions": suggestions,
            "metrics": metrics
        }
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            # Control flow statements increase complexity
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler, 
                               ast.With, ast.AsyncWith, ast.AsyncFor)):
                complexity += 1
            # Boolean operators in conditions
            elif isinstance(node, (ast.BoolOp)):
                complexity += len(node.values) - 1
        
        return complexity
    
    def get_completions(self, code: str, line: int, column: int) -> List[Dict[str, Any]]:
        """
        Get code completions at the specified position.
        
        Args:
            code: Current code
            line: Line number (0-based)
            column: Column number (0-based)
            
        Returns:
            List of completion items
        """
        completions = []
        
        try:
            lines = code.split('\n')
            if line >= len(lines):
                return []
            
            current_line = lines[line]
            text_before_cursor = current_line[:column]
            
            # Determine completion context
            context = self._get_completion_context(text_before_cursor, lines[:line])
            
            if context["type"] == "method_call":
                # Complete methods for object
                if context["object"] in ["self.data", "data"]:
                    completions.extend(self.sdk_completions.get("MarketData", []))
                elif context["object"] in ["self.portfolio", "portfolio"]:
                    completions.extend(self.sdk_completions.get("Portfolio", []))
                elif context["object"] in ["self.orders", "orders"]:
                    completions.extend(self.sdk_completions.get("OrderManager", []))
                elif context["object"] in ["self.risk", "risk"]:
                    completions.extend(self.sdk_completions.get("RiskManager", []))
                elif context["object"] == "self":
                    completions.extend(self.context_completions)
                    completions.extend(self.sdk_completions.get("BaseStrategy", []))
            
            elif context["type"] == "general":
                # General completions
                
                # Python keywords
                for keyword_name in self.python_keywords:
                    if keyword_name.startswith(context.get("prefix", "")):
                        completions.append(CodeCompletionItem(
                            label=keyword_name,
                            kind="keyword",
                            detail="Python keyword"
                        ))
                
                # Built-in functions
                for builtin_name in self.builtin_functions:
                    if not builtin_name.startswith('_') and builtin_name.startswith(context.get("prefix", "")):
                        completions.append(CodeCompletionItem(
                            label=builtin_name,
                            kind="function", 
                            detail="Built-in function"
                        ))
                
                # Context variables
                completions.extend(self.context_completions)
                
                # Common patterns
                completions.extend(self.common_patterns)
            
            # Convert to dictionaries and filter by prefix
            prefix = context.get("prefix", "").lower()
            filtered_completions = []
            
            for completion in completions:
                if isinstance(completion, CodeCompletionItem):
                    completion_dict = completion.to_dict()
                else:
                    completion_dict = completion
                
                if not prefix or completion_dict["label"].lower().startswith(prefix):
                    filtered_completions.append(completion_dict)
            
            # Sort by relevance
            filtered_completions.sort(key=lambda x: (
                0 if x["label"].lower().startswith(prefix) else 1,
                len(x["label"]),
                x["label"].lower()
            ))
            
            return filtered_completions[:50]  # Limit results
            
        except Exception as e:
            self.logger.error(f"Failed to get completions: {str(e)}")
            return []
    
    def _get_completion_context(self, text_before_cursor: str, previous_lines: List[str]) -> Dict[str, Any]:
        """Determine the completion context."""
        
        # Check for method calls
        method_call_pattern = r'(\w+(?:\.\w+)*)\.$'
        match = re.search(method_call_pattern, text_before_cursor)
        if match:
            return {
                "type": "method_call",
                "object": match.group(1),
                "prefix": ""
            }
        
        # Check for partial method calls
        partial_method_pattern = r'(\w+(?:\.\w+)*\.(\w*))$'
        match = re.search(partial_method_pattern, text_before_cursor)
        if match:
            return {
                "type": "method_call",
                "object": match.group(1).rsplit('.', 1)[0],
                "prefix": match.group(2)
            }
        
        # Check for variable/function names
        word_pattern = r'(\w+)$'
        match = re.search(word_pattern, text_before_cursor)
        if match:
            return {
                "type": "general",
                "prefix": match.group(1)
            }
        
        return {"type": "general", "prefix": ""}
    
    def get_hover_info(self, code: str, line: int, column: int) -> Optional[Dict[str, Any]]:
        """
        Get hover information for the symbol at the specified position.
        
        Args:
            code: Current code
            line: Line number (0-based)
            column: Column number (0-based)
            
        Returns:
            Hover information or None
        """
        try:
            lines = code.split('\n')
            if line >= len(lines):
                return None
            
            current_line = lines[line]
            
            # Find the word at the cursor position
            word_start = column
            word_end = column
            
            # Move backwards to find word start
            while word_start > 0 and (current_line[word_start - 1].isalnum() or current_line[word_start - 1] == '_'):
                word_start -= 1
            
            # Move forwards to find word end
            while word_end < len(current_line) and (current_line[word_end].isalnum() or current_line[word_end] == '_'):
                word_end += 1
            
            if word_start == word_end:
                return None
            
            word = current_line[word_start:word_end]
            
            # Look up hover information
            hover_info = self._get_symbol_info(word, current_line, lines)
            
            if hover_info:
                return {
                    "word": word,
                    "range": {
                        "start": {"line": line, "character": word_start},
                        "end": {"line": line, "character": word_end}
                    },
                    "info": hover_info
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get hover info: {str(e)}")
            return None
    
    def _get_symbol_info(self, symbol: str, current_line: str, all_lines: List[str]) -> Optional[Dict[str, Any]]:
        """Get information about a symbol."""
        
        # Check if it's a method call on a known object
        method_call_pattern = r'(\w+(?:\.\w+)*)\.' + re.escape(symbol)
        match = re.search(method_call_pattern, current_line)
        
        if match:
            object_path = match.group(1)
            
            # Look up in SDK completions
            sdk_mappings = {
                "self.data": "MarketData",
                "data": "MarketData",
                "self.portfolio": "Portfolio", 
                "portfolio": "Portfolio",
                "self.orders": "OrderManager",
                "orders": "OrderManager",
                "self.risk": "RiskManager",
                "risk": "RiskManager"
            }
            
            sdk_class = sdk_mappings.get(object_path)
            if sdk_class and sdk_class in self.sdk_completions:
                for completion in self.sdk_completions[sdk_class]:
                    if completion.label == symbol:
                        return {
                            "type": "method",
                            "signature": completion.detail,
                            "documentation": completion.documentation,
                            "class": sdk_class
                        }
        
        # Check Python keywords
        if symbol in self.python_keywords:
            return {
                "type": "keyword",
                "documentation": f"Python keyword: {symbol}"
            }
        
        # Check built-in functions
        if symbol in self.builtin_functions:
            try:
                builtin_obj = getattr(builtins, symbol)
                doc = inspect.getdoc(builtin_obj) or ""
                return {
                    "type": "builtin",
                    "documentation": doc
                }
            except:
                pass
        
        return None
    
    def get_diagnostics(self, code: str) -> List[Dict[str, Any]]:
        """
        Get diagnostic information (errors, warnings) for the code.
        
        Args:
            code: Code to analyze
            
        Returns:
            List of diagnostic items
        """
        diagnostics = []
        
        # Validate code
        validation_result = self.validate_code(code)
        
        # Convert errors to diagnostics
        for error in validation_result.get("errors", []):
            diagnostic = {
                "severity": "error",
                "message": error.get("message", str(error)),
                "source": "ai-ml-strategy-service"
            }
            
            if isinstance(error, dict) and "line" in error:
                diagnostic["range"] = {
                    "start": {"line": error["line"] - 1, "character": error.get("column", 0)},
                    "end": {"line": error["line"] - 1, "character": error.get("column", 0) + 1}
                }
            
            diagnostics.append(diagnostic)
        
        # Convert warnings to diagnostics
        for warning in validation_result.get("warnings", []):
            diagnostic = {
                "severity": "warning",
                "message": str(warning),
                "source": "ai-ml-strategy-service"
            }
            diagnostics.append(diagnostic)
        
        # Convert suggestions to info diagnostics
        for suggestion in validation_result.get("suggestions", []):
            diagnostic = {
                "severity": "info",
                "message": str(suggestion),
                "source": "ai-ml-strategy-service"
            }
            diagnostics.append(diagnostic)
        
        return diagnostics