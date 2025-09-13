"""Enhanced Node Handlers for the Compiler System.

This module provides enhanced node handlers that generate optimized code
and support the compiler's type system and optimization framework.
"""

import json
from typing import List, Dict, Any, Optional
from node_handlers.base import NodeHandler
from ir import Node


class EnhancedDataSourceHandler(NodeHandler):
    """Enhanced handler for data source nodes."""
    
    node_type = "dataSource"

    def handle(self, node: Node, generator) -> str:
        params = node.data.get("parameters", {})
        symbol = params.get("symbol", "AAPL")
        timeframe = params.get("timeframe", "1h")
        bars = params.get("bars", 1000)
        asset_class = params.get("assetClass", "stocks")
        data_source = params.get("dataSource", "system")
        
        node_var = f"data_{self.sanitize_id(node.id)}"
        
        if data_source == "system":
            # Generate system data loading code
            code = f"""
# Load {symbol} data ({timeframe}, {bars} bars)
try:
    # In a real implementation, this would connect to your data provider
    import yfinance as yf
    ticker = yf.Ticker("{symbol}")
    {node_var} = ticker.history(period="1y", interval="{timeframe}")
    {node_var} = {node_var}.tail({bars}).copy()
    
    # Ensure we have OHLCV columns
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    if all(col in {node_var}.columns for col in required_cols):
        # Standardize column names
        {node_var}.columns = [col.lower() for col in {node_var}.columns]
        df = {node_var}  # Set as main dataframe
        print(f"Loaded {{len(df)}} rows of {symbol} data")
    else:
        raise ValueError(f"Missing required OHLCV columns for {symbol}")
        
except Exception as e:
    print(f"Error loading {symbol} data: {{e}}")
    # Fallback to synthetic data for testing
    import pandas as pd
    import numpy as np
    dates = pd.date_range(start='2023-01-01', periods={bars}, freq='1H')
    np.random.seed(42)
    base_price = 100
    returns = np.random.normal(0.0001, 0.02, {bars})
    prices = base_price * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame({{
        'open': prices * (1 + np.random.normal(0, 0.001, {bars})),
        'high': prices * (1 + np.abs(np.random.normal(0, 0.01, {bars}))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.01, {bars}))),
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, {bars})
    }}, index=dates)
    
    print(f"Using synthetic data for {symbol} ({bars} rows)")
"""
        else:
            # User uploaded data
            code = f"""
# Load custom dataset for {symbol}
# Note: In production, implement file upload handling
df = pd.read_csv("uploaded_data_{symbol}.csv")
df.index = pd.to_datetime(df.index)
print(f"Loaded {{len(df)}} rows from custom dataset")
"""
        
        return code.strip()

    def required_packages(self) -> List[str]:
        return ["pandas", "numpy", "yfinance"]


