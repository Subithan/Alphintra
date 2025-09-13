-- Add new columns for database-only storage
-- Run this against your PostgreSQL database

-- Add code metrics columns to nocode_workflows table
ALTER TABLE nocode_workflows 
ADD COLUMN IF NOT EXISTS generated_code_size INTEGER DEFAULT 0;

ALTER TABLE nocode_workflows 
ADD COLUMN IF NOT EXISTS generated_code_lines INTEGER DEFAULT 0;

ALTER TABLE nocode_workflows 
ADD COLUMN IF NOT EXISTS compiler_version VARCHAR(50) DEFAULT 'Enhanced v2.0';

-- Add comments for documentation
COMMENT ON COLUMN nocode_workflows.generated_code_size IS 'Size of generated code in bytes';
COMMENT ON COLUMN nocode_workflows.generated_code_lines IS 'Number of lines in generated code';
COMMENT ON COLUMN nocode_workflows.compiler_version IS 'Version of compiler used to generate code';

-- Verify the columns were added
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'nocode_workflows' 
AND column_name IN ('generated_code_size', 'generated_code_lines', 'compiler_version')
ORDER BY column_name;