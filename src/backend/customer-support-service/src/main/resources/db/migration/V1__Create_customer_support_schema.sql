-- Customer Support Service Database Schema
-- This script creates the initial schema for the customer support system

-- Create the customer support database if it doesn't exist (handled by Spring Boot)
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create support agents table
CREATE TABLE support_agents (
    agent_id VARCHAR(50) PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    agent_level VARCHAR(20) NOT NULL CHECK (agent_level IN ('L1', 'L2', 'L3_SPECIALIST', 'L4_MANAGER')),
    status VARCHAR(20) NOT NULL CHECK (status IN ('AVAILABLE', 'BUSY', 'AWAY', 'BREAK', 'OFFLINE')),
    department VARCHAR(50),
    max_concurrent_tickets INTEGER DEFAULT 5,
    current_ticket_count INTEGER DEFAULT 0,
    total_tickets_handled BIGINT DEFAULT 0,
    average_resolution_time_hours DECIMAL(5,2),
    customer_satisfaction_rating DECIMAL(3,2),
    languages VARCHAR(200),
    timezone VARCHAR(50),
    work_hours_start VARCHAR(5), -- HH:mm format
    work_hours_end VARCHAR(5),   -- HH:mm format
    last_activity_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT true
);

-- Create agent specializations table
CREATE TABLE agent_specializations (
    agent_id VARCHAR(50) NOT NULL,
    specialization VARCHAR(50) NOT NULL CHECK (specialization IN (
        'TECHNICAL', 'STRATEGY_DEVELOPMENT', 'LIVE_TRADING', 'PAPER_TRADING',
        'BROKER_INTEGRATION', 'MODEL_TRAINING', 'BACKTESTING', 'ACCOUNT_BILLING',
        'KYC_VERIFICATION', 'API_SDK', 'MARKETPLACE', 'SECURITY', 'DATA_PRIVACY',
        'FEATURE_REQUEST', 'BUG_REPORT', 'GENERAL_INQUIRY', 'OTHER'
    )),
    PRIMARY KEY (agent_id, specialization),
    FOREIGN KEY (agent_id) REFERENCES support_agents(agent_id) ON DELETE CASCADE
);

-- Create support tickets table
CREATE TABLE support_tickets (
    ticket_id VARCHAR(20) PRIMARY KEY,
    user_id UUID NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL CHECK (category IN (
        'TECHNICAL', 'STRATEGY_DEVELOPMENT', 'LIVE_TRADING', 'PAPER_TRADING',
        'BROKER_INTEGRATION', 'MODEL_TRAINING', 'BACKTESTING', 'ACCOUNT_BILLING',
        'KYC_VERIFICATION', 'API_SDK', 'MARKETPLACE', 'SECURITY', 'DATA_PRIVACY',
        'FEATURE_REQUEST', 'BUG_REPORT', 'GENERAL_INQUIRY', 'OTHER'
    )),
    priority VARCHAR(20) NOT NULL CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'URGENT', 'CRITICAL')),
    status VARCHAR(20) NOT NULL CHECK (status IN (
        'NEW', 'ASSIGNED', 'IN_PROGRESS', 'PENDING_USER', 'PENDING_INTERNAL',
        'ESCALATED', 'RESOLVED', 'CLOSED', 'REOPENED'
    )),
    assigned_agent_id VARCHAR(50),
    escalation_level INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    last_updated_by VARCHAR(50),
    estimated_resolution_time TIMESTAMP,
    satisfaction_rating INTEGER CHECK (satisfaction_rating >= 1 AND satisfaction_rating <= 5),
    satisfaction_feedback TEXT,
    FOREIGN KEY (assigned_agent_id) REFERENCES support_agents(agent_id)
);

-- Create ticket tags table
CREATE TABLE ticket_tags (
    ticket_id VARCHAR(20) NOT NULL,
    tag VARCHAR(50) NOT NULL,
    PRIMARY KEY (ticket_id, tag),
    FOREIGN KEY (ticket_id) REFERENCES support_tickets(ticket_id) ON DELETE CASCADE
);

-- Create communications table
CREATE TABLE communications (
    communication_id BIGSERIAL PRIMARY KEY,
    ticket_id VARCHAR(20) NOT NULL,
    sender_id VARCHAR(50) NOT NULL,
    sender_type VARCHAR(20) NOT NULL CHECK (sender_type IN ('USER', 'AGENT', 'SYSTEM')),
    content TEXT,
    communication_type VARCHAR(20) NOT NULL CHECK (communication_type IN (
        'MESSAGE', 'EMAIL', 'PHONE_LOG', 'VIDEO_CALL', 'SCREEN_SHARE',
        'INTERNAL_NOTE', 'SYSTEM_LOG', 'FILE_UPLOAD', 'STATUS_UPDATE',
        'ESCALATION', 'RESOLUTION'
    )),
    is_internal BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP,
    email_message_id VARCHAR(100),
    phone_call_duration INTEGER, -- in seconds
    video_call_recording_url TEXT,
    FOREIGN KEY (ticket_id) REFERENCES support_tickets(ticket_id) ON DELETE CASCADE
);

-- Create communication attachments table
CREATE TABLE communication_attachments (
    communication_id BIGINT NOT NULL,
    attachment_url TEXT NOT NULL,
    PRIMARY KEY (communication_id, attachment_url),
    FOREIGN KEY (communication_id) REFERENCES communications(communication_id) ON DELETE CASCADE
);

