DELETE FROM DB.kidehen.cc_opportunity;
DELETE FROM DB.kidehen.cc_claim;
DELETE FROM DB.kidehen.cc_relationship;
DELETE FROM DB.kidehen.cc_property;
DELETE FROM DB.kidehen.cc_metric;
DELETE FROM DB.kidehen.cc_entity_alt_label;
DELETE FROM DB.kidehen.cc_entity;
DELETE FROM DB.kidehen.cc_source;

INSERT INTO DB.kidehen.cc_source (source_id, name, system_type, description) VALUES (1, 'Cloud Warehouse', 'warehouse', 'Analyst SQL in the cloud warehouse');
INSERT INTO DB.kidehen.cc_source (source_id, name, system_type, description) VALUES (2, 'CRM', 'crm', 'Deal-desk / CRM opportunity fields');
INSERT INTO DB.kidehen.cc_source (source_id, name, system_type, description) VALUES (3, 'BI Tool', 'bi', 'Dashboard formulas');
INSERT INTO DB.kidehen.cc_source (source_id, name, system_type, description) VALUES (4, 'Metadata Catalog', 'catalog', 'Catalogued metric definitions');

INSERT INTO DB.kidehen.cc_entity (entity_id, preferred_label, description) VALUES (1, 'Opportunity', 'A sales opportunity / deal');
INSERT INTO DB.kidehen.cc_entity (entity_id, preferred_label, description) VALUES (2, 'Account', 'A customer or prospect account');

INSERT INTO DB.kidehen.cc_entity_alt_label (entity_id, alt_label) VALUES (1, 'Deal');
INSERT INTO DB.kidehen.cc_entity_alt_label (entity_id, alt_label) VALUES (1, 'Opp');
INSERT INTO DB.kidehen.cc_entity_alt_label (entity_id, alt_label) VALUES (2, 'Customer');
INSERT INTO DB.kidehen.cc_entity_alt_label (entity_id, alt_label) VALUES (2, 'Company');

INSERT INTO DB.kidehen.cc_metric (metric_id, entity_id, preferred_label, description) VALUES (1, 1, 'Win Rate', 'Share of opportunities that closed won — contested definition');

INSERT INTO DB.kidehen.cc_property (property_id, entity_id, preferred_label, description) VALUES (1, 1, 'stage', 'Lifecycle stage');
INSERT INTO DB.kidehen.cc_property (property_id, entity_id, preferred_label, description) VALUES (2, 1, 'amount', 'Deal amount');
INSERT INTO DB.kidehen.cc_property (property_id, entity_id, preferred_label, description) VALUES (3, 1, 'is_new_business', 'New-business flag');

INSERT INTO DB.kidehen.cc_relationship (rel_id, from_entity_id, to_entity_id, preferred_label) VALUES (1, 1, 2, 'belongs_to');

INSERT INTO DB.kidehen.cc_claim (claim_id, claim_kind, subject_ref, definition_text, source_id, confidence, valid_from, valid_to, status, reviewed_by, reviewed_at)
VALUES (1, 'definition', 'metric:1', 'closed_won / all closed opportunities', 1, 0.8200, cast('2024-01-01' as date), cast('2025-06-30' as date), 'superseded', 'emily', cast('2025-07-01' as datetime));
INSERT INTO DB.kidehen.cc_claim (claim_id, claim_kind, subject_ref, definition_text, source_id, confidence, valid_from, valid_to, status, reviewed_by, reviewed_at)
VALUES (2, 'definition', 'metric:1', 'closed_won / closed opportunities that reached qualification (exclude never-qualified)', 2, 0.9100, cast('2025-07-01' as date), NULL, 'approved', 'emily', cast('2025-07-02' as datetime));
INSERT INTO DB.kidehen.cc_claim (claim_id, claim_kind, subject_ref, definition_text, source_id, confidence, valid_from, valid_to, status, reviewed_by, reviewed_at)
VALUES (3, 'definition', 'metric:1', 'closed_won / closed new-business opportunities only', 3, 0.7400, cast('2025-01-01' as date), NULL, 'candidate', NULL, NULL);

INSERT INTO DB.kidehen.cc_opportunity (opp_id, account_name, stage, amount, created_at, closed_at, is_new_business, reached_qualification)
VALUES (1, 'Acme', 'closed_won', 100000, cast('2025-02-01' as date), cast('2025-03-15' as date), 1, 1);
INSERT INTO DB.kidehen.cc_opportunity (opp_id, account_name, stage, amount, created_at, closed_at, is_new_business, reached_qualification)
VALUES (2, 'BetaCo', 'closed_lost', 50000, cast('2025-02-10' as date), cast('2025-04-01' as date), 1, 1);
INSERT INTO DB.kidehen.cc_opportunity (opp_id, account_name, stage, amount, created_at, closed_at, is_new_business, reached_qualification)
VALUES (3, 'Gamma', 'closed_lost', 30000, cast('2025-03-01' as date), cast('2025-03-20' as date), 0, 0);
INSERT INTO DB.kidehen.cc_opportunity (opp_id, account_name, stage, amount, created_at, closed_at, is_new_business, reached_qualification)
VALUES (4, 'Delta', 'closed_won', 80000, cast('2025-05-01' as date), cast('2025-06-10' as date), 1, 1);
INSERT INTO DB.kidehen.cc_opportunity (opp_id, account_name, stage, amount, created_at, closed_at, is_new_business, reached_qualification)
VALUES (5, 'Epsilon', 'closed_lost', 20000, cast('2025-05-15' as date), cast('2025-07-01' as date), 0, 1);
INSERT INTO DB.kidehen.cc_opportunity (opp_id, account_name, stage, amount, created_at, closed_at, is_new_business, reached_qualification)
VALUES (6, 'Zeta', 'open', 90000, cast('2025-08-01' as date), NULL, 1, 1);
INSERT INTO DB.kidehen.cc_opportunity (opp_id, account_name, stage, amount, created_at, closed_at, is_new_business, reached_qualification)
VALUES (7, 'Eta', 'closed_won', 40000, cast('2024-11-01' as date), cast('2025-01-20' as date), 0, 1);
INSERT INTO DB.kidehen.cc_opportunity (opp_id, account_name, stage, amount, created_at, closed_at, is_new_business, reached_qualification)
VALUES (8, 'Theta', 'closed_lost', 15000, cast('2025-01-05' as date), cast('2025-02-01' as date), 1, 0);
