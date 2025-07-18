-- No-Code Console Database Schema
-- This schema supports the visual workflow builder and strategy generation

-- Enable required extensions if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- No-code workflows table
CREATE TABLE nocode_workflows (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) DEFAULT 'custom' CHECK (category IN ('technical_analysis', 'fundamental_analysis', 'risk_management', 'portfolio_optimization', 'custom')),
    tags TEXT[] DEFAULT '{}',
    
    -- Workflow definition (React Flow format)
    workflow_data JSONB NOT NULL DEFAULT '{"nodes": [], "edges": []}',
    
    -- Generated strategy code
    generated_code TEXT,
    generated_code_language VARCHAR(20) DEFAULT 'python',
    generated_requirements TEXT[] DEFAULT '{}',
    
    -- Compilation and validation status
    compilation_status VARCHAR(20) DEFAULT 'pending' CHECK (compilation_status IN ('pending', 'compiling', 'compiled', 'failed')),
    compilation_errors JSONB DEFAULT '[]',
    validation_status VARCHAR(20) DEFAULT 'pending' CHECK (validation_status IN ('pending', 'validating', 'valid', 'invalid')),
    validation_errors JSONB DEFAULT '[]',
    
    -- Deployment and execution
    deployment_status VARCHAR(20) DEFAULT 'draft' CHECK (deployment_status IN ('draft', 'deployed', 'archived')),
    execution_mode VARCHAR(20) DEFAULT 'backtest' CHECK (execution_mode IN ('backtest', 'paper', 'live')),
    
    -- Versioning
    version INTEGER DEFAULT 1,
    parent_workflow_id INTEGER REFERENCES nocode_workflows(id) ON DELETE SET NULL,
    is_template BOOLEAN DEFAULT false,
    is_public BOOLEAN DEFAULT false,
    
    -- Performance and usage metrics
    total_executions INTEGER DEFAULT 0,
    successful_executions INTEGER DEFAULT 0,
    avg_performance_score DECIMAL(5,2) DEFAULT 0.0,
    last_execution_at TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    published_at TIMESTAMP
);

