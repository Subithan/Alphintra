import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from collections import deque, defaultdict

logger = logging.getLogger(__name__)

class GeneratedCode:
    def __init__(self):
        self.strategy = ""
        self.requirements = []
        self.imports = []
        self.classes = []
        self.functions = []
        self.metadata = {
            "name": "",
            "description": "",
            "author": "Alphintra Code Generator",
            "version": "1.0.0",
            "generatedAt": datetime.utcnow().isoformat(),
            "complexity": 0,
            "estimatedPerformance": {
                "executionTime": "",
                "memoryUsage": "",
                "backtestSpeed": ""
            }
        }
        self.tests = ""
        self.documentation = ""

class CodeClass:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.methods = []
        self.properties = []

class CodeMethod:
    def __init__(self, name: str, parameters: List[Dict], return_type: str, description: str, code: str):
        self.name = name
        self.parameters = parameters
        self.return_type = return_type
        self.description = description
        self.code = code

class CodeProperty:
    def __init__(self, name: str, type: str, description: str, default_value: Optional[Any] = None):
        self.name = name
        self.type = type
        self.description = description
        self.default_value = default_value

class CodeFunction:
    def __init__(self, name: str, parameters: List[Dict], return_type: str, description: str, code: str):
        self.name = name
        self.parameters = parameters
        self.return_type = return_type
        self.description = description
        self.code = code

