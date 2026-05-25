-- TechCorp Database Schema
-- Last Updated: March 2026

-- Users Table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    company_id INTEGER NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Companies Table
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    website VARCHAR(255),
    employee_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Instances Table
CREATE TABLE instances (
    id SERIAL PRIMARY KEY,
    instance_id VARCHAR(50) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    instance_type VARCHAR(50),
    region VARCHAR(50),
    status VARCHAR(20),
    cpu_count INTEGER,
    memory_gb INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Databases Table
CREATE TABLE databases (
    id SERIAL PRIMARY KEY,
    database_id VARCHAR(50) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    engine VARCHAR(50),
    version VARCHAR(20),
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Billing Table
CREATE TABLE billing (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL,
    billing_period DATE,
    total_amount DECIMAL(12, 2),
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- Create Indexes
CREATE INDEX idx_users_company ON users(company_id);
CREATE INDEX idx_instances_user ON instances(user_id);
CREATE INDEX idx_databases_user ON databases(user_id);
CREATE INDEX idx_billing_company ON billing(company_id);
