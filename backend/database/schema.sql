-- NextGen ERP: Specialty Chemical Research Database
-- Created: May 8, 2026
-- Purpose: Store company research data, pain signals, and contact information

-- Table 1: Companies
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    country VARCHAR(100),
    website VARCHAR(255),
    industry VARCHAR(100),
    employees INT,
    revenue_estimate VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 2: Pain Signals (evidence of problems)
CREATE TABLE IF NOT EXISTS pain_signals (
    id SERIAL PRIMARY KEY,
    company_id INT REFERENCES companies(id),
    pain_type VARCHAR(100), -- 'segregation_violation', 'inventory_issue', 'demand_planning', etc.
    signal_text TEXT,
    evidence_source VARCHAR(100), -- 'OSHA', 'LinkedIn', 'Earnings', 'Forum', etc.
    signal_date DATE,
    urgency_score INT, -- 1-10, 10 = most urgent
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 3: Decision Makers (contacts at companies)
CREATE TABLE IF NOT EXISTS decision_makers (
    id SERIAL PRIMARY KEY,
    company_id INT REFERENCES companies(id),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    title VARCHAR(100), -- 'Plant Manager', 'Operations Director', etc.
    email VARCHAR(255),
    phone VARCHAR(20),
    linkedin_url VARCHAR(255),
    contacted BOOLEAN DEFAULT FALSE,
    contact_date DATE,
    response_status VARCHAR(50), -- 'interested', 'not_interested', 'pending', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 4: Research Notes
CREATE TABLE IF NOT EXISTS research_notes (
    id SERIAL PRIMARY KEY,
    company_id INT REFERENCES companies(id),
    note_text TEXT,
    researcher VARCHAR(100),
    note_type VARCHAR(50), -- 'finding', 'analysis', 'strategy', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 5: AI Insights (for recommendations)
CREATE TABLE IF NOT EXISTS ai_insights (
    id SERIAL PRIMARY KEY,
    company_id INT REFERENCES companies(id),
    insight_type VARCHAR(100), -- 'segregation_risk', 'inventory_optimization', etc.
    insight_text TEXT,
    confidence_score DECIMAL(3, 2), -- 0.0 to 1.0
    recommended_action TEXT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for faster queries
CREATE INDEX idx_companies_country ON companies(country);
CREATE INDEX idx_pain_signals_urgency ON pain_signals(urgency_score DESC);
CREATE INDEX idx_decision_makers_company ON decision_makers(company_id);
CREATE INDEX idx_pain_signals_company ON pain_signals(company_id);
