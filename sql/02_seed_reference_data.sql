-- 02_seed_reference_data.sql
INSERT INTO data_sources (source_name, refresh_cadence)
VALUES ('Financial Modeling Prep', 'daily')
ON CONFLICT (source_name) DO NOTHING;

INSERT INTO companies (ticker, legal_name, currency)
VALUES ('RPD', 'Rapid7, Inc.', 'USD')
ON CONFLICT (ticker) DO NOTHING;

-- simple FY periods for 2020‑2024
INSERT INTO periods (period_id, fy)
VALUES (2020,2020),(2021,2021),(2022,2022),(2023,2023),(2024,2024)
ON CONFLICT (period_id) DO NOTHING;

-- minimal metric dictionary (extend as needed)
INSERT INTO metric_dictionary (metric_code, description, statement_section, is_ratio, preferred_unit)
VALUES
  ('sales','Total revenue','income',false,'USD'),
  ('ebit','EBIT (operating income)','income',false,'USD'),
  ('ebitda','Adjusted EBITDA','income',false,'USD'),
  ('ev_ebitda','Enterprise value / EBITDA','ratios',true,'x'),
  ('ev_sales','Enterprise value / Sales','ratios',true,'x'),
  ('price_earnings','Price / Earnings','ratios',true,'x')
ON CONFLICT (metric_code) DO NOTHING;