class EnhancedTechnicalIndicatorHandler(NodeHandler):
    """Enhanced handler for technical indicator nodes."""
    
    node_type = "technicalIndicator"

    def handle(self, node: Node, generator) -> str:
        params = node.data.get("parameters", {})
        indicator = params.get("indicator", "SMA")
        period = params.get("period", 20)
        source_col = params.get("source", "close")
        category = params.get("indicatorCategory", "trend")
        
        feature_name = f"feature_{self.sanitize_id(node.id)}"
        
        # Check for optimizations
        optimizations = getattr(node, 'optimizations', [])
        vectorized = "vectorized" in optimizations
        
        if vectorized:
            code = f"# Vectorized {indicator} calculation"
        else:
            code = f"# {indicator} calculation"
        
        # Generate indicator-specific code
        if indicator == "SMA":
            code += f"""
df['{feature_name}'] = df['{source_col}'].rolling(window={period}).mean()"""
        
        elif indicator == "EMA":
            code += f"""
df['{feature_name}'] = df['{source_col}'].ewm(span={period}).mean()"""
        
        elif indicator == "RSI":
            code += f"""
# RSI calculation
delta = df['{source_col}'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window={period}).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window={period}).mean()
rs = gain / loss
df['{feature_name}'] = 100 - (100 / (1 + rs))"""
        
        elif indicator == "MACD":
            fast_period = params.get("fastPeriod", 12)
            slow_period = params.get("slowPeriod", 26)
            signal_period = params.get("signalPeriod", 9)
            
            code += f"""
# MACD calculation
ema_fast = df['{source_col}'].ewm(span={fast_period}).mean()
ema_slow = df['{source_col}'].ewm(span={slow_period}).mean()
df['{feature_name}'] = ema_fast - ema_slow
df['{feature_name}_signal'] = df['{feature_name}'].ewm(span={signal_period}).mean()
df['{feature_name}_histogram'] = df['{feature_name}'] - df['{feature_name}_signal']"""
        
        elif indicator == "BB":  # Bollinger Bands
            std_dev = params.get("multiplier", 2)
            
            code += f"""
# Bollinger Bands calculation
sma = df['{source_col}'].rolling(window={period}).mean()
std = df['{source_col}'].rolling(window={period}).std()
df['{feature_name}_upper'] = sma + (std * {std_dev})
df['{feature_name}_middle'] = sma
df['{feature_name}_lower'] = sma - (std * {std_dev})
df['{feature_name}_width'] = df['{feature_name}_upper'] - df['{feature_name}_lower']
df['{feature_name}'] = df['{feature_name}_middle']  # Main output"""
        
        elif indicator == "ADX":
            code += f"""
# ADX calculation using TA-Lib
try:
    import talib as ta
    df['{feature_name}'] = ta.ADX(
        df['high'].values, 
        df['low'].values, 
        df['{source_col}'].values, 
        timeperiod={period}
    )
    df['{feature_name}_di_plus'] = ta.PLUS_DI(
        df['high'].values, 
        df['low'].values, 
        df['{source_col}'].values, 
        timeperiod={period}
    )
    df['{feature_name}_di_minus'] = ta.MINUS_DI(
        df['high'].values, 
        df['low'].values, 
        df['{source_col}'].values, 
        timeperiod={period}
    )
except ImportError:
    # Fallback ADX calculation
    print("TA-Lib not available, using simplified ADX calculation")
    df['{feature_name}'] = df['{source_col}'].rolling({period}).std()"""
        
        elif indicator == "STOCH":  # Stochastic
            k_period = params.get("kPeriod", 14)
            d_period = params.get("dPeriod", 3)
            
            code += f"""
# Stochastic calculation
lowest_low = df['low'].rolling(window={k_period}).min()
highest_high = df['high'].rolling(window={k_period}).max()
df['{feature_name}_k'] = 100 * ((df['{source_col}'] - lowest_low) / (highest_high - lowest_low))
df['{feature_name}_d'] = df['{feature_name}_k'].rolling(window={d_period}).mean()
df['{feature_name}'] = df['{feature_name}_k']  # Main output"""
        
        else:
            # Generic indicator using TA-Lib if available
            code += f"""
# Generic {indicator} calculation
try:
    import talib as ta
    if hasattr(ta, '{indicator.upper()}'):
        df['{feature_name}'] = getattr(ta, '{indicator.upper()}')(
            df['{source_col}'].values, timeperiod={period}
        )
    else:
        # Fallback to simple moving average
        df['{feature_name}'] = df['{source_col}'].rolling(window={period}).mean()
except ImportError:
    # Fallback calculation
    df['{feature_name}'] = df['{source_col}'].rolling(window={period}).mean()"""

        # Add data validation
        code += f"""
# Validate {indicator} output
df['{feature_name}'] = df['{feature_name}'].fillna(method='bfill').fillna(0)"""
        
        return code

    def required_packages(self) -> List[str]:
        return ["pandas", "numpy", "ta-lib"]


