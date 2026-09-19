CREATE TABLE ingestion_runs (
  id TEXT PRIMARY KEY,
  fetched_at TEXT NOT NULL,
  source_ref TEXT,
  payload_sha256 TEXT NOT NULL,
  imported_at TEXT NOT NULL
);

ALTER TABLE listing_observations
ADD COLUMN ingestion_run_id TEXT REFERENCES ingestion_runs(id);

ALTER TABLE seller_safety_checks
ADD COLUMN ingestion_run_id TEXT REFERENCES ingestion_runs(id);

CREATE INDEX idx_observations_ingestion_run
ON listing_observations(ingestion_run_id);

CREATE INDEX idx_safety_ingestion_run
ON seller_safety_checks(ingestion_run_id);
