-- Customer Support Service Database Initialization
-- Creates all necessary tables and relationships for the customer support system

-- Create database schema if needed
CREATE SCHEMA IF NOT EXISTS public;

-- Support Agents Table
CREATE TABLE IF NOT EXISTS support_agents (
    agent_id VARCHAR(50) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    agent_level VARCHAR(20) DEFAULT 'L1' CHECK (agent_level IN ('L1', 'L2', 'L3_SPECIALIST', 'L4_MANAGER')),
    status VARCHAR(20) DEFAULT 'OFFLINE' CHECK (status IN ('AVAILABLE', 'BUSY', 'AWAY', 'OFFLINE')),
    department VARCHAR(50),
    max_concurrent_tickets INTEGER DEFAULT 10,
    current_ticket_count INTEGER DEFAULT 0,
    total_tickets_handled BIGINT DEFAULT 0,
    average_resolution_time_hours DOUBLE PRECISION DEFAULT 0.0,
    customer_satisfaction_rating DOUBLE PRECISION DEFAULT 0.0,
    languages VARCHAR(200),
    timezone VARCHAR(50),
    work_hours_start VARCHAR(10),
    work_hours_end VARCHAR(10),
    last_activity_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent Specializations Table (for SupportAgent entity @ElementCollection)
CREATE TABLE IF NOT EXISTS agent_specializations (
    agent_id VARCHAR(50) NOT NULL REFERENCES support_agents(agent_id) ON DELETE CASCADE,
    specialization VARCHAR(50) NOT NULL CHECK (specialization IN ('TECHNICAL', 'STRATEGY_DEVELOPMENT', 'LIVE_TRADING', 'PAPER_TRADING', 'BROKER_INTEGRATION', 'MODEL_TRAINING', 'BACKTESTING', 'ACCOUNT_BILLING', 'KYC_VERIFICATION', 'API_SDK', 'MARKETPLACE', 'SECURITY', 'DATA_PRIVACY', 'FEATURE_REQUEST', 'BUG_REPORT', 'GENERAL_INQUIRY', 'OTHER')),
    PRIMARY KEY (agent_id, specialization)
);

-- Support Tickets Table
CREATE TABLE IF NOT EXISTS support_tickets (
    ticket_id VARCHAR(20) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    user_email VARCHAR(255) NOT NULL,
    user_name VARCHAR(200),
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN ('TECHNICAL', 'STRATEGY_DEVELOPMENT', 'LIVE_TRADING', 'PAPER_TRADING', 'BROKER_INTEGRATION', 'MODEL_TRAINING', 'BACKTESTING', 'ACCOUNT_BILLING', 'KYC_VERIFICATION', 'API_SDK', 'MARKETPLACE', 'SECURITY', 'DATA_PRIVACY', 'FEATURE_REQUEST', 'BUG_REPORT', 'GENERAL_INQUIRY', 'OTHER')),
    priority VARCHAR(20) NOT NULL DEFAULT 'MEDIUM' CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'URGENT', 'CRITICAL')),
    status VARCHAR(20) NOT NULL DEFAULT 'NEW' CHECK (status IN ('NEW', 'ASSIGNED', 'IN_PROGRESS', 'PENDING_CUSTOMER', 'PENDING_INTERNAL', 'ESCALATED', 'RESOLVED', 'CLOSED', 'CANCELLED')),
    assigned_agent_id VARCHAR(255) REFERENCES support_agents(agent_id),
    assigned_agent_name VARCHAR(200),
    resolution TEXT,
    resolution_type VARCHAR(50),
    escalation_level INTEGER DEFAULT 0,
    escalation_reason TEXT,
    escalated_to VARCHAR(255) REFERENCES support_agents(agent_id),
    escalated_at TIMESTAMP,
    escalated_by VARCHAR(255),
    satisfaction_rating INTEGER CHECK (satisfaction_rating >= 1 AND satisfaction_rating <= 5),
    satisfaction_feedback TEXT,
    tags TEXT[],
    attachments TEXT[],
    source_channel VARCHAR(50) DEFAULT 'WEB' CHECK (source_channel IN ('WEB', 'EMAIL', 'CHAT', 'PHONE', 'API', 'MOBILE')),
    environment_info JSONB,
    browser_info JSONB,
    device_info JSONB,
    session_id VARCHAR(255),
    referrer_url TEXT,
    page_url TEXT,
    user_agent TEXT,
    ip_address INET,
    has_unread_messages BOOLEAN DEFAULT false,
    communication_count INTEGER DEFAULT 0,
    first_response_at TIMESTAMP,
    last_customer_message_at TIMESTAMP,
    last_agent_message_at TIMESTAMP,
    sla_due_date TIMESTAMP,
    is_sla_breached BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    closed_at TIMESTAMP,
    estimated_resolution_time TIMESTAMP,
    last_updated_by VARCHAR(255),
    created_by VARCHAR(255),
    updated_by VARCHAR(255)
);