-- Create knowledge base articles table
CREATE TABLE knowledge_base_articles (
    article_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    difficulty VARCHAR(20) NOT NULL CHECK (difficulty IN ('BEGINNER', 'INTERMEDIATE', 'EXPERT')),
    user_type VARCHAR(20) NOT NULL CHECK (user_type IN ('TRADER', 'DEVELOPER', 'ADMIN', 'ALL')),
    author_id VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT' CHECK (status IN ('DRAFT', 'PUBLISHED', 'ARCHIVED')),
    view_count BIGINT DEFAULT 0,
    helpful_count BIGINT DEFAULT 0,
    not_helpful_count BIGINT DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP,
    FOREIGN KEY (author_id) REFERENCES support_agents(agent_id)
);

-- Create knowledge base tags table
CREATE TABLE kb_article_tags (
    article_id UUID NOT NULL,
    tag VARCHAR(50) NOT NULL,
    PRIMARY KEY (article_id, tag),
    FOREIGN KEY (article_id) REFERENCES knowledge_base_articles(article_id) ON DELETE CASCADE
);

-- Create audit logs table
CREATE TABLE audit_logs (
    log_id BIGSERIAL PRIMARY KEY,
    agent_id VARCHAR(50) NOT NULL,
    user_id UUID,
    action_type VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(100),
    data_accessed TEXT, -- JSON array of accessed fields
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(100),
    FOREIGN KEY (agent_id) REFERENCES support_agents(agent_id)
);

-- Create user consent records table
CREATE TABLE user_consent_records (
    consent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    agent_id VARCHAR(50) NOT NULL,
    consent_type VARCHAR(50) NOT NULL,
    reason TEXT NOT NULL,
    data_requested TEXT, -- JSON array of requested data
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'GRANTED', 'DENIED', 'EXPIRED')),
    granted_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES support_agents(agent_id)
);

-- Create indexes for better performance
CREATE INDEX idx_tickets_status_created ON support_tickets(status, created_at DESC);
CREATE INDEX idx_tickets_assigned_agent ON support_tickets(assigned_agent_id, status);
CREATE INDEX idx_tickets_user_id ON support_tickets(user_id);
CREATE INDEX idx_tickets_category ON support_tickets(category);
CREATE INDEX idx_tickets_priority ON support_tickets(priority);

CREATE INDEX idx_communications_ticket_created ON communications(ticket_id, created_at DESC);
CREATE INDEX idx_communications_sender ON communications(sender_id);
CREATE INDEX idx_communications_type ON communications(communication_type);

CREATE INDEX idx_agents_level ON support_agents(agent_level);
CREATE INDEX idx_agents_status ON support_agents(status);
CREATE INDEX idx_agents_department ON support_agents(department);

CREATE INDEX idx_kb_articles_category ON knowledge_base_articles(category);
CREATE INDEX idx_kb_articles_status ON knowledge_base_articles(status);
CREATE INDEX idx_kb_articles_user_type ON knowledge_base_articles(user_type);

CREATE INDEX idx_audit_logs_agent_time ON audit_logs(agent_id, created_at DESC);
CREATE INDEX idx_audit_logs_user_time ON audit_logs(user_id, created_at DESC);

CREATE INDEX idx_consent_records_user ON user_consent_records(user_id);
CREATE INDEX idx_consent_records_agent ON user_consent_records(agent_id);
CREATE INDEX idx_consent_records_status ON user_consent_records(status);

-- Insert default support agents
INSERT INTO support_agents (
    agent_id, username, email, first_name, last_name, agent_level, 
    status, department, max_concurrent_tickets
) VALUES 
    ('agent-001', 'admin', 'admin@alphintra.com', 'Support', 'Administrator', 'L4_MANAGER', 'OFFLINE', 'Management', 10),
    ('agent-002', 'l1-agent', 'l1@alphintra.com', 'Level 1', 'Agent', 'L1', 'OFFLINE', 'General Support', 5),
    ('agent-003', 'l2-agent', 'l2@alphintra.com', 'Level 2', 'Agent', 'L2', 'OFFLINE', 'Technical Support', 8),
    ('agent-004', 'specialist', 'specialist@alphintra.com', 'Trading', 'Specialist', 'L3_SPECIALIST', 'OFFLINE', 'Trading Support', 6);

-- Insert specializations for agents
INSERT INTO agent_specializations (agent_id, specialization) VALUES
    ('agent-002', 'GENERAL_INQUIRY'),
    ('agent-002', 'ACCOUNT_BILLING'),
    ('agent-002', 'KYC_VERIFICATION'),
    ('agent-003', 'TECHNICAL'),
    ('agent-003', 'API_SDK'),
    ('agent-003', 'BUG_REPORT'),
    ('agent-004', 'STRATEGY_DEVELOPMENT'),
    ('agent-004', 'LIVE_TRADING'),
    ('agent-004', 'MODEL_TRAINING'),
    ('agent-004', 'BACKTESTING');

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic updated_at updates
CREATE TRIGGER update_support_agents_updated_at 
    BEFORE UPDATE ON support_agents 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_support_tickets_updated_at 
    BEFORE UPDATE ON support_tickets 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_knowledge_base_articles_updated_at 
    BEFORE UPDATE ON knowledge_base_articles 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();