-- 01_schema.sql
-- core tables for financial metrics store
CREATE TABLE IF NOT EXISTS companies (
    company_id      SERIAL PRIMARY KEY,
    ticker          VARCHAR(10) UNIQUE NOT NULL,
    legal_name      TEXT,
    currency        CHAR(3),
    created_at      TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS metric_dictionary (
    metric_code     VARCHAR(40) PRIMARY KEY,
    description     TEXT,
    statement_section VARCHAR(20),
    is_ratio        BOOLEAN DEFAULT false,
    preferred_unit  VARCHAR(8)
);

CREATE TABLE IF NOT EXISTS data_sources (
    source_id       SERIAL PRIMARY KEY,
    source_name     TEXT UNIQUE,
    refresh_cadence TEXT
);

-- simple periods dim (FY only for now)
CREATE TABLE IF NOT EXISTS periods (
    period_id   INT PRIMARY KEY,
    fy          INT UNIQUE
);

CREATE TABLE IF NOT EXISTS financial_metrics (
    metric_id       BIGSERIAL PRIMARY KEY,
    period_id       INT REFERENCES periods(period_id),
    source_id       INT REFERENCES data_sources(source_id),
    company_id      INT REFERENCES companies(company_id),
    metric_code     VARCHAR(40) REFERENCES metric_dictionary(metric_code),
    value_numeric   NUMERIC(20,4),
    value_int       BIGINT,
    unit            VARCHAR(8),
    collected_at    TIMESTAMPTZ DEFAULT now(),
    UNIQUE(period_id, source_id, company_id, metric_code)
);
