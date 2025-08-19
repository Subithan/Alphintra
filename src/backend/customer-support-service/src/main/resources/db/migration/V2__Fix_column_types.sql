-- Fix column types for Hibernate compatibility
-- Change DECIMAL columns to DOUBLE PRECISION to match JPA entity types

ALTER TABLE support_agents 
    ALTER COLUMN average_resolution_time_hours TYPE DOUBLE PRECISION,
    ALTER COLUMN customer_satisfaction_rating TYPE DOUBLE PRECISION;