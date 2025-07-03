import ast
import inspect
from typing import Dict, List, Any, Optional
import json
import re

class WorkflowCompiler:
    """Compiles visual workflows into executable Python trading strategies"""
    
    def __init__(self):
        self.component_registry = self._initialize_component_registry()
        
    def _initialize_component_registry(self) -> Dict[str, Dict[str, Any]]:
        """Initialize the registry of available components"""
        return {
            # Data Source Components
            "market_data_input": {
                "type": "input",
                "category": "data_source",
                "template": """
def get_market_data(symbol, timeframe, start_date, end_date):
    '''Fetch market data for the specified symbol and timeframe'''
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    
    # This would connect to real data sources in production
    # For now, generate sample data
    dates = pd.date_range(start=start_date, end=end_date, freq='{timeframe}')
    np.random.seed(42)
    
    price = 100
    data = []
    for date in dates:
        change = np.random.normal(0, 0.02)
        price *= (1 + change)
        high = price * (1 + abs(np.random.normal(0, 0.01)))
        low = price * (1 - abs(np.random.normal(0, 0.01)))
        volume = np.random.randint(1000, 10000)
        
        data.append({
            'timestamp': date,
            'open': price,
            'high': high,
            'low': low,
            'close': price,
            'volume': volume
        })
    
    return pd.DataFrame(data)
""",
                "imports": ["pandas", "numpy", "datetime"],
                "outputs": ["market_data"]
            },
            
            # Technical Indicators
            "sma_indicator": {
                "type": "transform",
                "category": "indicator",
                "template": """
def calculate_sma(data, period={period}):
    '''Calculate Simple Moving Average'''
    import pandas as pd
    if isinstance(data, pd.DataFrame):
        return data['close'].rolling(window=period).mean()
    return pd.Series(data).rolling(window=period).mean()
""",
                "imports": ["pandas"],
                "parameters": ["period"],
                "inputs": ["data"],
                "outputs": ["sma"]
            },
            
            "rsi_indicator": {
                "type": "transform", 
                "category": "indicator",
                "template": """
def calculate_rsi(data, period={period}):
    '''Calculate Relative Strength Index'''
    import pandas as pd
    import numpy as np
    
    if isinstance(data, pd.DataFrame):
        prices = data['close']
    else:
        prices = pd.Series(data)
    
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi
""",
                "imports": ["pandas", "numpy"],
                "parameters": ["period"],
                "inputs": ["data"],
                "outputs": ["rsi"]
            },
            
            "macd_indicator": {
                "type": "transform",
                "category": "indicator", 
                "template": """
def calculate_macd(data, fast_period={fast_period}, slow_period={slow_period}, signal_period={signal_period}):
    '''Calculate MACD indicator'''
    import pandas as pd
    
    if isinstance(data, pd.DataFrame):
        prices = data['close']
    else:
        prices = pd.Series(data)
    
    ema_fast = prices.ewm(span=fast_period).mean()
    ema_slow = prices.ewm(span=slow_period).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_period).mean()
    histogram = macd_line - signal_line
    
    return pd.DataFrame({
        'macd': macd_line,
        'signal': signal_line, 
        'histogram': histogram
    })
""",
                "imports": ["pandas"],
                "parameters": ["fast_period", "slow_period", "signal_period"],
                "inputs": ["data"],
                "outputs": ["macd_data"]
            },
            
            # Condition Components
            "price_condition": {
                "type": "condition",
                "category": "condition",
                "template": """
def check_price_condition(current_price, indicator_value, operator='{operator}', threshold={threshold}):
    '''Check price-based trading condition'''
    if operator == '>':
        return current_price > indicator_value + threshold
    elif operator == '<':
        return current_price < indicator_value - threshold
    elif operator == '>=':
        return current_price >= indicator_value + threshold
    elif operator == '<=':
        return current_price <= indicator_value - threshold
    elif operator == '==':
        return abs(current_price - indicator_value) <= threshold
    elif operator == 'cross_above':
        return current_price > indicator_value and current_price != indicator_value
    elif operator == 'cross_below':
        return current_price < indicator_value and current_price != indicator_value
    return False
""",
                "imports": [],
                "parameters": ["operator", "threshold"],
                "inputs": ["current_price", "indicator_value"],
                "outputs": ["condition_met"]
            },
            
            "indicator_condition": {
                "type": "condition",
                "category": "condition",
                "template": """
def check_indicator_condition(indicator_value, threshold={threshold}, operator='{operator}'):
    '''Check indicator-based condition (e.g., RSI > 70)'''
    if operator == '>':
        return indicator_value > threshold
    elif operator == '<':
        return indicator_value < threshold
    elif operator == '>=':
        return indicator_value >= threshold
    elif operator == '<=':
        return indicator_value <= threshold
    elif operator == '==':
        return abs(indicator_value - threshold) < 0.001
    return False
""",
                "imports": [],
                "parameters": ["threshold", "operator"],
                "inputs": ["indicator_value"],
                "outputs": ["condition_met"]
            },
            
            # Action Components
            "buy_signal": {
                "type": "action",
                "category": "action",
                "template": """
def generate_buy_signal(condition, quantity={quantity}, order_type='{order_type}'):
    '''Generate buy signal when condition is met'''
    if condition:
        return {
            'action': 'buy',
            'quantity': quantity,
            'order_type': order_type,
            'timestamp': pd.Timestamp.now()
        }
    return None
""",
                "imports": ["pandas"],
                "parameters": ["quantity", "order_type"],
                "inputs": ["condition"],
                "outputs": ["buy_signal"]
            },
            
            "sell_signal": {
                "type": "action",
                "category": "action",
                "template": """
def generate_sell_signal(condition, quantity={quantity}, order_type='{order_type}'):
    '''Generate sell signal when condition is met'''
    if condition:
        return {
            'action': 'sell',
            'quantity': quantity,
            'order_type': order_type,
            'timestamp': pd.Timestamp.now()
        }
    return None
""",
                "imports": ["pandas"],
                "parameters": ["quantity", "order_type"],
                "inputs": ["condition"],
                "outputs": ["sell_signal"]
            },
            
            # Risk Management
            "stop_loss": {
                "type": "risk",
                "category": "risk_management",
                "template": """
def check_stop_loss(current_price, entry_price, position_side, stop_loss_percent={stop_loss_percent}):
    '''Check if stop loss should be triggered'''
    if position_side == 'long':
        stop_price = entry_price * (1 - stop_loss_percent / 100)
        return current_price <= stop_price
    elif position_side == 'short':
        stop_price = entry_price * (1 + stop_loss_percent / 100)
        return current_price >= stop_price
    return False
""",
                "imports": [],
                "parameters": ["stop_loss_percent"],
                "inputs": ["current_price", "entry_price", "position_side"],
                "outputs": ["should_stop"]
            },
            
            "take_profit": {
                "type": "risk",
                "category": "risk_management",
                "template": """
def check_take_profit(current_price, entry_price, position_side, take_profit_percent={take_profit_percent}):
    '''Check if take profit should be triggered'''
    if position_side == 'long':
        target_price = entry_price * (1 + take_profit_percent / 100)
        return current_price >= target_price
    elif position_side == 'short':
        target_price = entry_price * (1 - take_profit_percent / 100)
        return current_price <= target_price
    return False
""",
                "imports": [],
                "parameters": ["take_profit_percent"],
                "inputs": ["current_price", "entry_price", "position_side"],
                "outputs": ["should_take_profit"]
            },
            
            # Output Components
            "portfolio_metrics": {
                "type": "output",
                "category": "output",
                "template": """
def calculate_portfolio_metrics(trades, initial_capital={initial_capital}):
    '''Calculate portfolio performance metrics'''
    import pandas as pd
    import numpy as np
    
    if not trades:
        return {
            'total_return': 0,
            'total_return_percent': 0,
            'total_trades': 0,
            'winning_trades': 0,
            'win_rate': 0
        }
    
    trades_df = pd.DataFrame(trades)
    total_pnl = trades_df['pnl'].sum() if 'pnl' in trades_df.columns else 0
    total_return_percent = (total_pnl / initial_capital) * 100
    
    winning_trades = len(trades_df[trades_df['pnl'] > 0]) if 'pnl' in trades_df.columns else 0
    win_rate = (winning_trades / len(trades_df)) * 100 if len(trades_df) > 0 else 0
    
    return {
        'total_return': total_pnl,
        'total_return_percent': total_return_percent,
        'total_trades': len(trades_df),
        'winning_trades': winning_trades,
        'win_rate': win_rate,
        'current_capital': initial_capital + total_pnl
    }
""",
                "imports": ["pandas", "numpy"],
                "parameters": ["initial_capital"],
                "inputs": ["trades"],
                "outputs": ["portfolio_metrics"]
            }
        }
    
    async def compile_workflow(self, nodes: List[Dict], edges: List[Dict], strategy_name: str = "Generated Strategy") -> Dict[str, Any]:
        """Compile a visual workflow into executable Python code"""
        try:
            # Validate workflow structure
            validation_result = self._validate_workflow(nodes, edges)
            if not validation_result['is_valid']:
                return {
                    'success': False,
                    'errors': validation_result['errors'],
                    'code': '',
                    'requirements': []
                }
            
            # Sort nodes by execution order
            sorted_nodes = self._topological_sort(nodes, edges)
            
            # Generate Python code
            code_parts = []
            imports = set()
            
            # Add imports
            code_parts.append("# Generated Trading Strategy")
            code_parts.append(f"# Strategy Name: {strategy_name}")
            code_parts.append("# Auto-generated from visual workflow")
            code_parts.append("")
            
            # Process each node and generate corresponding code
            node_outputs = {}
            
            for node in sorted_nodes:
                node_type = node.get('type', '')
                node_data = node.get('data', {})
                
                if node_type in self.component_registry:
                    component = self.component_registry[node_type]
                    
                    # Add component imports
                    for imp in component.get('imports', []):
                        imports.add(f"import {imp}")
                    
                    # Generate function code for this node
                    function_code = self._generate_node_code(node, component)
                    code_parts.append(function_code)
                    code_parts.append("")
                    
                    # Track outputs for connecting to other nodes
                    node_outputs[node['id']] = component.get('outputs', [])
            
            # Generate main strategy execution function
            main_function = self._generate_main_strategy_function(sorted_nodes, edges, node_outputs)
            code_parts.append(main_function)
            
            # Combine all code parts
            import_statements = sorted(list(imports))
            full_code = "\n".join(import_statements) + "\n\n" + "\n".join(code_parts)
            
            # Get required packages
            requirements = self._get_requirements(imports)
            
            return {
                'success': True,
                'code': full_code,
                'requirements': requirements,
                'errors': [],
                'warnings': validation_result.get('warnings', [])
            }
            
        except Exception as e:
            return {
                'success': False,
                'errors': [f"Compilation error: {str(e)}"],
                'code': '',
                'requirements': []
            }
    
    def _validate_workflow(self, nodes: List[Dict], edges: List[Dict]) -> Dict[str, Any]:
        """Validate workflow structure"""
        errors = []
        warnings = []
        
        if not nodes:
            errors.append("Workflow must contain at least one node")
        
        # Check for required node types
        node_types = [node.get('type', '') for node in nodes]
        
        has_data_source = any(self.component_registry.get(nt, {}).get('category') == 'data_source' for nt in node_types)
        if not has_data_source:
            errors.append("Workflow must include at least one data source")
        
        has_action = any(self.component_registry.get(nt, {}).get('category') == 'action' for nt in node_types)
        if not has_action:
            warnings.append("Workflow should include at least one trading action")
        
        # Check for circular dependencies
        if self._has_circular_dependency(nodes, edges):
            errors.append("Workflow contains circular dependencies")
        
        # Validate node connections
        for edge in edges:
            source_exists = any(node['id'] == edge['source'] for node in nodes)
            target_exists = any(node['id'] == edge['target'] for node in nodes)
            
            if not source_exists:
                errors.append(f"Edge references non-existent source node: {edge['source']}")
            if not target_exists:
                errors.append(f"Edge references non-existent target node: {edge['target']}")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _topological_sort(self, nodes: List[Dict], edges: List[Dict]) -> List[Dict]:
        """Sort nodes in execution order using topological sort"""
        # Build adjacency list
        graph = {node['id']: [] for node in nodes}
        in_degree = {node['id']: 0 for node in nodes}
        
        for edge in edges:
            graph[edge['source']].append(edge['target'])
            in_degree[edge['target']] += 1
        
        # Topological sort using Kahn's algorithm
        queue = [node_id for node_id in in_degree if in_degree[node_id] == 0]
        sorted_node_ids = []
        
        while queue:
            current = queue.pop(0)
            sorted_node_ids.append(current)
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Return nodes in sorted order
        node_dict = {node['id']: node for node in nodes}
        return [node_dict[node_id] for node_id in sorted_node_ids if node_id in node_dict]
    
    def _has_circular_dependency(self, nodes: List[Dict], edges: List[Dict]) -> bool:
        """Check if workflow has circular dependencies"""
        sorted_nodes = self._topological_sort(nodes, edges)
        return len(sorted_nodes) != len(nodes)
    
    def _generate_node_code(self, node: Dict, component: Dict) -> str:
        """Generate Python code for a specific node"""
        template = component['template']
        parameters = node.get('data', {}).get('parameters', {})
        
        # Replace parameter placeholders in template
        for param_name, param_value in parameters.items():
            if isinstance(param_value, str):
                template = template.replace(f"{{{param_name}}}", f"'{param_value}'")
            else:
                template = template.replace(f"{{{param_name}}}", str(param_value))
        
        # Replace any remaining placeholders with defaults
        template = re.sub(r'{(\w+)}', lambda m: self._get_default_parameter_value(m.group(1)), template)
        
        return template
    
    def _get_default_parameter_value(self, param_name: str) -> str:
        """Get default value for a parameter"""
        defaults = {
            'period': '20',
            'threshold': '0',
            'operator': '>',
            'quantity': '100',
            'order_type': 'market',
            'stop_loss_percent': '5',
            'take_profit_percent': '10',
            'fast_period': '12',
            'slow_period': '26',
            'signal_period': '9',
            'initial_capital': '10000'
        }
        return defaults.get(param_name, '0')
    
    def _generate_main_strategy_function(self, nodes: List[Dict], edges: List[Dict], node_outputs: Dict) -> str:
        """Generate the main strategy execution function"""
        return '''
def execute_strategy(symbol, timeframe, start_date, end_date, initial_capital=10000):
    """Main strategy execution function"""
    import pandas as pd
    import numpy as np
    from datetime import datetime
    
    # Initialize variables
    portfolio = {
        'capital': initial_capital,
        'positions': [],
        'trades': [],
        'signals': []
    }
    
    # Get market data
    market_data = get_market_data(symbol, timeframe, start_date, end_date)
    
    # Initialize indicators
    data_length = len(market_data)
    
    # Calculate indicators (this would be dynamically generated based on workflow)
    # For now, using a simple example
    sma_20 = calculate_sma(market_data, 20)
    rsi_14 = calculate_rsi(market_data, 14)
    
    # Process each bar
    for i in range(max(20, 14), len(market_data)):  # Start after warmup period
        current_bar = market_data.iloc[i]
        current_price = current_bar['close']
        
        # Check trading conditions (this would be dynamically generated)
        rsi_value = rsi_14.iloc[i]
        sma_value = sma_20.iloc[i]
        
        # Example buy condition: RSI < 30 and price > SMA
        if rsi_value < 30 and current_price > sma_value and len(portfolio['positions']) == 0:
            buy_signal = generate_buy_signal(True, 100, 'market')
            if buy_signal:
                portfolio['signals'].append(buy_signal)
                portfolio['positions'].append({
                    'side': 'long',
                    'entry_price': current_price,
                    'quantity': 100,
                    'entry_time': current_bar['timestamp']
                })
        
        # Example sell condition: RSI > 70 or stop loss
        elif len(portfolio['positions']) > 0:
            position = portfolio['positions'][0]
            
            # Check sell conditions
            should_sell = rsi_value > 70 or check_stop_loss(current_price, position['entry_price'], 'long', 5)
            
            if should_sell:
                sell_signal = generate_sell_signal(True, position['quantity'], 'market')
                if sell_signal:
                    # Calculate PnL
                    pnl = (current_price - position['entry_price']) * position['quantity']
                    
                    portfolio['trades'].append({
                        'entry_price': position['entry_price'],
                        'exit_price': current_price,
                        'quantity': position['quantity'],
                        'pnl': pnl,
                        'entry_time': position['entry_time'],
                        'exit_time': current_bar['timestamp']
                    })
                    
                    portfolio['capital'] += pnl
                    portfolio['positions'] = []  # Close position
    
    # Calculate final metrics
    metrics = calculate_portfolio_metrics(portfolio['trades'], initial_capital)
    
    return {
        'portfolio': portfolio,
        'metrics': metrics,
        'market_data': market_data
    }

# Example usage:
# result = execute_strategy('BTCUSDT', '1h', '2023-01-01', '2023-12-31', 10000)
# print(f"Total Return: {result['metrics']['total_return_percent']:.2f}%")
'''
    
    def _get_requirements(self, imports: set) -> List[str]:
        """Get pip requirements from imports"""
        requirement_mapping = {
            'pandas': 'pandas>=1.3.0',
            'numpy': 'numpy>=1.21.0',
            'ccxt': 'ccxt>=2.0.0',
            'requests': 'requests>=2.25.0',
            'websocket': 'websocket-client>=1.2.0',
            'ta': 'ta>=0.10.0'
        }
        
        requirements = []
        for imp in imports:
            base_import = imp.split('.')[0]  # Get base module name
            if base_import in requirement_mapping:
                requirements.append(requirement_mapping[base_import])
        
        return list(set(requirements))  # Remove duplicates