-- No-code workflow components/nodes library
CREATE TABLE nocode_components (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL CHECK (category IN ('data_source', 'indicator', 'condition', 'action', 'risk_management', 'output', 'logic', 'custom')),
    subcategory VARCHAR(50),
    
    -- Component definition
    component_type VARCHAR(50) NOT NULL,
    input_schema JSONB NOT NULL DEFAULT '{}',
    output_schema JSONB NOT NULL DEFAULT '{}',
    parameters_schema JSONB NOT NULL DEFAULT '{}',
    default_parameters JSONB DEFAULT '{}',
    
    -- Code templates
    code_template TEXT NOT NULL,
    imports_required TEXT[] DEFAULT '{}',
    dependencies TEXT[] DEFAULT '{}',
    
    -- UI configuration
    ui_config JSONB DEFAULT '{"width": 200, "height": 100, "color": "#1f2937"}',
    icon VARCHAR(100),
    
    -- Metadata
    author_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    is_builtin BOOLEAN DEFAULT false,
    is_public BOOLEAN DEFAULT false,
    usage_count INTEGER DEFAULT 0,
    rating DECIMAL(2,1) DEFAULT 0.0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- No-code workflow executions
CREATE TABLE nocode_executions (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    workflow_id INTEGER REFERENCES nocode_workflows(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    
    -- Execution configuration
    execution_type VARCHAR(20) NOT NULL CHECK (execution_type IN ('backtest', 'paper_trade', 'live_trade', 'validation')),
    parameters JSONB DEFAULT '{}',
    
    -- Market data and timeframe
    symbols TEXT[] NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    initial_capital DECIMAL(20,8) DEFAULT 10000.0,
    
    -- Execution status and progress
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    current_step VARCHAR(255),
    
    -- Results and performance
    final_capital DECIMAL(20,8),
    total_return DECIMAL(10,4),
    total_return_percent DECIMAL(6,2),
    sharpe_ratio DECIMAL(6,3),
    max_drawdown_percent DECIMAL(6,2),
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    
    -- Execution data
    trades_data JSONB DEFAULT '[]',
    performance_metrics JSONB DEFAULT '{}',
    execution_logs JSONB DEFAULT '[]',
    error_logs JSONB DEFAULT '[]',
    
    -- Timestamps
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- No-code templates library
CREATE TABLE nocode_templates (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    difficulty_level VARCHAR(20) DEFAULT 'beginner' CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced')),
    
    -- Template workflow definition
    template_data JSONB NOT NULL,
    preview_image_url VARCHAR(500),
    
    -- Metadata
    author_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    is_featured BOOLEAN DEFAULT false,
    is_public BOOLEAN DEFAULT true,
    usage_count INTEGER DEFAULT 0,
    rating DECIMAL(2,1) DEFAULT 0.0,
    
    -- SEO and discovery
    keywords TEXT[] DEFAULT '{}',
    estimated_time_minutes INTEGER,
    expected_performance JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- No-code workflow sharing and marketplace
CREATE TABLE nocode_workflow_shares (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER REFERENCES nocode_workflows(id) ON DELETE CASCADE,
    shared_by_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    shared_with_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    permission_level VARCHAR(20) DEFAULT 'view' CHECK (permission_level IN ('view', 'edit', 'execute')),
    shared_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- No-code component ratings and reviews
CREATE TABLE nocode_component_reviews (
    id SERIAL PRIMARY KEY,
    component_id INTEGER REFERENCES nocode_components(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    review_text TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(component_id, user_id)
);

-- No-code workflow analytics
CREATE TABLE nocode_workflow_analytics (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER REFERENCES nocode_workflows(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN ('created', 'opened', 'modified', 'compiled', 'executed', 'shared', 'cloned')),
    event_data JSONB DEFAULT '{}',
    session_id UUID,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Data sources configuration for no-code workflows
CREATE TABLE nocode_data_sources (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('rest_api', 'websocket', 'database', 'file', 'stream')),
    
    -- Connection configuration
    connection_config JSONB NOT NULL DEFAULT '{}',
    authentication_config JSONB DEFAULT '{}',
    
    -- Data schema and mapping
    data_schema JSONB DEFAULT '{}',
    field_mappings JSONB DEFAULT '{}',
    
    -- Status and testing
    status VARCHAR(20) DEFAULT 'inactive' CHECK (status IN ('active', 'inactive', 'error', 'testing')),
    last_test_result JSONB,
    last_test_at TIMESTAMP,
    
    -- Usage and performance
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    avg_response_time_ms INTEGER,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Compilation results for workflow code generation
CREATE TABLE compilation_results (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER REFERENCES nocode_workflows(id) ON DELETE CASCADE,
    compiled_code TEXT,
    compilation_status VARCHAR(20) DEFAULT 'pending' CHECK (compilation_status IN ('pending', 'success', 'failed')),
    compilation_errors JSONB DEFAULT '[]',
    compilation_warnings JSONB DEFAULT '[]',
    dependencies TEXT[] DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Training jobs for ML model training
CREATE TABLE training_jobs (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER REFERENCES nocode_workflows(id) ON DELETE CASCADE,
    compilation_id INTEGER REFERENCES compilation_results(id) ON DELETE CASCADE,
    dataset_id INTEGER,
    config JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    current_epoch INTEGER DEFAULT 0,
    total_epochs INTEGER DEFAULT 100,
    metrics JSONB DEFAULT '{}',
    model_artifacts JSONB DEFAULT '{}',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Datasets for training and backtesting
CREATE TABLE datasets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    dataset_type VARCHAR(50) NOT NULL CHECK (dataset_type IN ('market_data', 'fundamental', 'alternative', 'custom')),
    file_path VARCHAR(500),
    file_size BIGINT,
    schema_info JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    is_public BOOLEAN DEFAULT false,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Component library for custom components
CREATE TABLE component_library (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) DEFAULT '1.0.0',
    description TEXT,
    component_code TEXT NOT NULL,
    component_schema JSONB DEFAULT '{}',
    dependencies TEXT[] DEFAULT '{}',
    is_public BOOLEAN DEFAULT false,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Testing results for workflow validation
CREATE TABLE testing_results (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER REFERENCES nocode_workflows(id) ON DELETE CASCADE,
    test_type VARCHAR(50) NOT NULL CHECK (test_type IN ('unit', 'integration', 'backtest', 'validation')),
    test_status VARCHAR(20) DEFAULT 'pending' CHECK (test_status IN ('pending', 'running', 'passed', 'failed')),
    test_results JSONB DEFAULT '{}',
    error_details JSONB DEFAULT '[]',
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Marketplace strategies
CREATE TABLE marketplace_strategies (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER REFERENCES nocode_workflows(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) DEFAULT 0.00,
    category VARCHAR(50) NOT NULL,
    tags TEXT[] DEFAULT '{}',
    performance_metrics JSONB DEFAULT '{}',
    is_featured BOOLEAN DEFAULT false,
    is_approved BOOLEAN DEFAULT false,
    download_count INTEGER DEFAULT 0,
    rating DECIMAL(2,1) DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Strategy ratings and reviews
CREATE TABLE strategy_ratings (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER REFERENCES marketplace_strategies(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    review_text TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(strategy_id, user_id)
);

-- Workflow executions tracking
CREATE TABLE workflow_executions (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER REFERENCES nocode_workflows(id) ON DELETE CASCADE,
    execution_id INTEGER REFERENCES nocode_executions(id) ON DELETE CASCADE,
    execution_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Audit log for tracking changes
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER NOT NULL,
    action VARCHAR(20) NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_values JSONB,
    new_values JSONB,
    changed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    changed_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_nocode_workflows_user_id ON nocode_workflows(user_id);
CREATE INDEX idx_nocode_workflows_category ON nocode_workflows(category);
CREATE INDEX idx_nocode_workflows_public ON nocode_workflows(is_public) WHERE is_public = true;
CREATE INDEX idx_nocode_workflows_template ON nocode_workflows(is_template) WHERE is_template = true;
CREATE INDEX idx_nocode_workflows_status ON nocode_workflows(compilation_status, validation_status);
CREATE INDEX idx_nocode_workflows_updated_at ON nocode_workflows(updated_at);

CREATE INDEX idx_nocode_components_category ON nocode_components(category, subcategory);
CREATE INDEX idx_nocode_components_public ON nocode_components(is_public) WHERE is_public = true;
CREATE INDEX idx_nocode_components_builtin ON nocode_components(is_builtin) WHERE is_builtin = true;
CREATE INDEX idx_nocode_components_rating ON nocode_components(rating DESC);

CREATE INDEX idx_nocode_executions_workflow_id ON nocode_executions(workflow_id);
CREATE INDEX idx_nocode_executions_user_id ON nocode_executions(user_id);
CREATE INDEX idx_nocode_executions_status ON nocode_executions(status);
CREATE INDEX idx_nocode_executions_started_at ON nocode_executions(started_at);

CREATE INDEX idx_nocode_templates_category ON nocode_templates(category);
CREATE INDEX idx_nocode_templates_featured ON nocode_templates(is_featured) WHERE is_featured = true;
CREATE INDEX idx_nocode_templates_rating ON nocode_templates(rating DESC);

CREATE INDEX idx_nocode_analytics_workflow_id ON nocode_workflow_analytics(workflow_id);
CREATE INDEX idx_nocode_analytics_user_id ON nocode_workflow_analytics(user_id);
CREATE INDEX idx_nocode_analytics_event_type ON nocode_workflow_analytics(event_type);
CREATE INDEX idx_nocode_analytics_timestamp ON nocode_workflow_analytics(timestamp);

CREATE INDEX idx_nocode_data_sources_user_id ON nocode_data_sources(user_id);
CREATE INDEX idx_nocode_data_sources_type ON nocode_data_sources(type);
CREATE INDEX idx_nocode_data_sources_status ON nocode_data_sources(status);

CREATE INDEX idx_compilation_results_workflow_id ON compilation_results(workflow_id);
CREATE INDEX idx_compilation_results_status ON compilation_results(compilation_status);
CREATE INDEX idx_compilation_results_created_at ON compilation_results(created_at);

CREATE INDEX idx_training_jobs_workflow_id ON training_jobs(workflow_id);
CREATE INDEX idx_training_jobs_compilation_id ON training_jobs(compilation_id);
CREATE INDEX idx_training_jobs_status ON training_jobs(status);
CREATE INDEX idx_training_jobs_created_at ON training_jobs(created_at);

CREATE INDEX idx_datasets_type ON datasets(dataset_type);
CREATE INDEX idx_datasets_public ON datasets(is_public) WHERE is_public = true;
CREATE INDEX idx_datasets_created_by ON datasets(created_by);

CREATE INDEX idx_component_library_public ON component_library(is_public) WHERE is_public = true;
CREATE INDEX idx_component_library_created_by ON component_library(created_by);

CREATE INDEX idx_testing_results_workflow_id ON testing_results(workflow_id);
CREATE INDEX idx_testing_results_type ON testing_results(test_type);
CREATE INDEX idx_testing_results_status ON testing_results(test_status);

CREATE INDEX idx_marketplace_strategies_workflow_id ON marketplace_strategies(workflow_id);
CREATE INDEX idx_marketplace_strategies_category ON marketplace_strategies(category);
CREATE INDEX idx_marketplace_strategies_featured ON marketplace_strategies(is_featured) WHERE is_featured = true;
CREATE INDEX idx_marketplace_strategies_approved ON marketplace_strategies(is_approved) WHERE is_approved = true;
CREATE INDEX idx_marketplace_strategies_rating ON marketplace_strategies(rating DESC);

CREATE INDEX idx_strategy_ratings_strategy_id ON strategy_ratings(strategy_id);
CREATE INDEX idx_strategy_ratings_user_id ON strategy_ratings(user_id);

CREATE INDEX idx_workflow_executions_workflow_id ON workflow_executions(workflow_id);
CREATE INDEX idx_workflow_executions_execution_id ON workflow_executions(execution_id);

CREATE INDEX idx_audit_log_table_record ON audit_log(table_name, record_id);
CREATE INDEX idx_audit_log_changed_by ON audit_log(changed_by);
CREATE INDEX idx_audit_log_changed_at ON audit_log(changed_at);

-- Create triggers for updated_at timestamps
CREATE TRIGGER update_nocode_workflows_updated_at BEFORE UPDATE ON nocode_workflows FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_nocode_components_updated_at BEFORE UPDATE ON nocode_components FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_nocode_templates_updated_at BEFORE UPDATE ON nocode_templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_nocode_data_sources_updated_at BEFORE UPDATE ON nocode_data_sources FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_compilation_results_updated_at BEFORE UPDATE ON compilation_results FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_datasets_updated_at BEFORE UPDATE ON datasets FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_component_library_updated_at BEFORE UPDATE ON component_library FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_marketplace_strategies_updated_at BEFORE UPDATE ON marketplace_strategies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert built-in components
INSERT INTO nocode_components (name, display_name, description, category, component_type, input_schema, output_schema, parameters_schema, default_parameters, code_template, imports_required, ui_config, is_builtin, is_public) VALUES

-- Data Source Components
('market_data_input', 'Market Data Input', 'Fetches real-time or historical market data', 'data_source', 'input', 
'{}', 
'{"type": "object", "properties": {"data": {"type": "array"}}}',
'{"type": "object", "properties": {"symbol": {"type": "string", "default": "BTCUSDT"}, "timeframe": {"type": "string", "default": "1h"}}}',
'{"symbol": "BTCUSDT", "timeframe": "1h"}',
'def market_data_input(symbol, timeframe):\n    # Fetch market data\n    return get_market_data(symbol, timeframe)',
'["pandas", "ccxt"]',
'{"width": 180, "height": 80, "color": "#3b82f6"}',
true, true),

-- Technical Indicators
('sma_indicator', 'Simple Moving Average', 'Calculates Simple Moving Average', 'indicator', 'transform',
'{"type": "object", "properties": {"data": {"type": "array"}}}',
'{"type": "object", "properties": {"sma": {"type": "array"}}}',
'{"type": "object", "properties": {"period": {"type": "integer", "default": 20}}}',
'{"period": 20}',
'def sma_indicator(data, period):\n    return data.rolling(window=period).mean()',
'["pandas", "numpy"]',
'{"width": 160, "height": 80, "color": "#10b981"}',
true, true),

('rsi_indicator', 'RSI Indicator', 'Calculates Relative Strength Index', 'indicator', 'transform',
'{"type": "object", "properties": {"data": {"type": "array"}}}',
'{"type": "object", "properties": {"rsi": {"type": "array"}}}',
'{"type": "object", "properties": {"period": {"type": "integer", "default": 14}}}',
'{"period": 14}',
'def rsi_indicator(data, period):\n    delta = data.diff()\n    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()\n    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()\n    rs = gain / loss\n    return 100 - (100 / (1 + rs))',
'["pandas", "numpy"]',
'{"width": 160, "height": 80, "color": "#10b981"}',
true, true),

-- Condition Components
('price_condition', 'Price Condition', 'Checks price-based conditions', 'condition', 'condition',
'{"type": "object", "properties": {"price": {"type": "number"}, "indicator": {"type": "number"}}}',
'{"type": "object", "properties": {"signal": {"type": "boolean"}}}',
'{"type": "object", "properties": {"operator": {"type": "string", "default": ">"}, "threshold": {"type": "number", "default": 0}}}',
'{"operator": ">", "threshold": 0}',
'def price_condition(price, indicator, operator, threshold):\n    if operator == ">":\n        return price > indicator + threshold\n    elif operator == "<":\n        return price < indicator - threshold\n    return False',
'[]',
'{"width": 160, "height": 80, "color": "#f59e0b"}',
true, true),

-- Action Components
('buy_signal', 'Buy Signal', 'Generates buy signal', 'action', 'action',
'{"type": "object", "properties": {"condition": {"type": "boolean"}}}',
'{"type": "object", "properties": {"action": {"type": "string"}}}',
'{"type": "object", "properties": {"quantity": {"type": "number", "default": 100}}}',
'{"quantity": 100}',
'def buy_signal(condition, quantity):\n    if condition:\n        return {"action": "buy", "quantity": quantity}\n    return None',
'[]',
'{"width": 140, "height": 80, "color": "#22c55e"}',
true, true),

('sell_signal', 'Sell Signal', 'Generates sell signal', 'action', 'action',
'{"type": "object", "properties": {"condition": {"type": "boolean"}}}',
'{"type": "object", "properties": {"action": {"type": "string"}}}',
'{"type": "object", "properties": {"quantity": {"type": "number", "default": 100}}}',
'{"quantity": 100}',
'def sell_signal(condition, quantity):\n    if condition:\n        return {"action": "sell", "quantity": quantity}\n    return None',
'[]',
'{"width": 140, "height": 80, "color": "#ef4444"}',
true, true),

-- Risk Management
('stop_loss', 'Stop Loss', 'Implements stop loss logic', 'risk_management', 'risk',
'{"type": "object", "properties": {"current_price": {"type": "number"}, "entry_price": {"type": "number"}}}',
'{"type": "object", "properties": {"should_exit": {"type": "boolean"}}}',
'{"type": "object", "properties": {"percentage": {"type": "number", "default": 5}}}',
'{"percentage": 5}',
'def stop_loss(current_price, entry_price, percentage):\n    loss_threshold = entry_price * (1 - percentage / 100)\n    return current_price <= loss_threshold',
'[]',
'{"width": 160, "height": 80, "color": "#dc2626"}',
true, true),

-- Output Components
('portfolio_output', 'Portfolio Output', 'Outputs portfolio performance metrics', 'output', 'output',
'{"type": "object", "properties": {"trades": {"type": "array"}}}',
'{"type": "object", "properties": {"metrics": {"type": "object"}}}',
'{}',
'{}',
'def portfolio_output(trades):\n    total_return = sum(trade["pnl"] for trade in trades)\n    return {"total_return": total_return, "total_trades": len(trades)}',
'["pandas"]',
'{"width": 180, "height": 80, "color": "#6366f1"}',
true, true);

-- Insert sample templates
INSERT INTO nocode_templates (name, description, category, difficulty_level, template_data, is_featured) VALUES
('Simple SMA Crossover', 'Basic moving average crossover strategy for beginners', 'technical_analysis', 'beginner',
'{"nodes": [{"id": "1", "type": "market_data_input", "position": {"x": 100, "y": 100}}, {"id": "2", "type": "sma_indicator", "position": {"x": 300, "y": 50}}, {"id": "3", "type": "sma_indicator", "position": {"x": 300, "y": 150}}, {"id": "4", "type": "price_condition", "position": {"x": 500, "y": 100}}, {"id": "5", "type": "buy_signal", "position": {"x": 700, "y": 100}}], "edges": [{"id": "e1-2", "source": "1", "target": "2"}, {"id": "e1-3", "source": "1", "target": "3"}, {"id": "e2-4", "source": "2", "target": "4"}, {"id": "e3-4", "source": "3", "target": "4"}, {"id": "e4-5", "source": "4", "target": "5"}]}',
true),

('RSI Mean Reversion', 'RSI-based mean reversion strategy', 'technical_analysis', 'intermediate',
'{"nodes": [{"id": "1", "type": "market_data_input", "position": {"x": 100, "y": 100}}, {"id": "2", "type": "rsi_indicator", "position": {"x": 300, "y": 100}}, {"id": "3", "type": "price_condition", "position": {"x": 500, "y": 50}}, {"id": "4", "type": "price_condition", "position": {"x": 500, "y": 150}}, {"id": "5", "type": "buy_signal", "position": {"x": 700, "y": 50}}, {"id": "6", "type": "sell_signal", "position": {"x": 700, "y": 150}}], "edges": [{"id": "e1-2", "source": "1", "target": "2"}, {"id": "e2-3", "source": "2", "target": "3"}, {"id": "e2-4", "source": "2", "target": "4"}, {"id": "e3-5", "source": "3", "target": "5"}, {"id": "e4-6", "source": "4", "target": "6"}]}',
true);

COMMIT;