class EnhancedConditionHandler(NodeHandler):
    """Enhanced handler for condition nodes."""
    
    node_type = "condition"

    def handle(self, node: Node, generator) -> str:
        params = node.data.get("parameters", {})
        condition_type = params.get("conditionType", "comparison")
        condition = params.get("condition", "greater_than")
        value = params.get("value", 0)
        value2 = params.get("value2")
        lookback = params.get("lookback", 1)
        confirmation_bars = params.get("confirmationBars", 0)
        
        target_col = f"target_{self.sanitize_id(node.id)}"
        signal_col = f"signal_{self.sanitize_id(node.id)}"
        
        # Get input connections
        inputs = generator.get_incoming(node.id) if hasattr(generator, 'get_incoming') else []
        
        if inputs:
            input_feature = f"feature_{self.sanitize_id(inputs[0])}"
        else:
            input_feature = "close"  # Default to close price
        
        code = f"# Condition: {condition_type} - {condition}"
        
        # Generate condition logic based on type
        if condition_type == "comparison":
            if condition == "greater_than":
                condition_expr = f"df['{input_feature}'] > {value}"
            elif condition == "less_than":
                condition_expr = f"df['{input_feature}'] < {value}"
            elif condition == "equal_to":
                condition_expr = f"df['{input_feature}'] == {value}"
            elif condition == "range" and value2 is not None:
                condition_expr = f"(df['{input_feature}'] >= {value}) & (df['{input_feature}'] <= {value2})"
            else:
                condition_expr = f"df['{input_feature}'] > {value}"
        
        elif condition_type == "crossover":
            if condition == "crossover":
                condition_expr = f"""(df['{input_feature}'] > {value}) & (df['{input_feature}'].shift(1) <= {value})"""
            elif condition == "crossunder":
                condition_expr = f"""(df['{input_feature}'] < {value}) & (df['{input_feature}'].shift(1) >= {value})"""
            else:
                condition_expr = f"df['{input_feature}'] > {value}"
        
        elif condition_type == "trend":
            if condition == "rising":
                condition_expr = f"df['{input_feature}'] > df['{input_feature}'].shift({lookback})"
            elif condition == "falling":
                condition_expr = f"df['{input_feature}'] < df['{input_feature}'].shift({lookback})"
            else:
                condition_expr = f"df['{input_feature}'] > df['{input_feature}'].shift(1)"
        
        else:
            # Default condition
            condition_expr = f"df['{input_feature}'] > {value}"
        
        code += f"""
# Apply condition logic
condition_raw = {condition_expr}
"""
        
        # Add confirmation bars logic
        if confirmation_bars > 0:
            code += f"""
# Apply confirmation bars ({confirmation_bars})
condition_confirmed = condition_raw.copy()
for i in range(1, {confirmation_bars + 1}):
    condition_confirmed &= condition_raw.shift(i)
df['{signal_col}'] = condition_confirmed.astype(int)
"""
        else:
            code += f"""
df['{signal_col}'] = condition_raw.astype(int)
"""
        
        # Create target for training
        code += f"""
# Create target variable for training
df['{target_col}'] = df['{signal_col}'].copy()
"""
        
        return code

    def required_packages(self) -> List[str]:
        return ["pandas", "numpy"]


class EnhancedLogicHandler(NodeHandler):
    """Enhanced handler for logic nodes."""
    
    node_type = "logic"

    def handle(self, node: Node, generator) -> str:
        params = node.data.get("parameters", {})
        operation = params.get("operation", "AND")
        num_inputs = params.get("inputs", 2)
        
        output_col = f"signal_{self.sanitize_id(node.id)}"
        
        # Get input connections
        inputs = generator.get_incoming(node.id) if hasattr(generator, 'get_incoming') else []
        
        if len(inputs) < num_inputs:
            # Pad with default signals if needed
            while len(inputs) < num_inputs:
                inputs.append("default_signal")
        
        input_signals = [f"signal_{self.sanitize_id(inp)}" if inp != "default_signal" else "False" 
                        for inp in inputs[:num_inputs]]
        
        code = f"# Logic Gate: {operation} with {num_inputs} inputs"
        
        # Ensure input signals exist
        for i, signal in enumerate(input_signals):
            if signal != "False":
                code += f"""
if '{signal}' not in df.columns:
    df['{signal}'] = 0  # Default to False if signal doesn't exist
"""
        
        # Generate logic operation
        if operation == "AND":
            logic_expr = " & ".join([f"(df['{sig}'] == 1)" if sig != "False" else "False" 
                                   for sig in input_signals])
        elif operation == "OR":
            logic_expr = " | ".join([f"(df['{sig}'] == 1)" if sig != "False" else "False" 
                                   for sig in input_signals])
        elif operation == "NOT" and num_inputs == 1:
            logic_expr = f"~(df['{input_signals[0]}'] == 1)" if input_signals[0] != "False" else "True"
        elif operation == "XOR":
            if num_inputs == 2:
                logic_expr = f"(df['{input_signals[0]}'] == 1) ^ (df['{input_signals[1]}'] == 1)"
            else:
                # XOR for multiple inputs (odd number of True inputs)
                signal_terms = [f"(df['{sig}'] == 1)" for sig in input_signals if sig != 'False']
                logic_expr = f"({' + '.join(signal_terms)}) % 2 == 1"
        else:
            # Default to AND
            logic_expr = " & ".join([f"(df['{sig}'] == 1)" if sig != "False" else "False" 
                                   for sig in input_signals])
        
        code += f"""
# Apply {operation} logic
df['{output_col}'] = ({logic_expr}).astype(int)
"""
        
        return code

    def required_packages(self) -> List[str]:
        return ["pandas", "numpy"]


