import ast
import textwrap
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from . import schemas

@dataclass
class CompilationResult:
    python_code: str
    validation_results: List[schemas.ValidationResult]
    status: str
    error_message: Optional[str] = None

class WorkflowCompiler:
    """Compiles visual workflows into executable Python code"""
    
    def __init__(self):
        self.component_registry = self._initialize_component_registry()
    
    def _initialize_component_registry(self) -> Dict[str, Dict[str, Any]]:
        """Initialize the component registry with all available components"""
        return {
            "dataSource": {
                "name": "Data Source",
                "category": "Data",
                "template": self._data_source_template,
                "inputs": [],
                "outputs": ["data"]
            },
            "technicalIndicator": {
                "name": "Technical Indicator",
                "category": "Indicators", 
                "template": self._technical_indicator_template,
                "inputs": ["data"],
                "outputs": ["value", "signal"]
            },
            "condition": {
                "name": "Condition",
                "category": "Logic",
                "template": self._condition_template,
                "inputs": ["data", "value"],
                "outputs": ["signal"]
            },
            "action": {
                "name": "Action",
                "category": "Trading",
                "template": self._action_template,
                "inputs": ["signal"],
                "outputs": ["order"]
            },
            "logic": {
                "name": "Logic Gate",
                "category": "Logic",
                "template": self._logic_template,
                "inputs": ["signal1", "signal2"],
                "outputs": ["signal"]
            },
            "risk": {
                "name": "Risk Management",
                "category": "Risk",
                "template": self._risk_template,
                "inputs": ["data", "signal"],
                "outputs": ["adjusted_signal"]
            }
        }
    
    async def compile(self, workflow_id: str, nodes: List[Dict], edges: List[Dict], parameters: Dict[str, Any]) -> CompilationResult:
        """Compile a workflow into Python code"""
        try:
            # Validate workflow structure
            validation_results = await self._validate_workflow(nodes, edges)
            
            # Check for critical validation failures
            critical_failures = [r for r in validation_results if r.status == "failed"]
            if critical_failures:
                return CompilationResult(
                    python_code="",
                    validation_results=validation_results,
                    status="failed",
                    error_message="Workflow validation failed"
                )
            
            # Generate Python code
            python_code = await self._generate_python_code(workflow_id, nodes, edges, parameters)
            
            # Validate generated code
            code_validation = await self._validate_python_code(python_code)
            validation_results.extend(code_validation)
            
            return CompilationResult(
                python_code=python_code,
                validation_results=validation_results,
                status="success"
            )
            
        except Exception as e:
            return CompilationResult(
                python_code="",
                validation_results=[],
                status="failed",
                error_message=str(e)
            )
    
    async def _validate_workflow(self, nodes: List[Dict], edges: List[Dict]) -> List[schemas.ValidationResult]:
        """Validate workflow structure and logic"""
        results = []
        
        # Check for required nodes
        has_data_source = any(node.get("type") == "dataSource" for node in nodes)
        if not has_data_source:
            results.append(schemas.ValidationResult(
                rule="data_source_required",
                status="failed",
                message="Workflow must have at least one data source"
            ))
        
        has_action = any(node.get("type") == "action" for node in nodes)
        if not has_action:
            results.append(schemas.ValidationResult(
                rule="action_required", 
                status="warning",
                message="Workflow has no trading actions defined"
            ))
        
        # Check for disconnected nodes
        connected_nodes = set()
        for edge in edges:
            connected_nodes.add(edge.get("source"))
            connected_nodes.add(edge.get("target"))
        
        disconnected_nodes = [node["id"] for node in nodes if node["id"] not in connected_nodes and len(nodes) > 1]
        if disconnected_nodes:
            results.append(schemas.ValidationResult(
                rule="disconnected_nodes",
                status="warning",
                message=f"Found {len(disconnected_nodes)} disconnected nodes",
                details={"nodes": disconnected_nodes}
            ))
        
        # Check for circular dependencies
        if self._has_circular_dependency(nodes, edges):
            results.append(schemas.ValidationResult(
                rule="circular_dependency",
                status="failed",
                message="Workflow contains circular dependencies"
            ))
        
        # Validate node parameters
        for node in nodes:
            node_validation = await self._validate_node_parameters(node)
            results.extend(node_validation)
        
        return results
    
    def _has_circular_dependency(self, nodes: List[Dict], edges: List[Dict]) -> bool:
        """Check for circular dependencies in the workflow"""
        # Build adjacency list
        graph = {}
        for node in nodes:
            graph[node["id"]] = []
        
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            if source and target:
                graph[source].append(target)
        
        # DFS to detect cycles
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            if node in rec_stack:
                return True
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if has_cycle(neighbor):
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node_id in graph:
            if has_cycle(node_id):
                return True
        
        return False
    
    async def _validate_node_parameters(self, node: Dict) -> List[schemas.ValidationResult]:
        """Validate individual node parameters"""
        results = []
        node_type = node.get("type")
        parameters = node.get("data", {}).get("parameters", {})
        
        if node_type == "technicalIndicator":
            indicator = parameters.get("indicator")
            if not indicator:
                results.append(schemas.ValidationResult(
                    rule="indicator_type_required",
                    status="failed",
                    message=f"Node {node['id']}: Indicator type is required"
                ))
            
            period = parameters.get("period")
            if period and (not isinstance(period, (int, float)) or period <= 0):
                results.append(schemas.ValidationResult(
                    rule="invalid_period",
                    status="failed",
                    message=f"Node {node['id']}: Period must be a positive number"
                ))
        
        elif node_type == "condition":
            condition_type = parameters.get("condition")
            if not condition_type:
                results.append(schemas.ValidationResult(
                    rule="condition_type_required",
                    status="failed",
                    message=f"Node {node['id']}: Condition type is required"
                ))
        
        elif node_type == "action":
            action_type = parameters.get("action")
            if not action_type:
                results.append(schemas.ValidationResult(
                    rule="action_type_required",
                    status="failed",
                    message=f"Node {node['id']}: Action type is required"
                ))
        
        return results
    
    async def _validate_python_code(self, python_code: str) -> List[schemas.ValidationResult]:
        """Validate the generated Python code"""
        results = []
        
        try:
            # Parse the code to check for syntax errors
            ast.parse(python_code)
            results.append(schemas.ValidationResult(
                rule="syntax_check",
                status="passed",
                message="Python syntax is valid"
            ))
        except SyntaxError as e:
            results.append(schemas.ValidationResult(
                rule="syntax_check",
                status="failed",
                message=f"Syntax error: {str(e)}"
            ))
        
        # Check for security issues
        security_check = await self._security_scan(python_code)
        results.extend(security_check)
        
        return results
    
    async def _security_scan(self, python_code: str) -> List[schemas.ValidationResult]:
        """Perform security scanning on generated code"""
        results = []
        
        # Check for dangerous imports
        dangerous_imports = ["os", "subprocess", "eval", "exec", "open", "__import__"]
        for dangerous in dangerous_imports:
            if dangerous in python_code:
                results.append(schemas.ValidationResult(
                    rule="dangerous_import",
                    status="failed",
                    message=f"Code contains potentially dangerous operation: {dangerous}"
                ))
        
        # Check for file operations
        file_operations = ["open(", "file(", "with open"]
        for operation in file_operations:
            if operation in python_code:
                results.append(schemas.ValidationResult(
                    rule="file_operation",
                    status="warning",
                    message="Code contains file operations that may need review"
                ))
        
        if not any(r.status == "failed" for r in results):
            results.append(schemas.ValidationResult(
                rule="security_scan",
                status="passed",
                message="No security issues detected"
            ))
        
        return results
    
    async def _generate_python_code(self, workflow_id: str, nodes: List[Dict], edges: List[Dict], parameters: Dict[str, Any]) -> str:
        """Generate Python code from workflow definition"""
        
        # Build execution order
        execution_order = self._topological_sort(nodes, edges)
        
        # Generate imports
        imports = self._generate_imports()
        
        # Generate class definition
        class_def = self._generate_class_definition(workflow_id)
        
        # Generate initialization method
        init_method = self._generate_init_method(parameters)
        
        # Generate execute method
        execute_method = self._generate_execute_method(nodes, edges, execution_order)
        
        # Generate helper methods
        helper_methods = self._generate_helper_methods(nodes)
        
        # Combine all parts
        python_code = f"""
{imports}

{class_def}
{init_method}

{execute_method}

{helper_methods}
"""
        
        return textwrap.dedent(python_code).strip()
    
    def _topological_sort(self, nodes: List[Dict], edges: List[Dict]) -> List[str]:
        """Sort nodes in execution order using topological sort"""
        # Build adjacency list and in-degree count
        graph = {}
        in_degree = {}
        
        for node in nodes:
            node_id = node["id"]
            graph[node_id] = []
            in_degree[node_id] = 0
        
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            if source and target:
                graph[source].append(target)
                in_degree[target] += 1
        
        # Kahn's algorithm
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result
    
    def _generate_imports(self) -> str:
        """Generate required imports"""
        return """
import pandas as pd
import numpy as np
import talib
from typing import Dict, Any, Optional
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')
"""
    
    def _generate_class_definition(self, workflow_id: str) -> str:
        """Generate class definition"""
        class_name = f"Strategy_{workflow_id.replace('-', '_')}"
        return f"""
class {class_name}:
    \"\"\"Generated trading strategy from visual workflow\"\"\"
"""
    
    def _generate_init_method(self, parameters: Dict[str, Any]) -> str:
        """Generate __init__ method"""
        return """
    def __init__(self, parameters: Dict[str, Any] = None):
        self.parameters = parameters or {}
        self.state = {}
        self.signals = {}
"""
    
    def _generate_execute_method(self, nodes: List[Dict], edges: List[Dict], execution_order: List[str]) -> str:
        """Generate the main execute method"""
        method_code = """
    def execute(self, data: pd.DataFrame) -> pd.DataFrame:
        \"\"\"Execute the trading strategy\"\"\"
        
        # Initialize results DataFrame
        results = pd.DataFrame(index=data.index)
        self.data = data
        
        # Execute nodes in topological order
"""
        
        for node_id in execution_order:
            node = next((n for n in nodes if n["id"] == node_id), None)
            if node:
                node_type = node.get("type")
                if node_type in self.component_registry:
                    template_func = self.component_registry[node_type]["template"]
                    node_code = template_func(node, edges)
                    method_code += f"""
        # Node: {node.get('data', {}).get('label', node_id)}
{textwrap.indent(node_code, '        ')}
"""
        
        method_code += """
        
        return results
"""
        
        return method_code
    
    def _generate_helper_methods(self, nodes: List[Dict]) -> str:
        """Generate helper methods"""
        return """
    def get_signal(self, node_id: str, default=0):
        \"\"\"Get signal value from a node\"\"\"
        return self.signals.get(node_id, default)
    
    def set_signal(self, node_id: str, value):
        \"\"\"Set signal value for a node\"\"\"
        self.signals[node_id] = value
    
    def backtest(self, data: pd.DataFrame) -> Dict[str, Any]:
        \"\"\"Run backtest on the strategy\"\"\"
        signals = self.execute(data)
        
        # Calculate basic performance metrics
        returns = signals.get('returns', pd.Series(dtype=float))
        
        if len(returns) == 0:
            return {
                'total_return': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0,
                'total_trades': 0
            }
        
        total_return = (1 + returns).prod() - 1
        sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        cumulative = (1 + returns).cumprod()
        max_drawdown = (cumulative / cumulative.expanding().max() - 1).min()
        
        winning_trades = (returns > 0).sum()
        total_trades = (returns != 0).sum()
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        return {
            'total_return': float(total_return),
            'sharpe_ratio': float(sharpe_ratio),
            'max_drawdown': float(max_drawdown),
            'win_rate': float(win_rate),
            'total_trades': int(total_trades)
        }
"""
    
    # Component template methods
    def _data_source_template(self, node: Dict, edges: List[Dict]) -> str:
        """Generate code for data source node"""
        parameters = node.get("data", {}).get("parameters", {})
        symbol = parameters.get("symbol", "AAPL")
        timeframe = parameters.get("timeframe", "1h")
        
        return f"""
# Data source: {symbol} {timeframe}
self.set_signal("{node['id']}_data", self.data)
"""
    
    def _technical_indicator_template(self, node: Dict, edges: List[Dict]) -> str:
        """Generate code for technical indicator node"""
        parameters = node.get("data", {}).get("parameters", {})
        indicator = parameters.get("indicator", "SMA")
        period = parameters.get("period", 20)
        source = parameters.get("source", "close")
        
        if indicator == "SMA":
            return f"""
# Simple Moving Average
{node['id']}_value = talib.SMA(self.data['{source}'], timeperiod={period})
self.set_signal("{node['id']}_value", {node['id']}_value)
"""
        elif indicator == "EMA":
            return f"""
# Exponential Moving Average  
{node['id']}_value = talib.EMA(self.data['{source}'], timeperiod={period})
self.set_signal("{node['id']}_value", {node['id']}_value)
"""
        elif indicator == "RSI":
            return f"""
# Relative Strength Index
{node['id']}_value = talib.RSI(self.data['{source}'], timeperiod={period})
self.set_signal("{node['id']}_value", {node['id']}_value)
"""
        else:
            return f"""
# {indicator}
{node['id']}_value = self.data['{source}']  # Placeholder
self.set_signal("{node['id']}_value", {node['id']}_value)
"""
    
    def _condition_template(self, node: Dict, edges: List[Dict]) -> str:
        """Generate code for condition node"""
        parameters = node.get("data", {}).get("parameters", {})
        condition_type = parameters.get("condition", "greater_than")
        value = parameters.get("value", 0)
        
        # Find input connections
        input_nodes = [e["source"] for e in edges if e["target"] == node["id"]]
        input_signal = f"self.get_signal('{input_nodes[0]}_value')" if input_nodes else "self.data['close']"
        
        if condition_type == "greater_than":
            return f"""
# Condition: Greater than {value}
{node['id']}_signal = ({input_signal} > {value}).astype(int)
self.set_signal("{node['id']}_signal", {node['id']}_signal)
"""
        elif condition_type == "less_than":
            return f"""
# Condition: Less than {value}
{node['id']}_signal = ({input_signal} < {value}).astype(int)
self.set_signal("{node['id']}_signal", {node['id']}_signal)
"""
        elif condition_type == "crossover":
            return f"""
# Condition: Crossover above {value}
{node['id']}_signal = (({input_signal} > {value}) & ({input_signal}.shift(1) <= {value})).astype(int)
self.set_signal("{node['id']}_signal", {node['id']}_signal)
"""
        else:
            return f"""
# Generic condition
{node['id']}_signal = ({input_signal} != 0).astype(int)
self.set_signal("{node['id']}_signal", {node['id']}_signal)
"""
    
    def _action_template(self, node: Dict, edges: List[Dict]) -> str:
        """Generate code for action node"""
        parameters = node.get("data", {}).get("parameters", {})
        action_type = parameters.get("action", "buy")
        quantity = parameters.get("quantity", 0)
        
        # Find input signal
        input_nodes = [e["source"] for e in edges if e["target"] == node["id"]]
        input_signal = f"self.get_signal('{input_nodes[0]}_signal')" if input_nodes else "1"
        
        return f"""
# Action: {action_type}
{node['id']}_orders = {input_signal} * {'1' if action_type == 'buy' else '-1'}
self.set_signal("{node['id']}_orders", {node['id']}_orders)
results['signal'] = {node['id']}_orders
"""
    
    def _logic_template(self, node: Dict, edges: List[Dict]) -> str:
        """Generate code for logic gate node"""
        parameters = node.get("data", {}).get("parameters", {})
        logic_type = parameters.get("type", "and")
        
        # Find input signals
        input_nodes = [e["source"] for e in edges if e["target"] == node["id"]]
        
        if len(input_nodes) >= 2:
            signal1 = f"self.get_signal('{input_nodes[0]}_signal')"
            signal2 = f"self.get_signal('{input_nodes[1]}_signal')"
            
            if logic_type == "and":
                return f"""
# Logic: AND gate
{node['id']}_signal = ({signal1} & {signal2}).astype(int)
self.set_signal("{node['id']}_signal", {node['id']}_signal)
"""
            elif logic_type == "or":
                return f"""
# Logic: OR gate  
{node['id']}_signal = ({signal1} | {signal2}).astype(int)
self.set_signal("{node['id']}_signal", {node['id']}_signal)
"""
        
        return f"""
# Logic gate (default)
{node['id']}_signal = pd.Series(0, index=self.data.index)
self.set_signal("{node['id']}_signal", {node['id']}_signal)
"""
    
    def _risk_template(self, node: Dict, edges: List[Dict]) -> str:
        """Generate code for risk management node"""
        parameters = node.get("data", {}).get("parameters", {})
        
        # Find input signal
        input_nodes = [e["source"] for e in edges if e["target"] == node["id"]]
        input_signal = f"self.get_signal('{input_nodes[0]}_signal')" if input_nodes else "1"
        
        return f"""
# Risk management
{node['id']}_risk_adjusted = {input_signal}  # Placeholder for risk adjustment
self.set_signal("{node['id']}_adjusted_signal", {node['id']}_risk_adjusted)
"""
    
    async def get_available_components(self) -> List[schemas.ComponentResponse]:
        """Get list of available components"""
        components = []
        
        for comp_id, comp_info in self.component_registry.items():
            components.append(schemas.ComponentResponse(
                id=comp_id,
                name=comp_info["name"],
                type=comp_id,
                category=comp_info["category"],
                description=f"{comp_info['name']} component",
                tags=[comp_info["category"].lower()],
                inputs=[schemas.ComponentIOPort(name=inp, type="data") for inp in comp_info["inputs"]],
                outputs=[schemas.ComponentIOPort(name=out, type="data") for out in comp_info["outputs"]]
            ))
        
        return components
    
    async def get_component_details(self, component_type: str) -> Optional[schemas.ComponentDetailResponse]:
        """Get detailed information about a component"""
        if component_type not in self.component_registry:
            return None
        
        comp_info = self.component_registry[component_type]
        
        return schemas.ComponentDetailResponse(
            id=component_type,
            name=comp_info["name"],
            type=component_type,
            category=comp_info["category"],
            description=f"Detailed description of {comp_info['name']}",
            tags=[comp_info["category"].lower()],
            inputs=[schemas.ComponentIOPort(name=inp, type="data") for inp in comp_info["inputs"]],
            outputs=[schemas.ComponentIOPort(name=out, type="data") for out in comp_info["outputs"]],
            documentation=f"Documentation for {comp_info['name']} component",
            examples=[]
        )