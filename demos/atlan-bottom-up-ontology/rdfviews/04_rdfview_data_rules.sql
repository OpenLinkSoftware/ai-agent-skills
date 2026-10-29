-- =============================================================================
-- 04_rdfview_data_rules.sql
-- QuadMap / RDF View data rules: DB.kidehen.* → graph http://localhost:8890/atlan-cc#
-- Instance IRIs: http://localhost:8890/atlan-cc/{type}/{id}#this
-- =============================================================================

-- Drop prior definition if re-running
SPARQL drop quad map graph iri ("http://localhost:8890/atlan-cc#") .
;

create quad storage virtrdf:DefaultQuadStorage
  from DB.kidehen.cc_source as source_tbl
  from DB.kidehen.cc_entity as entity_tbl
  from DB.kidehen.cc_entity_alt_label as alt_tbl
  from DB.kidehen.cc_metric as metric_tbl
  from DB.kidehen.cc_property as property_tbl
  from DB.kidehen.cc_relationship as rel_tbl
  from DB.kidehen.cc_claim as claim_tbl
  from DB.kidehen.cc_opportunity as opp_tbl
{
  create virtrdf:atlan_cc as graph iri ("http://localhost:8890/atlan-cc#") option (exclusive)
  {
    -- Sources
    <http://localhost:8890/schemas/atlan-cc/iri/source> (source_tbl.source_id)
      a <http://localhost:8890/schemas/atlan-cc/Source> as virtrdf:atlan_cc-Source-type ;
      <http://www.w3.org/2004/02/skos/core#prefLabel> source_tbl.name as virtrdf:atlan_cc-Source-name ;
      <http://localhost:8890/schemas/atlan-cc/systemType> source_tbl.system_type as virtrdf:atlan_cc-Source-systemType ;
      <http://www.w3.org/2000/01/rdf-schema#label> source_tbl.name as virtrdf:atlan_cc-Source-label .

    -- Entities
    <http://localhost:8890/schemas/atlan-cc/iri/entity> (entity_tbl.entity_id)
      a <http://localhost:8890/schemas/atlan-cc/Entity> as virtrdf:atlan_cc-Entity-type ;
      <http://www.w3.org/2004/02/skos/core#prefLabel> entity_tbl.preferred_label as virtrdf:atlan_cc-Entity-pref ;
      <http://localhost:8890/schemas/atlan-cc/preferredLabel> entity_tbl.preferred_label as virtrdf:atlan_cc-Entity-pref2 ;
      <http://www.w3.org/2000/01/rdf-schema#comment> entity_tbl.description as virtrdf:atlan_cc-Entity-desc .

    -- Alt labels (join via entity_id)
    <http://localhost:8890/schemas/atlan-cc/iri/entity> (alt_tbl.entity_id)
      <http://www.w3.org/2004/02/skos/core#altLabel> alt_tbl.alt_label as virtrdf:atlan_cc-Entity-alt ;
      <http://localhost:8890/schemas/atlan-cc/altLabel> alt_tbl.alt_label as virtrdf:atlan_cc-Entity-alt2 .

    -- Metrics
    <http://localhost:8890/schemas/atlan-cc/iri/metric> (metric_tbl.metric_id)
      a <http://localhost:8890/schemas/atlan-cc/Metric> as virtrdf:atlan_cc-Metric-type ;
      <http://www.w3.org/2004/02/skos/core#prefLabel> metric_tbl.preferred_label as virtrdf:atlan_cc-Metric-pref ;
      <http://www.w3.org/2000/01/rdf-schema#comment> metric_tbl.description as virtrdf:atlan_cc-Metric-desc ;
      <http://localhost:8890/schemas/atlan-cc/forEntity>
        <http://localhost:8890/schemas/atlan-cc/iri/entity> (metric_tbl.entity_id)
        as virtrdf:atlan_cc-Metric-entity .

    -- Properties
    <http://localhost:8890/schemas/atlan-cc/iri/property> (property_tbl.property_id)
      a <http://localhost:8890/schemas/atlan-cc/Property> as virtrdf:atlan_cc-Property-type ;
      <http://www.w3.org/2004/02/skos/core#prefLabel> property_tbl.preferred_label as virtrdf:atlan_cc-Property-pref ;
      <http://localhost:8890/schemas/atlan-cc/forEntity>
        <http://localhost:8890/schemas/atlan-cc/iri/entity> (property_tbl.entity_id)
        as virtrdf:atlan_cc-Property-entity .

    -- Relationships
    <http://localhost:8890/schemas/atlan-cc/iri/relationship> (rel_tbl.rel_id)
      a <http://localhost:8890/schemas/atlan-cc/Relationship> as virtrdf:atlan_cc-Rel-type ;
      <http://www.w3.org/2004/02/skos/core#prefLabel> rel_tbl.preferred_label as virtrdf:atlan_cc-Rel-pref ;
      <http://localhost:8890/schemas/atlan-cc/fromEntity>
        <http://localhost:8890/schemas/atlan-cc/iri/entity> (rel_tbl.from_entity_id)
        as virtrdf:atlan_cc-Rel-from ;
      <http://localhost:8890/schemas/atlan-cc/toEntity>
        <http://localhost:8890/schemas/atlan-cc/iri/entity> (rel_tbl.to_entity_id)
        as virtrdf:atlan_cc-Rel-to .

    -- Claims (source + confidence + validity)
    <http://localhost:8890/schemas/atlan-cc/iri/claim> (claim_tbl.claim_id)
      a <http://localhost:8890/schemas/atlan-cc/Claim> as virtrdf:atlan_cc-Claim-type ;
      <http://localhost:8890/schemas/atlan-cc/claimKind> claim_tbl.claim_kind as virtrdf:atlan_cc-Claim-kind ;
      <http://localhost:8890/schemas/atlan-cc/subjectRef> claim_tbl.subject_ref as virtrdf:atlan_cc-Claim-subject ;
      <http://localhost:8890/schemas/atlan-cc/definitionText> claim_tbl.definition_text as virtrdf:atlan_cc-Claim-def ;
      <http://localhost:8890/schemas/atlan-cc/confidence> claim_tbl.confidence as virtrdf:atlan_cc-Claim-conf ;
      <http://localhost:8890/schemas/atlan-cc/validFrom> claim_tbl.valid_from as virtrdf:atlan_cc-Claim-from ;
      <http://localhost:8890/schemas/atlan-cc/validTo> claim_tbl.valid_to as virtrdf:atlan_cc-Claim-to ;
      <http://localhost:8890/schemas/atlan-cc/status> claim_tbl.status as virtrdf:atlan_cc-Claim-status ;
      <http://localhost:8890/schemas/atlan-cc/derivedFrom>
        <http://localhost:8890/schemas/atlan-cc/iri/source> (claim_tbl.source_id)
        as virtrdf:atlan_cc-Claim-src ;
      <http://www.w3.org/ns/prov#wasDerivedFrom>
        <http://localhost:8890/schemas/atlan-cc/iri/source> (claim_tbl.source_id)
        as virtrdf:atlan_cc-Claim-prov ;
      <http://www.w3.org/2000/01/rdf-schema#label> claim_tbl.subject_ref as virtrdf:atlan_cc-Claim-label .

    -- Opportunities (raw facts)
    <http://localhost:8890/schemas/atlan-cc/iri/opportunity> (opp_tbl.opp_id)
      a <http://localhost:8890/schemas/atlan-cc/Opportunity> as virtrdf:atlan_cc-Opp-type ;
      <http://localhost:8890/schemas/atlan-cc/accountName> opp_tbl.account_name as virtrdf:atlan_cc-Opp-acct ;
      <http://localhost:8890/schemas/atlan-cc/stage> opp_tbl.stage as virtrdf:atlan_cc-Opp-stage ;
      <http://localhost:8890/schemas/atlan-cc/amount> opp_tbl.amount as virtrdf:atlan_cc-Opp-amt ;
      <http://localhost:8890/schemas/atlan-cc/createdAt> opp_tbl.created_at as virtrdf:atlan_cc-Opp-created ;
      <http://localhost:8890/schemas/atlan-cc/closedAt> opp_tbl.closed_at as virtrdf:atlan_cc-Opp-closed ;
      <http://localhost:8890/schemas/atlan-cc/isNewBusiness> opp_tbl.is_new_business as virtrdf:atlan_cc-Opp-nb ;
      <http://localhost:8890/schemas/atlan-cc/reachedQualification> opp_tbl.reached_qualification as virtrdf:atlan_cc-Opp-qual .
  } .
} .

-- Alternate / complementary pattern: materialize via SPARQL CONSTRUCT into the graph
-- (useful when QuadMap syntax variants differ across Virtuoso builds)
SPARQL
PREFIX :    <http://localhost:8890/schemas/atlan-cc/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
CLEAR GRAPH <http://localhost:8890/atlan-cc#>
;

-- Note: For Linked Data Views, after create quad storage, run:
--   DB.DBA.RDF_VIEW_SYNC_TO_PHYSICAL ('http://localhost:8890/atlan-cc#', 1, 0);
-- Or rely on virtual quad map evaluation without physical sync.

-- Sanity probe (SPASQL)
SPARQL
SELECT ?g COUNT(*) AS ?triples
WHERE { GRAPH ?g { ?s ?p ?o } }
FILTER (STRSTARTS(STR(?g), "http://localhost:8890/atlan-cc"))
GROUP BY ?g
;