class AdvancedCodeGenerator:
    def __init__(self, workflow: Dict[str, Any]):
        self.workflow = workflow
        self.nodes = workflow.get('nodes', [])
        self.edges = workflow.get('edges', [])

    def generate_strategy(self) -> GeneratedCode:
        topology = self.analyze_topology()
        requirements = self.generate_requirements()
        imports = self.generate_imports()
        strategy_class = self.generate_strategy_class(topology)
        helper_functions = self.generate_helper_functions()
        tests = self.generate_tests()
        documentation = self.generate_documentation()

        strategy_code = self.assemble_strategy_code(imports, strategy_class, helper_functions)

        generated_code = GeneratedCode()
        generated_code.strategy = strategy_code
        generated_code.requirements = requirements
        generated_code.imports = imports
        generated_code.classes = [strategy_class]
        generated_code.functions = helper_functions
        generated_code.metadata["name"] = self.workflow.get("name", "GeneratedStrategy")
        generated_code.metadata["description"] = self.workflow.get("description", "Generated trading strategy")
        generated_code.metadata["complexity"] = self.calculate_complexity()
        generated_code.metadata["estimatedPerformance"] = self.estimate_performance()
        generated_code.tests = tests
        generated_code.documentation = documentation

        return generated_code

    def analyze_topology(self):
        execution_order = self.topological_sort()
        data_flow = self.analyze_data_flow()
        node_types = self.categorize_nodes()
        return {
            "execution_order": execution_order,
            "data_flow": data_flow,
            "node_types": node_types
        }

    def topological_sort(self):
        in_degree = {node['id']: 0 for node in self.nodes}
        adj_list = defaultdict(list)

        for edge in self.edges:
            source = edge['source']
            target = edge['target']
            adj_list[source].append(target)
            in_degree[target] += 1

        queue = deque([node_id for node_id in in_degree if in_degree[node_id] == 0])
        result = []

        while queue:
            current = queue.popleft()
            result.append(current)
            for neighbor in adj_list[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(self.nodes):
            raise ValueError("Cycle detected in the workflow")

        return result

    def analyze_data_flow(self):
        data_flow = {}
        for node in self.nodes:
            inputs = [edge['source'] for edge in self.edges if edge['target'] == node['id']]
            outputs = [edge['target'] for edge in self.edges if edge['source'] == node['id']]
            data_flow[node['id']] = {
                "inputs": inputs,
                "outputs": outputs,
                "data_type": self.get_node_data_type(node)
            }
        return data_flow

    def categorize_nodes(self):
        categories = {
            "dataSources": [node for node in self.nodes if node['type'] in ['dataSource', 'customDataset']],
            "indicators": [node for node in self.nodes if node['type'] == 'technicalIndicator'],
            "conditions": [node for node in self.nodes if node['type'] == 'condition'],
            "logic": [node for node in self.nodes if node['type'] == 'logic'],
            "actions": [node for node in self.nodes if node['type'] == 'action'],
            "riskManagement": [node for node in self.nodes if node['type'] == 'risk'],
            "outputs": [node for node in self.nodes if node['type'] == 'output']
        }
        return categories

    def generate_requirements(self):
        return [
            'pandas>=2.0.0',
            'numpy>=1.24.0',
            'ta-lib>=0.4.25',
            'backtrader>=1.9.76',
            'yfinance>=0.2.18',
            'scipy>=1.10.0',
            'scikit-learn>=1.3.0',
            'plotly>=5.15.0',
            'fastapi>=0.104.0',
            'pydantic>=2.4.0',
            'asyncio-mqtt>=0.11.0'
        ]

    def generate_imports(self):
        return [
            'import pandas as pd',
            'import numpy as np',
            'import talib as ta',
            'from typing import Dict, List, Optional, Tuple, Union',
            'from dataclasses import dataclass',
            'from datetime import datetime, timedelta',
            'from enum import Enum',
            'import logging',
            'import asyncio',
            'from abc import ABC, abstractmethod'
        ]

    def generate_strategy_class(self, topology):
        methods = [
            self.generate_init_method(),
            self.generate_setup_method(topology),
            self.generate_on_data_method(topology),
            self.generate_calculate_indicators_method(topology),
            self.generate_evaluate_conditions_method(topology),
            self.generate_execute_actions_method(topology),
            self.generate_manage_risk_method(topology),
            self.generate_get_signals_method(),
            self.generate_backtest_method()
        ]

        properties = [
            CodeProperty("name", "str", "Strategy name"),
            CodeProperty("data", "pd.DataFrame", "Market data"),
            CodeProperty("indicators", "Dict[str, pd.Series]", "Technical indicators"),
            CodeProperty("signals", "Dict[str, bool]", "Trading signals"),
            CodeProperty("positions", "Dict[str, float]", "Current positions"),
            CodeProperty("portfolio_value", "float", "Current portfolio value"),
            CodeProperty("risk_params", "Dict[str, float]", "Risk management parameters")
        ]

        class_name = self.sanitize_class_name(self.workflow.get("name", "GeneratedStrategy"))
        strategy_class = CodeClass(
            name=class_name,
            description=f"Generated trading strategy: {self.workflow.get('description', 'Generated trading strategy')}",
)

        strategy_class.methods = methods
        strategy_class.properties = properties
        return strategy_class

    def generate_init_method(self):
        return CodeMethod(
            name="__init__",
            parameters=[
                {"name": "self", "type": "self", "description": "Instance reference"},
                {"name": "config", "type": "Dict[str, any]", "description": "Strategy configuration", "default_value": "None"}
            ],
            return_type="None",
            description="Initialize the trading strategy",
            code=f"""        """Initialize the trading strategy with configuration."""\n        if config is None:\n            config = {{}}\n        self.name = "{self.workflow.get("name", "GeneratedStrategy")}"\n        self.config = config\n        self.data = pd.DataFrame()\n        self.indicators = {{}}\n        self.signals = {{}}\n        self.positions = {{}}\n        self.portfolio_value = 100000.0  # Default starting capital\n        self.risk_params = self._setup_risk_parameters()\n        self.logger = logging.getLogger(self.__class__.__name__)\n        \n        # Initialize performance tracking\n        self.trades = []\n        self.performance_metrics = {{\n            'total_return': 0.0,\n            'sharpe_ratio': 0.0,\n            'max_drawdown': 0.0,\n            'win_rate': 0.0\n        }}"""
        )

    def generate_setup_method(self, topology):
        data_source_nodes = topology["node_types"]["dataSources"]
        setup_code = "\n".join([
            f"        # Setup data source: {node['data']['label']}\n"\
            f"        self.symbol = \"{node['data'].get('parameters', {}) .get('symbol', 'AAPL')}\"\n"\
            f"        self.timeframe = \"{node['data'].get('parameters', {}) .get('timeframe', '1h')}\"\n"\
            f"        self.bars = {node['data'].get('parameters', {}) .get('bars', 1000)}"
            if node['type'] == 'dataSource' else
            f"        # Setup custom dataset: {node['data']['label']}\n"\
            f"        self.custom_data_path = \"{node['data'].get('parameters', {}) .get('fileName', 'custom_data.csv')}\""
            for node in data_source_nodes
        ]) or "        # No data sources configured\n        pass"

        return CodeMethod(
            name="setup",
            parameters=[{"name": "self", "type": "self", "description": "Instance reference"}],
            return_type="None",
            description="Setup strategy parameters and data sources",
            code=setup_code
        )

    def generate_on_data_method(self, topology):
        return CodeMethod(
            name="on_data",
            parameters=[
                {"name": "self", "type": "self", "description": "Instance reference"},
                {"name": "data", "type": "pd.DataFrame", "description": "New market data"}
            ],
            return_type="Dict[str, any]",
            description="Process new market data and generate trading signals",
            code="""        """Process new market data and generate trading signals."""\n        try:\n            # Update internal data\n            self.data = data\n            \n            # Calculate technical indicators\n            self.calculate_indicators()\n            \n            # Evaluate trading conditions\n            signals = self.evaluate_conditions()\n            \n            # Execute trading actions based on signals\n            actions = self.execute_actions(signals)\n            \n            # Apply risk management\n            actions = self.manage_risk(actions)\n            \n            # Log performance\n            self._log_performance()\n            \n            return {{\n                'signals': signals,\n                'actions': actions,\n                'indicators': self.indicators,\n                'portfolio_value': self.portfolio_value\n            }}\n            \n        except Exception as e:\n            self.logger.error(f"Error in on_data: {{str(e)}}")\n            return {{'error': str(e)}}\n"""
        )

    def generate_calculate_indicators_method(self, topology):
        indicator_nodes = topology["node_types"]["indicators"]
        indicator_code = "\n\n".join([
            self.generate_indicator_code(node['id'], node['data'].get('parameters', {}))
            for node in indicator_nodes
        ]) or "        # No indicators configured\n        pass"

        return CodeMethod(
            name="calculate_indicators",
            parameters=[{"name": "self", "type": "self", "description": "Instance reference"}],
            return_type="None",
            description="Calculate all technical indicators",
            code=indicator_code
        )

    def generate_indicator_code(self, node_id, params):
        indicator = params.get('indicator', 'SMA')
        period = params.get('period', 20)
        source = params.get('source', 'close')
        var_name = f"{indicator.lower()}_{node_id.replace('-', '_')}"

        if indicator == 'SMA':
            return f"        # Simple Moving Average\n        self.indicators['{{var_name}}'] = ta.SMA(self.data['{{source}}'], timeperiod={{period}})"
        elif indicator == 'EMA':
            return f"        # Exponential Moving Average\n        self.indicators['{{var_name}}'] = ta.EMA(self.data['{{source}}'], timeperiod={{period}})"
        elif indicator == 'RSI':
            return f"        # Relative Strength Index\n        self.indicators['{{var_name}}'] = ta.RSI(self.data['{{source}}'], timeperiod={{period}})"
        elif indicator == 'MACD':
            fast_period = params.get('fastPeriod', 12)
            slow_period = params.get('slowPeriod', 26)
            signal_period = params.get('signalPeriod', 9)
            return f"        # MACD\n        macd, signal, histogram = ta.MACD(self.data['{{source}}'], fastperiod={{fast_period}}, slowperiod={{slow_period}}, signalperiod={{signal_period}})\n        self.indicators['{{var_name}}_macd'] = macd\n        self.indicators['{{var_name}}_signal'] = signal\n        self.indicators['{{var_name}}_histogram'] = histogram"
        elif indicator == 'BB':
            multiplier = params.get('multiplier', 2.0)
            return f"        # Bollinger Bands\n        upper, middle, lower = ta.BBANDS(self.data['{{source}}'], timeperiod={{period}}, nbdevup={{multiplier}}, nbdevdn={{multiplier}})\n        self.indicators['{{var_name}}_upper'] = upper\n        self.indicators['{{var_name}}_middle'] = middle\n        self.indicators['{{var_name}}_lower'] = lower\n        self.indicators['{{var_name}}_width'] = (upper - lower) / middle"
        elif indicator == 'ATR':
            return f"        # Average True Range\n        self.indicators['{{var_name}}'] = ta.ATR(self.data['high'], self.data['low'], self.data['close'], timeperiod={{period}})"
        else:
            return f"        # {{indicator}} (Generic implementation)\n        self.indicators['{{var_name}}'] = ta.SMA(self.data['{{source}}'], timeperiod={{period}})"

    def generate_evaluate_conditions_method(self, topology):
        condition_nodes = topology["node_types"]["conditions"]
        logic_nodes = topology["node_types"]["logic"]
        condition_code = self.generate_conditions_code(condition_nodes, logic_nodes, topology)
        return CodeMethod(
            name="evaluate_conditions",
            parameters=[{"name": "self", "type": "self", "description": "Instance reference"}],
            return_type="Dict[str, bool]",
            description="Evaluate all trading conditions and logic",
            code=condition_code
        )

    def generate_conditions_code(self, condition_nodes, logic_nodes, topology):
        if not condition_nodes and not logic_nodes:
            return "        # No conditions configured\n        return {{}}"

        code = "        ""Evaluate all trading conditions and logic."""\n        signals = {{}}\n\n"
        
        indicator_var_map = {{
            node['id']: f"{{node['data'].get('parameters', {}) .get('indicator', 'SMA').lower()}}_{{node['id'].replace('-', '_')}}"
            for node in topology["node_types"]["indicators"]
        }}
        
        data_flow = topology['data_flow']

        for node in condition_nodes:
            params = node['data'].get('parameters', {}) 
            condition_type = params.get('conditionType', 'comparison')
            var_name = f"condition_{{node['id'].replace('-', '_')}}"

            if condition_type == 'comparison':
                condition = params.get('condition', 'greater_than')
                value = params.get('value', 0)
                operator = self.get_comparison_operator(condition)
                
                input_node_id = data_flow[node['id']]['inputs'][0] if data_flow[node['id']]['inputs'] else None
                input_var = indicator_var_map.get(input_node_id, "self.data['close']")

                code += f"""        # {{condition_type}} condition\n        try:\n            # Check if the indicator series is not empty and has a recent value\n            if not self.indicators['{{input_var}}'].empty:\n                current_value = self.indicators['{{input_var}}'].iloc[-1]\n                signals['{{var_name}}'] = current_value {{operator}} {{value}}\n            else:\n                signals['{{var_name}}'] = False\n        except (KeyError, IndexError) as e:\n            self.logger.warning(f"Could not evaluate condition for {{input_var}}: {{{{e}}}}")\n            signals['{{var_name}}'] = False\n\n"""
            elif condition_type == 'crossover':
                code += f"""        # Crossover condition\n        try:\n            # Implement crossover logic (requires two input series)\n            signals['{{var_name}}'] = False  # Placeholder\n        except Exception as e:\n            self.logger.warning(f"Error evaluating {{var_name}}: {{{{e}}}}")\n            signals['{{var_name}}'] = False\n\n"""
            else:
                code += f"        # {{condition_type}} condition\n        signals['{{var_name}}'] = False  # Placeholder\n\n"

        for node in logic_nodes:
            params = node['data'].get('parameters', {}) 
            operation = params.get('operation', 'AND')
            var_name = f"logic_{{node['id'].replace('-', '_')}}"
            
            input_node_ids = data_flow[node['id']]['inputs']
            input_signal_vars = []
            for nid in input_node_ids:
                input_node = next((n for n in self.nodes if n['id'] == nid), None)
                if input_node:
                    if input_node['type'] == 'condition':
                        input_signal_vars.append(f"signals.get('condition_{{nid.replace('-', '_')}}', False)")
                    elif input_node['type'] == 'logic':
                         input_signal_vars.append(f"signals.get('logic_{{nid.replace('-', '_')}}', False)")
            
            input_signals_str = f"[{{', '.join(input_signal_vars)}}]"
            code += f"""        # Logic gate: {{operation}}\n        try:\n            # Get input signals from connected conditions\n            input_signals = {{input_signals_str}}\n            if operation == 'AND':\n                signals['{{var_name}}'] = all(input_signals) if input_signals else False\n            elif operation == 'OR':\n                signals['{{var_name}}'] = any(input_signals) if input_signals else False\n            elif operation == 'NOT':\n                signals['{{var_name}}'] = not input_signals[0] if input_signals else True\n        except Exception as e:\n            self.logger.warning(f"Error evaluating {{var_name}}: {{{{e}}}}")\n            signals['{{var_name}}'] = False\n\n"""

        code += "\n        return signals"
        return code

    def generate_execute_actions_method(self, topology):
        action_nodes = topology["node_types"]["actions"]
        action_code = "\n\n".join([
            self.generate_action_code(node, topology)
            for node in action_nodes
        ]) or "        # No actions configured"

        return CodeMethod(
            name="execute_actions",
            parameters=[
                {"name": "self", "type": "self", "description": "Instance reference"},
                {"name": "signals", "type": "Dict[str, bool]", "description": "Trading signals"}
            ],
            return_type="List[Dict[str, any]]",
            description="Execute trading actions based on signals",
            code=f"        """Execute trading actions based on signals."""\n        actions = []\n\n{{action_code}}\n\n        return actions"
        )

    def generate_action_code(self, node, topology):
        node_id = node['id']
        params = node['data'].get('parameters', {}) 
        data_flow = topology['data_flow']

        input_node_ids = data_flow[node_id]['inputs']
        trigger_signal_var = "False"
        if input_node_ids:
            input_node_id = input_node_ids[0]
            input_node = next((n for n in self.nodes if n['id'] == input_node_id), None)
            if input_node:
                node_type = input_node['type']
                if node_type == 'condition':
                    trigger_signal_var = f"signals.get('condition_{{input_node_id.replace('-', '_')}}', False)"
                elif node_type == 'logic':
                    trigger_signal_var = f"signals.get('logic_{{input_node_id.replace('-', '_')}}', False)"

        action = params.get('action', 'buy')
        quantity = params.get('quantity', 10)
        order_type = params.get('order_type', 'market')
        stop_loss = params.get('stop_loss', 0)
        take_profit = params.get('take_profit', 0)
        return f"""        # {{action.upper()}} action\n        if {{trigger_signal_var}}:  # Signal from connected node\n            action = {{{{\n                'type': '{{action}}',\n                'symbol': self.symbol,\n                'quantity': {{quantity}},\n                'order_type': '{{order_type}}',\n                'timestamp': datetime.now(),\n                'stop_loss': {{stop_loss}},\n                'take_profit': {{take_profit}}\n            }}}}\n            actions.append(action)\n            self.logger.info(f"Generated {{{{action['type']}}}} order: {{{{action}}}}")\n"""

    def generate_manage_risk_method(self, topology):
        return CodeMethod(
            name="manage_risk",
            parameters=[
                {"name": "self", "type": "self", "description": "Instance reference"},
                {"name": "actions", "type": "List[Dict[str, any]]", "description": "Proposed trading actions"}
            ],
            return_type="List[Dict[str, any]]",
            description="Apply risk management to trading actions",
            code="""        """Apply risk management to trading actions."""\n        filtered_actions = []\n        \n        for action in actions:\n            # Apply position sizing\n            action['quantity'] = self._calculate_position_size(action)\n            \n            # Check portfolio heat\n            if self._check_portfolio_heat(action):\n                # Apply stop loss and take profit\n                action = self._apply_risk_controls(action)\n                filtered_actions.append(action)\n            else:\n                self.logger.warning(f"Action rejected due to risk limits: {{action}}")\n        \n        return filtered_actions\n"""
        )

    def generate_get_signals_method(self):
        return CodeMethod(
            name="get_signals",
            parameters=[{"name": "self", "type": "self", "description": "Instance reference"}],
            return_type="Dict[str, any]",
            description="Get current trading signals and indicators",
            code="""        """Get current trading signals and indicators."""\n        return {{\n            'signals': self.signals,\n            'indicators': self.indicators,\n            'portfolio_value': self.portfolio_value,\n            'positions': self.positions,\n            'timestamp': datetime.now()\n        }}\n"""
        )

    def generate_backtest_method(self):
        return CodeMethod(
            name="backtest",
            parameters=[
                {"name": "self", "type": "self", "description": "Instance reference"},
                {"name": "start_date", "type": "str", "description": "Backtest start date"},
                {"name": "end_date", "type": "str", "description": "Backtest end date"}
            ],
            return_type="Dict[str, any]",
            description="Run strategy backtest",
            code="""        """Run strategy backtest over specified period."""\n        try:\n            # Implement backtesting logic\n            results = {{\n                'total_return': 0.0,\n                'sharpe_ratio': 0.0,\n                'max_drawdown': 0.0,\n                'win_rate': 0.0,\n                'total_trades': 0,\n                'start_date': start_date,\n                'end_date': end_date\n            }}\n            \n            self.logger.info(f"Backtest completed: {{results}}")\n            return results\n            \n        except Exception as e:\n            self.logger.error(f"Backtest failed: {{str(e)}}")\n            return {{'error': str(e)}}\n"""
        )

    def generate_helper_functions(self):
        return [
            CodeFunction(
                name="_setup_risk_parameters",
                parameters=[{"name": "self", "type": "self", "description": "Instance reference"}],
                return_type="Dict[str, float]",
                description="Setup default risk management parameters",
                code="""        """Setup default risk management parameters."""\n        return {{\n            'max_position_size': 0.1,  # 10% of portfolio\n            'max_portfolio_heat': 0.2,  # 20% total risk\n            'stop_loss_pct': 0.02,  # 2% stop loss\n            'take_profit_pct': 0.04,  # 4% take profit\n            'max_drawdown': 0.15  # 15% max drawdown\n        }}\n"""
            ),
            CodeFunction(
                name="_calculate_position_size",
                parameters=[
                    {"name": "self", "type": "self", "description": "Instance reference"},
                    {"name": "action", "type": "Dict[str, any]", "description": "Trading action"}
                ],
                return_type="float",
                description="Calculate optimal position size based on risk parameters",
                code="""        """Calculate optimal position size based on risk parameters."""\n        risk_per_share = action.get('stop_loss', self.risk_params['stop_loss_pct'])\n        max_risk = self.portfolio_value * self.risk_params['max_position_size']\n        \n        if risk_per_share > 0:\n            position_size = max_risk / risk_per_share\n            return min(position_size, action['quantity'])\n        \n        return action['quantity']\n"""
            ),
            CodeFunction(
                name="_check_portfolio_heat",
                parameters=[
                    {"name": "self", "type": "self", "description": "Instance reference"},
                    {"name": "action", "type": "Dict[str, any]", "description": "Trading action"}
                ],
                return_type="bool",
                description="Check if action exceeds portfolio heat limits",
                code="""        """Check if action exceeds portfolio heat limits."""\n        current_heat = sum(abs(pos) for pos in self.positions.values())\n        new_heat = current_heat + abs(action['quantity'])\n        max_heat = self.portfolio_value * self.risk_params['max_portfolio_heat']\n        \n        return new_heat <= max_heat\n"""
            ),
            CodeFunction(
                name="_apply_risk_controls",
                parameters=[
                    {"name": "self", "type": "self", "description": "Instance reference"},
                    {"name": "action", "type": "Dict[str, any]", "description": "Trading action"}
                ],
                return_type="Dict[str, any]",
                description="Apply stop loss and take profit to action",
                code="""        """Apply stop loss and take profit to action."""\n        if action.get('stop_loss', 0) == 0:\n            action['stop_loss'] = self.risk_params['stop_loss_pct']\n        \n        if action.get('take_profit', 0) == 0:\n            action['take_profit'] = self.risk_params['take_profit_pct']\n        \n        return action\n"""
            ),
            CodeFunction(
                name="_log_performance",
                parameters=[{"name": "self", "type": "self", "description": "Instance reference"}],
                return_type="None",
                description="Log current performance metrics",
                code="""        """Log current performance metrics."""\n        if len(self.data) > 0:\n            self.logger.info(f"Portfolio Value: {{self.portfolio_value:.2f}}")\n            self.logger.info(f"Active Positions: {{len(self.positions)}}")\n            self.logger.info(f"Current Signals: {{sum(1 for s in self.signals.values() if s)}}")\n"""
            )
        ]

    def generate_tests(self):
        class_name = self.sanitize_class_name(self.workflow.get("name", "GeneratedStrategy"))
        return f""""""\nTest suite for {{self.workflow.get("name", "GeneratedStrategy")}} strategy\n"""\n\nimport unittest\nimport pandas as pd\nimport numpy as np\nfrom datetime import datetime, timedelta\n\nclass Test{{class_name}}(unittest.TestCase):\n    \n    def setUp(self):\n        """Setup test environment."""\n        self.strategy = {{class_name}}()\n        \n        # Create sample data\n        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='1H')\n        self.sample_data = pd.DataFrame({{{{ \n            'open': np.random.randn(len(dates)).cumsum() + 100,\n            'high': np.random.randn(len(dates)).cumsum() + 102,\n            'low': np.random.randn(len(dates)).cumsum() + 98,\n            'close': np.random.randn(len(dates)).cumsum() + 100,\n            'volume': np.random.randint(1000, 10000, len(dates))\n        }}}}, index=dates)\n    \n    def test_strategy_initialization(self):\n        """Test strategy initialization."""\n        self.assertEqual(self.strategy.name, "{{self.workflow.get('name', 'GeneratedStrategy')}}")\n        self.assertIsInstance(self.strategy.indicators, dict)\n        self.assertIsInstance(self.strategy.signals, dict)\n    \n    def test_indicator_calculation(self):\n        """Test technical indicator calculations."""\n        self.strategy.data = self.sample_data\n        self.strategy.calculate_indicators()\n        \n        # Check that indicators were calculated\n        self.assertGreater(len(self.strategy.indicators), 0)\n    \n    def test_signal_generation(self):\n        """Test trading signal generation."""\n        self.strategy.data = self.sample_data\n        self.strategy.calculate_indicators()\n        signals = self.strategy.evaluate_conditions()\n        \n        self.assertIsInstance(signals, dict)\n    \n    def test_risk_management(self):\n        """Test risk management functions."""\n        test_action = {{{{\n            'type': 'buy',\n            'quantity': 100,\n            'stop_loss': 0.02\n        }}}}\n        \n        size = self.strategy._calculate_position_size(test_action)\n        self.assertGreater(size, 0)\n        \n        heat_check = self.strategy._check_portfolio_heat(test_action)\n        self.assertIsInstance(heat_check, bool)\n    \n    def test_backtest(self):\n        """Test backtesting functionality."""\n        self.strategy.data = self.sample_data\n        results = self.strategy.backtest('2023-01-01', '2023-12-31')\n        \n        self.assertIn('total_return', results)\n        self.assertIn('sharpe_ratio', results)\n        self.assertIn('max_drawdown', results)\n\nif __name__ == '__main__':\n    unittest.main()\n"""

    def generate_documentation(self):
        return f"""# {{self.workflow.get("name", "GeneratedStrategy")}} - Trading Strategy Documentation\n\n## Overview\n{{self.workflow.get("description", "Generated trading strategy using Alphintra No-Code Console")}}\n\n**Generated:** {{datetime.utcnow().isoformat()}}\n**Version:** 1.0.0\n\n## Strategy Components\n\n### Data Sources\n{{"\n".join([f"- **{{node['data']['label']}}**: {{'Market data feed' if node['type'] == 'dataSource' else 'Custom dataset'}}" for node in self.nodes if node['type'] in ['dataSource', 'customDataset']])}}\n\n### Technical Indicators\n{{"\n".join([f"- **{{node['data']['label']}}**: {{node['data'].get('parameters', {}) .get('indicator', 'Unknown')}} (Period: {{node['data'].get('parameters', {}) .get('period', 'N/A')}})" for node in self.nodes if node['type'] == 'technicalIndicator']])}}\n\n### Trading Conditions\n{{"\n".join([f"- **{{node['data']['label']}}**: {{node['data'].get('parameters', {}) .get('condition', 'Unknown condition')}}" for node in self.nodes if node['type'] == 'condition']])}}\n\n### Actions\n{{"\n".join([f"- **{{node['data']['label']}}**: {{node['data'].get('parameters', {}) .get('action', 'Unknown action')}}" for node in self.nodes if node['type'] == 'action']])}}\n\n### Risk Management\n{{"\n".join([f"- **{{node['data']['label']}}**: {{node['data'].get('parameters', {}) .get('riskType', 'Unknown risk control')}}" for node in self.nodes if node['type'] == 'risk']])}}\n\n## Usage\n\n```python\n# Initialize strategy\nstrategy = {{self.sanitize_class_name(self.workflow.get("name", "GeneratedStrategy"))}}()\n\n# Setup with configuration\nstrategy.setup()\n\n# Process market data\nresult = strategy.on_data(market_data)\n\n# Run backtest\nbacktest_results = strategy.backtest('2023-01-01', '2023-12-31')\n```\n\n## Performance Characteristics\n\n- **Estimated Complexity**: {{self.calculate_complexity()}}\n- **Estimated Execution Time**: {{self.estimate_performance()['executionTime']}}\n- **Memory Usage**: {{self.estimate_performance()['memoryUsage']}}\n\n## Risk Controls\n\n- Position sizing based on portfolio percentage\n- Stop loss and take profit management\n- Portfolio heat monitoring\n- Maximum drawdown limits\n\n## Notes\n\nThis strategy was automatically generated from a visual workflow. \nReview and test thoroughly before using in production.\n"""

    def assemble_strategy_code(self, imports, strategy_class, helper_functions):
        imports_section = "\n".join(imports)
        class_section = self.generate_class_code(strategy_class)
        functions_section = "\n\n".join([self.generate_function_code(func) for func in helper_functions])

        return f"""{{imports_section}}\n\n# Generated Trading Strategy: {{self.workflow.get("name", "GeneratedStrategy")}}\n# Created: {{datetime.utcnow().isoformat()}}\n# Generator: Alphintra Advanced Code Generator v1.0.0\n\n{{class_section}}\n\n{{functions_section}}\n\n# Example usage\nif __name__ == "__main__":\n    # Initialize strategy\n    strategy = {{strategy_class.name}}()\n    \n    # Setup strategy\n    strategy.setup()\n    \n    print(f"Strategy '{{{{strategy.name}}}}' initialized successfully!")\n    print(f"Indicators: {{{{list(strategy.indicators.keys())}}}}")\n    print(f"Risk Parameters: {{{{strategy.risk_params}}}}")\n"""

    def generate_class_code(self, class_obj):
        methods_code = "\n\n".join([
            f"    def {{method.name}}(f{{', '.join([p['name'] + (f' = {{p['default_value']}}' if 'default_value' in p else '') for p in method.parameters])}}) -> {{method.return_type}}:\n"\
            f"        """{{method.description}}"""\n{{method.code}}"
            for method in class_obj.methods
        ])

        return f"""class {{class_obj.name}}:\n    """{{class_obj.description}}"""\n    \n{{methods_code}}"""

    def generate_function_code(self, func):
        return f"""def {{func.name}}(f{{', '.join([p['name'] + (f' = {{p['default_value']}}' if 'default_value' in p else '') for p in func.parameters])}}) -> {{func.return_type}}:\n    """{{func.description}}"""\n{{func.code}}"""

    def get_node_data_type(self, node):
        node_type = node.get('type')
        if node_type in ['dataSource', 'customDataset']:
            return 'ohlcv'
        elif node_type == 'technicalIndicator':
            return 'numeric'
        elif node_type in ['condition', 'logic']:
            return 'signal'
        elif node_type == 'action':
            return 'order'
        elif node_type == 'risk':
            return 'risk'
        else:
            return 'unknown'

    def get_comparison_operator(self, condition):
        operators = {{
            'greater_than': '>','
            'less_than': '<',
            'greater_than_equal': '>=',
            'less_than_equal': '<=',
            'equal': '==',
            'not_equal': '!='
        }}
        return operators.get(condition, '>')

    def sanitize_class_name(self, name):
        import re
        name = re.sub(r'[^a-zA-Z0-9]', '', name)
        if name[0].isdigit():
            name = 'Strategy' + name
        return name or 'GeneratedStrategy'

    def calculate_complexity(self):
        return len(self.nodes) * 10 + len(self.edges) * 5

    def estimate_performance(self):
        complexity = self.calculate_complexity()
        if complexity < 100:
            return {'executionTime': '<10ms', 'memoryUsage': '<1MB', 'backtestSpeed': 'Fast'}
        elif complexity < 500:
            return {'executionTime': '<50ms', 'memoryUsage': '<5MB', 'backtestSpeed': 'Medium'}
        else:
            return {'executionTime': '<100ms', 'memoryUsage': '<10MB', 'backtestSpeed': 'Slow'}

def generate_strategy_code(workflow: Dict[str, Any]) -> GeneratedCode:
    generator = AdvancedCodeGenerator(workflow)
    return generator.generate_strategy()