class EnhancedActionHandler(NodeHandler):
    """Enhanced handler for action nodes."""
    
    node_type = "action"

    def handle(self, node: Node, generator) -> str:
        params = node.data.get("parameters", {})
        action_category = params.get("actionCategory", "entry")
        action = params.get("action", "buy")
        quantity = params.get("quantity", 1)
        order_type = params.get("order_type", "market")
        position_sizing = params.get("positionSizing", "fixed")
        stop_loss = params.get("stop_loss")
        take_profit = params.get("take_profit")
        
        action_col = f"action_{self.sanitize_id(node.id)}"
        
        # Get signal input
        inputs = generator.get_incoming(node.id) if hasattr(generator, 'get_incoming') else []
        signal_input = f"signal_{self.sanitize_id(inputs[0])}" if inputs else "signal_default"
        
        code = f"# Action: {action_category} - {action} ({order_type})"
        
        # Ensure signal exists
        code += f"""
if '{signal_input}' not in df.columns:
    df['{signal_input}'] = 0  # Default signal
"""
        
        # Generate action logic
        if action in ["buy", "long"]:
            action_value = 1
        elif action in ["sell", "short"]:
            action_value = -1
        else:
            action_value = 0
        
        code += f"""
# Generate {action} actions
df['{action_col}'] = 0  # Initialize

# Apply action when signal is active
active_signals = df['{signal_input}'] == 1
df.loc[active_signals, '{action_col}'] = {action_value}

# Position sizing logic
if '{position_sizing}' == 'percentage':
    # Percentage of portfolio
    df['{action_col}_size'] = df['{action_col}'] * ({quantity} / 100.0)
elif '{position_sizing}' == 'fixed':
    # Fixed quantity
    df['{action_col}_size'] = df['{action_col}'] * {quantity}
else:
    # Default to fixed
    df['{action_col}_size'] = df['{action_col}'] * {quantity}
"""
        
        # Add risk management if specified
        if stop_loss or take_profit:
            code += f"""
# Risk management
if {stop_loss is not None}:
    df['{action_col}_stop_loss'] = {stop_loss}
if {take_profit is not None}:
    df['{action_col}_take_profit'] = {take_profit}
"""
        
        return code

    def required_packages(self) -> List[str]:
        return ["pandas", "numpy"]


class EnhancedRiskManagementHandler(NodeHandler):
    """Enhanced handler for risk management nodes."""
    
    node_type = "riskManagement"

    def handle(self, node: Node, generator) -> str:
        params = node.data.get("parameters", {})
        risk_category = params.get("riskCategory", "position")
        risk_type = params.get("riskType", "position_size")
        risk_level = params.get("riskLevel", 2)
        max_loss = params.get("maxLoss", 2.0)
        portfolio_heat = params.get("portfolioHeat", 10.0)
        
        risk_col = f"risk_{self.sanitize_id(node.id)}"
        
        code = f"# Risk Management: {risk_category} - {risk_type}"
        
        if risk_type == "position_size":
            code += f"""
# Position size risk management
df['{risk_col}_max_position'] = {max_loss / 100.0}  # Max position as percentage
df['{risk_col}_portfolio_heat'] = {portfolio_heat / 100.0}  # Portfolio heat limit

# Calculate position size based on risk
df['{risk_col}_volatility'] = df['close'].pct_change().rolling(20).std()
df['{risk_col}_position_size'] = np.minimum(
    df['{risk_col}_max_position'] / (df['{risk_col}_volatility'] * 2),
    df['{risk_col}_portfolio_heat']
)
"""
        
        elif risk_type == "drawdown_limit":
            drawdown_limit = params.get("drawdownLimit", 10.0)
            code += f"""
# Drawdown limit risk management
df['{risk_col}_drawdown_limit'] = {drawdown_limit / 100.0}

# Calculate running drawdown (simplified)
df['{risk_col}_peak'] = df['close'].expanding().max()
df['{risk_col}_drawdown'] = (df['close'] - df['{risk_col}_peak']) / df['{risk_col}_peak']
df['{risk_col}_breach'] = df['{risk_col}_drawdown'] < -df['{risk_col}_drawdown_limit']
"""
        
        else:
            # Generic risk management
            code += f"""
# Generic risk management (level {risk_level})
df['{risk_col}_level'] = {risk_level}
df['{risk_col}_multiplier'] = 1.0 / {risk_level}  # Reduce size based on risk level
"""
        
        return code

    def required_packages(self) -> List[str]:
        return ["pandas", "numpy"]


