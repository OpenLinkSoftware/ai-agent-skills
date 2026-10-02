-- Atlan Context & Chaos demo — DB.kidehen (Virtuoso)
-- No COMMENT ON (unsupported). Drop manually if reloading.

DROP TABLE DB.kidehen.cc_opportunity;
DROP TABLE DB.kidehen.cc_claim;
DROP TABLE DB.kidehen.cc_relationship;
DROP TABLE DB.kidehen.cc_property;
DROP TABLE DB.kidehen.cc_metric;
DROP TABLE DB.kidehen.cc_entity_alt_label;
DROP TABLE DB.kidehen.cc_entity;
DROP TABLE DB.kidehen.cc_source;

CREATE TABLE DB.kidehen.cc_source (
  source_id INTEGER NOT NULL PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  system_type VARCHAR(64) NOT NULL,
  description VARCHAR(512)
);

CREATE TABLE DB.kidehen.cc_entity (
  entity_id INTEGER NOT NULL PRIMARY KEY,
  preferred_label VARCHAR(128) NOT NULL,
  description VARCHAR(512)
);

CREATE TABLE DB.kidehen.cc_entity_alt_label (
  entity_id INTEGER NOT NULL,
  alt_label VARCHAR(128) NOT NULL,
  PRIMARY KEY (entity_id, alt_label)
);

CREATE TABLE DB.kidehen.cc_metric (
  metric_id INTEGER NOT NULL PRIMARY KEY,
  entity_id INTEGER NOT NULL,
  preferred_label VARCHAR(128) NOT NULL,
  description VARCHAR(512)
);

CREATE TABLE DB.kidehen.cc_property (
  property_id INTEGER NOT NULL PRIMARY KEY,
  entity_id INTEGER NOT NULL,
  preferred_label VARCHAR(128) NOT NULL,
  description VARCHAR(512)
);

CREATE TABLE DB.kidehen.cc_relationship (
  rel_id INTEGER NOT NULL PRIMARY KEY,
  from_entity_id INTEGER NOT NULL,
  to_entity_id INTEGER NOT NULL,
  preferred_label VARCHAR(128) NOT NULL
);

CREATE TABLE DB.kidehen.cc_claim (
  claim_id INTEGER NOT NULL PRIMARY KEY,
  claim_kind VARCHAR(32) NOT NULL,
  subject_ref VARCHAR(64) NOT NULL,
  definition_text VARCHAR(1024) NOT NULL,
  source_id INTEGER NOT NULL,
  confidence NUMERIC(5,4) NOT NULL,
  valid_from DATE NOT NULL,
  valid_to DATE,
  status VARCHAR(32) NOT NULL,
  reviewed_by VARCHAR(128),
  reviewed_at DATETIME
);

CREATE TABLE DB.kidehen.cc_opportunity (
  opp_id INTEGER NOT NULL PRIMARY KEY,
  account_name VARCHAR(128) NOT NULL,
  stage VARCHAR(64) NOT NULL,
  amount NUMERIC(12,2) NOT NULL,
  created_at DATE NOT NULL,
  closed_at DATE,
  is_new_business INTEGER NOT NULL,
  reached_qualification INTEGER NOT NULL
);

CREATE INDEX cc_claim_subject ON DB.kidehen.cc_claim (subject_ref);
CREATE INDEX cc_claim_valid ON DB.kidehen.cc_claim (valid_from, valid_to);
