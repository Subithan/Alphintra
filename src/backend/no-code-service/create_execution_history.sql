-- Create execution_history table for database-only storage
-- This table stores copies of generated strategy code and execution details

CREATE TABLE IF NOT EXISTS execution_history (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,
    workflow_id INTEGER NOT NULL,
    execution_mode VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    execution_config JSONB DEFAULT '{}',
    results JSONB DEFAULT '{}',
    error_logs JSONB DEFAULT '[]',
    
    -- Store generated strategy details
    generated_code TEXT,
    generated_requirements TEXT[],
    compilation_stats JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Add foreign key constraint if nocode_workflows table exists
    CONSTRAINT fk_execution_workflow 
        FOREIGN KEY (workflow_id) 
        REFERENCES nocode_workflows(id)
        ON DELETE CASCADE
);

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_execution_history_uuid ON execution_history(uuid);
CREATE INDEX IF NOT EXISTS idx_execution_history_workflow ON execution_history(workflow_id);
CREATE INDEX IF NOT EXISTS idx_execution_history_mode ON execution_history(execution_mode);
CREATE INDEX IF NOT EXISTS idx_execution_history_status ON execution_history(status);
CREATE INDEX IF NOT EXISTS idx_execution_history_created ON execution_history(created_at);

-- Add comment
COMMENT ON TABLE execution_history IS 'Stores execution history and copies of generated strategy code';
COMMENT ON COLUMN execution_history.generated_code IS 'Copy of generated strategy code for backup/audit';
COMMENT ON COLUMN execution_history.compilation_stats IS 'Statistics from Enhanced Compiler';

GRANT SELECT, INSERT, UPDATE, DELETE ON execution_history TO nocode_service;
GRANT USAGE ON SEQUENCE execution_history_id_seq TO nocode_service;