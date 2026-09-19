PRAGMA foreign_keys = ON;

CREATE TABLE marketplaces (
  code TEXT PRIMARY KEY,
  name_ko TEXT NOT NULL,
  base_url TEXT NOT NULL
);

CREATE TABLE products (
  id TEXT PRIMARY KEY,
  brand TEXT NOT NULL,
  model TEXT NOT NULL,
  variant TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  UNIQUE (brand, model, variant)
);

CREATE TABLE sellers (
  id TEXT PRIMARY KEY,
  marketplace_code TEXT NOT NULL REFERENCES marketplaces(code),
  external_seller_id TEXT,
  display_name TEXT,
  created_at TEXT NOT NULL,
  UNIQUE (marketplace_code, external_seller_id)
);

CREATE TABLE listings (
  id TEXT PRIMARY KEY,
  marketplace_code TEXT NOT NULL REFERENCES marketplaces(code),
  external_listing_id TEXT NOT NULL,
  product_id TEXT NOT NULL REFERENCES products(id),
  seller_id TEXT REFERENCES sellers(id),
  listing_url TEXT NOT NULL UNIQUE,
  listed_at TEXT,
  updated_at TEXT,
  sold_at TEXT,
  fetched_at TEXT NOT NULL,
  is_comparable INTEGER NOT NULL DEFAULT 1 CHECK (is_comparable IN (0, 1)),
  exclusion_reason TEXT,
  raw_json TEXT,
  UNIQUE (marketplace_code, external_listing_id)
);

CREATE TABLE listing_observations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  listing_id TEXT NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
  observed_at TEXT NOT NULL,
  title TEXT NOT NULL,
  price_krw INTEGER NOT NULL CHECK (price_krw >= 0),
  state TEXT NOT NULL CHECK (state IN ('active', 'sold', 'removed', 'unknown')),
  raw_json TEXT,
  UNIQUE (listing_id, observed_at)
);

CREATE TABLE seller_safety_checks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  seller_id TEXT NOT NULL REFERENCES sellers(id) ON DELETE CASCADE,
  checked_at TEXT NOT NULL,
  verification_status TEXT NOT NULL CHECK (verification_status IN ('verified', 'unavailable')),
  safe_trade_count INTEGER CHECK (safe_trade_count IS NULL OR safe_trade_count >= 0),
  source_url TEXT,
  raw_json TEXT,
  CHECK (
    (verification_status = 'verified' AND safe_trade_count IS NOT NULL)
    OR (verification_status = 'unavailable' AND safe_trade_count IS NULL)
  ),
  UNIQUE (seller_id, checked_at)
);

CREATE TABLE pricing_runs (
  id TEXT PRIMARY KEY,
  as_of TEXT NOT NULL,
  ruleset_id TEXT NOT NULL,
  current_listing_max_age_days INTEGER NOT NULL CHECK (current_listing_max_age_days > 0),
  source_kind TEXT NOT NULL CHECK (source_kind IN ('legacy_snapshot', 'normalized_listings')),
  source_ref TEXT,
  rules_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE price_guide_rows (
  pricing_run_id TEXT NOT NULL REFERENCES pricing_runs(id) ON DELETE CASCADE,
  product_id TEXT NOT NULL REFERENCES products(id),
  current_listing_id TEXT REFERENCES listings(id),
  current_price_krw INTEGER,
  current_url TEXT,
  safe_listing_id TEXT REFERENCES listings(id),
  safe_price_krw INTEGER,
  safe_url TEXT,
  low6_listing_id TEXT REFERENCES listings(id),
  low6_price_krw INTEGER,
  low6_url TEXT,
  avg3_price_krw INTEGER,
  avg3_sample_size INTEGER NOT NULL DEFAULT 0 CHECK (avg3_sample_size >= 0),
  safety_label TEXT NOT NULL,
  note TEXT NOT NULL DEFAULT '',
  sort_order INTEGER NOT NULL,
  PRIMARY KEY (pricing_run_id, product_id)
);

CREATE INDEX idx_listings_product ON listings(product_id);
CREATE INDEX idx_listings_seller ON listings(seller_id);
CREATE INDEX idx_listings_freshness ON listings(updated_at, listed_at);
CREATE INDEX idx_observations_latest ON listing_observations(listing_id, observed_at DESC);
CREATE INDEX idx_safety_latest ON seller_safety_checks(seller_id, checked_at DESC);
CREATE INDEX idx_guide_rows_order ON price_guide_rows(pricing_run_id, sort_order);