class EnhancedCustomDatasetHandler(NodeHandler):
    """Enhanced handler for custom dataset nodes."""
    
    node_type = "customDataset"

    def handle(self, node: Node, generator) -> str:
        params = node.data.get("parameters", {})
        file_name = params.get("fileName", "custom_data.csv")
        columns = params.get("columns", [])
        date_column = params.get("dateColumn", "date")
        ohlc_mapping = params.get("ohlcMapping", {})
        
        node_var = f"data_{self.sanitize_id(node.id)}"
        
        code = f"""
# Load custom dataset: {file_name}
try:
    {node_var} = pd.read_csv("{file_name}")
    
    # Set date index if specified
    if "{date_column}" in {node_var}.columns:
        {node_var}["{date_column}"] = pd.to_datetime({node_var}["{date_column}"])
        {node_var}.set_index("{date_column}", inplace=True)
    
    # Map OHLCV columns if specified
    ohlc_mapping = {ohlc_mapping if ohlc_mapping else {}}
    if ohlc_mapping:
        for standard_col, custom_col in ohlc_mapping.items():
            if custom_col in {node_var}.columns:
                {node_var}[standard_col] = {node_var}[custom_col]
    
    # Ensure we have basic OHLC columns
    required_cols = ['open', 'high', 'low', 'close']
    missing_cols = [col for col in required_cols if col not in {node_var}.columns]
    
    if missing_cols:
        print(f"Warning: Missing columns {{missing_cols}} in custom dataset")
        # Create synthetic columns if needed
        if 'close' in {node_var}.columns:
            base_col = 'close'
        elif len({node_var}.columns) > 0:
            base_col = {node_var}.columns[0]  # Use first available column
        else:
            raise ValueError("No usable columns found in custom dataset")
        
        for col in missing_cols:
            {node_var}[col] = {node_var}[base_col] * (1 + np.random.normal(0, 0.001, len({node_var})))
    
    df = {node_var}  # Set as main dataframe
    print(f"Loaded {{len(df)}} rows from custom dataset")
    
except Exception as e:
    print(f"Error loading custom dataset: {{e}}")
    # Create fallback synthetic data
    dates = pd.date_range(start='2023-01-01', periods=1000, freq='1H')
    np.random.seed(42)
    base_price = 100
    returns = np.random.normal(0.0001, 0.02, 1000)
    prices = base_price * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame({{
        'open': prices * (1 + np.random.normal(0, 0.001, 1000)),
        'high': prices * (1 + np.abs(np.random.normal(0, 0.01, 1000))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.01, 1000))),
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, 1000)
    }}, index=dates)
    
    print("Using fallback synthetic data")
"""
        
        return code

    def required_packages(self) -> List[str]:
        return ["pandas", "numpy"]


# Registry of enhanced handlers
ENHANCED_HANDLER_REGISTRY = {
    "dataSource": EnhancedDataSourceHandler(),
    "customDataset": EnhancedCustomDatasetHandler(),
    "technicalIndicator": EnhancedTechnicalIndicatorHandler(),
    "condition": EnhancedConditionHandler(),
    "logic": EnhancedLogicHandler(),
    "action": EnhancedActionHandler(),
    "riskManagement": EnhancedRiskManagementHandler(),
}

__all__ = [
    "EnhancedDataSourceHandler",
    "EnhancedCustomDatasetHandler", 
    "EnhancedTechnicalIndicatorHandler",
    "EnhancedConditionHandler",
    "EnhancedLogicHandler",
    "EnhancedActionHandler",
    "EnhancedRiskManagementHandler",
    "ENHANCED_HANDLER_REGISTRY"
]