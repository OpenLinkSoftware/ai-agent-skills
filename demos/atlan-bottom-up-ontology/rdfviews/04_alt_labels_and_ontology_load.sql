-- Load ontology TTL and SKOS altLabels into physical graphs
-- Companion helper for 03_rdfview_install.sql / 04_rdfview_data_rules.sql
-- Schema: DB.kidehen · Graph: http://localhost:8890/atlan-cc#

-- Ontology: adjust file path for your host (box, Mac, or DAV)
-- Example Mac path after copy:
--   /Users/kidehen/Documents/Management/Development/ai-agent-skills/demos/atlan-bottom-up-ontology/ontology/atlan-cc.ttl
TTLP (
  file_to_string('{ONTOLOGY_TTL_PATH}'),
  '',
  'http://localhost:8890/schemas/atlan-cc/'
);

-- Or, if ontology already published to DAV / HTTP:
-- SPARQL LOAD <http://localhost:8890/DAV/home/kidehen/atlan-cc/atlan-cc.ttl> INTO GRAPH <http://localhost:8890/schemas/atlan-cc/> ;

-- Materialize alt labels into the instance graph (authority control)
SPARQL
PREFIX a: <http://localhost:8890/schemas/atlan-cc/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
INSERT INTO GRAPH <http://localhost:8890/atlan-cc#> {
  ?e skos:altLabel ?lab ;
     a:altLabel ?lab .
}
WHERE {
  {
    SELECT
      IRI(sprintf('http://localhost:8890/atlan-cc/entity/%d#this', entity_id)) AS ?e,
      alt_label AS ?lab
    FROM DB.kidehen.cc_entity_alt_label
  }
};