-- Ticket Tags Table (for Ticket entity @ElementCollection)
CREATE TABLE IF NOT EXISTS ticket_tags (
    ticket_id VARCHAR(20) NOT NULL REFERENCES support_tickets(ticket_id) ON DELETE CASCADE,
    tag VARCHAR(255) NOT NULL,
    PRIMARY KEY (ticket_id, tag)
);

-- Communications Table (Messages within tickets)
CREATE TABLE IF NOT EXISTS communications (
    communication_id BIGSERIAL PRIMARY KEY,
    ticket_id VARCHAR(20) NOT NULL REFERENCES support_tickets(ticket_id) ON DELETE CASCADE,
    sender_id VARCHAR(255) NOT NULL,
    sender_type VARCHAR(20) NOT NULL CHECK (sender_type IN ('CUSTOMER', 'AGENT', 'SYSTEM')),
    content TEXT,
    communication_type VARCHAR(50) NOT NULL CHECK (communication_type IN ('MESSAGE', 'EMAIL', 'PHONE_LOG', 'VIDEO_CALL', 'SCREEN_SHARE', 'INTERNAL_NOTE', 'SYSTEM_LOG', 'FILE_UPLOAD', 'STATUS_UPDATE', 'ESCALATION', 'RESOLUTION')),
    is_internal BOOLEAN DEFAULT false,
    email_message_id VARCHAR(255),
    phone_call_duration INTEGER,
    video_call_recording_url TEXT,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ticket History/Audit Table
CREATE TABLE IF NOT EXISTS ticket_history (
    history_id SERIAL PRIMARY KEY,
    ticket_id VARCHAR(20) NOT NULL REFERENCES support_tickets(ticket_id) ON DELETE CASCADE,
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    change_type VARCHAR(50) NOT NULL CHECK (change_type IN ('CREATED', 'UPDATED', 'STATUS_CHANGED', 'ASSIGNED', 'ESCALATED', 'RESOLVED', 'CLOSED', 'COMMENTED')),
    changed_by VARCHAR(255) NOT NULL,
    changed_by_type VARCHAR(20) DEFAULT 'AGENT' CHECK (changed_by_type IN ('CUSTOMER', 'AGENT', 'SYSTEM')),
    change_reason TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Knowledge Base Articles Table
CREATE TABLE IF NOT EXISTS knowledge_base_articles (
    article_id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    tags TEXT[],
    difficulty_level VARCHAR(20) DEFAULT 'BEGINNER' CHECK (difficulty_level IN ('BEGINNER', 'INTERMEDIATE', 'ADVANCED')),
    target_audience VARCHAR(100) DEFAULT 'ALL' CHECK (target_audience IN ('ALL', 'CUSTOMERS', 'AGENTS', 'DEVELOPERS')),
    language VARCHAR(10) DEFAULT 'en',
    status VARCHAR(20) DEFAULT 'DRAFT' CHECK (status IN ('DRAFT', 'REVIEW', 'PUBLISHED', 'ARCHIVED')),
    author_id VARCHAR(255) NOT NULL,
    author_name VARCHAR(200),
    reviewer_id VARCHAR(255),
    reviewer_name VARCHAR(200),
    view_count INTEGER DEFAULT 0,
    helpful_count INTEGER DEFAULT 0,
    not_helpful_count INTEGER DEFAULT 0,
    last_reviewed_at TIMESTAMP,
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- FAQ Table
CREATE TABLE IF NOT EXISTS frequently_asked_questions (
    faq_id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    language VARCHAR(10) DEFAULT 'en',
    priority INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    helpful_count INTEGER DEFAULT 0,
    not_helpful_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Notifications Table
CREATE TABLE IF NOT EXISTS support_notifications (
    notification_id VARCHAR(255) PRIMARY KEY,
    recipient_type VARCHAR(20) NOT NULL CHECK (recipient_type IN ('CUSTOMER', 'AGENT', 'ADMIN')),
    recipient_id VARCHAR(255) NOT NULL,
    notification_type VARCHAR(50) NOT NULL CHECK (notification_type IN ('TICKET_CREATED', 'TICKET_ASSIGNED', 'TICKET_UPDATED', 'MESSAGE_RECEIVED', 'ESCALATION', 'SLA_WARNING', 'SATISFACTION_REQUEST')),
    title VARCHAR(500) NOT NULL,
    message TEXT NOT NULL,
    related_ticket_id VARCHAR(20) REFERENCES support_tickets(ticket_id),
    delivery_channel VARCHAR(20) DEFAULT 'IN_APP' CHECK (delivery_channel IN ('IN_APP', 'EMAIL', 'SMS', 'PUSH')),
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMP,
    delivery_status VARCHAR(20) DEFAULT 'PENDING' CHECK (delivery_status IN ('PENDING', 'SENT', 'DELIVERED', 'FAILED', 'BOUNCE')),
    delivered_at TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SLA Policies Table
CREATE TABLE IF NOT EXISTS sla_policies (
    sla_id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    priority VARCHAR(20) NOT NULL CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'URGENT', 'CRITICAL')),
    category VARCHAR(50),
    first_response_minutes INTEGER NOT NULL,
    resolution_hours INTEGER NOT NULL,
    escalation_hours INTEGER,
    business_hours_only BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default SLA policies
INSERT INTO sla_policies (name, description, priority, first_response_minutes, resolution_hours, escalation_hours) VALUES
('Critical Issues', 'Critical system outages and security issues', 'CRITICAL', 15, 4, 2),
('Urgent Issues', 'High impact issues affecting multiple users', 'URGENT', 30, 8, 4),
('High Priority', 'Important issues affecting business operations', 'HIGH', 60, 24, 12),
('Medium Priority', 'Standard support requests and questions', 'MEDIUM', 240, 72, 48),
('Low Priority', 'General inquiries and feature requests', 'LOW', 480, 168, 120)
ON CONFLICT DO NOTHING;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_support_tickets_user_id ON support_tickets(user_id);
CREATE INDEX IF NOT EXISTS idx_support_tickets_assigned_agent_id ON support_tickets(assigned_agent_id);
CREATE INDEX IF NOT EXISTS idx_support_tickets_status ON support_tickets(status);
CREATE INDEX IF NOT EXISTS idx_support_tickets_priority ON support_tickets(priority);
CREATE INDEX IF NOT EXISTS idx_support_tickets_category ON support_tickets(category);
CREATE INDEX IF NOT EXISTS idx_support_tickets_created_at ON support_tickets(created_at);
CREATE INDEX IF NOT EXISTS idx_support_tickets_updated_at ON support_tickets(updated_at);
CREATE INDEX IF NOT EXISTS idx_support_tickets_sla_due_date ON support_tickets(sla_due_date);
CREATE INDEX IF NOT EXISTS idx_communications_ticket_id ON communications(ticket_id);
CREATE INDEX IF NOT EXISTS idx_communications_created_at ON communications(created_at);
CREATE INDEX IF NOT EXISTS idx_ticket_tags_ticket_id ON ticket_tags(ticket_id);
CREATE INDEX IF NOT EXISTS idx_ticket_history_ticket_id ON ticket_history(ticket_id);
CREATE INDEX IF NOT EXISTS idx_ticket_history_created_at ON ticket_history(created_at);
CREATE INDEX IF NOT EXISTS idx_support_agents_status ON support_agents(status);
CREATE INDEX IF NOT EXISTS idx_support_agents_agent_level ON support_agents(agent_level);
CREATE INDEX IF NOT EXISTS idx_agent_specializations_agent_id ON agent_specializations(agent_id);
CREATE INDEX IF NOT EXISTS idx_kb_articles_category ON knowledge_base_articles(category);
CREATE INDEX IF NOT EXISTS idx_kb_articles_status ON knowledge_base_articles(status);
CREATE INDEX IF NOT EXISTS idx_faq_category ON frequently_asked_questions(category);
CREATE INDEX IF NOT EXISTS idx_notifications_recipient ON support_notifications(recipient_type, recipient_id);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON support_notifications(notification_type);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON support_notifications(created_at);

-- Create some default support agents for development
INSERT INTO support_agents (agent_id, username, first_name, last_name, email, department, agent_level, status, max_concurrent_tickets, languages) VALUES
('dev-agent-001', 'dev_agent', 'Development', 'Agent', 'dev@alphintra.com', 'Support', 'L2', 'AVAILABLE', 15, 'english'),
('admin-agent-001', 'admin_agent', 'Admin', 'Agent', 'admin@alphintra.com', 'Support', 'L4_MANAGER', 'AVAILABLE', 20, 'english'),
('l1-agent-001', 'l1_agent', 'Level1', 'Agent', 'l1@alphintra.com', 'Support', 'L1', 'AVAILABLE', 10, 'english')
ON CONFLICT (agent_id) DO NOTHING;

-- Insert default specializations for agents
INSERT INTO agent_specializations (agent_id, specialization) VALUES
('dev-agent-001', 'TECHNICAL'),
('dev-agent-001', 'ACCOUNT_BILLING'),
('dev-agent-001', 'BUG_REPORT'),
('admin-agent-001', 'ACCOUNT_BILLING'),
('admin-agent-001', 'TECHNICAL'),
('admin-agent-001', 'FEATURE_REQUEST'),
('l1-agent-001', 'GENERAL_INQUIRY'),
('l1-agent-001', 'ACCOUNT_BILLING')
ON CONFLICT (agent_id, specialization) DO NOTHING;

-- Update triggers for timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_support_tickets_updated_at BEFORE UPDATE ON support_tickets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_support_agents_updated_at BEFORE UPDATE ON support_agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_communications_updated_at BEFORE UPDATE ON communications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_kb_articles_updated_at BEFORE UPDATE ON knowledge_base_articles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_faq_updated_at BEFORE UPDATE ON frequently_asked_questions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sla_policies_updated_at BEFORE UPDATE ON sla_policies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
