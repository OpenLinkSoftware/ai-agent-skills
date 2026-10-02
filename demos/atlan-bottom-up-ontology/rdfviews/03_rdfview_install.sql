-- Companion compact install (alternate to 03_ontology_from_tables.sql + 04_rdfview_data_rules.sql)
-- Install Linked Data Views for DB.kidehen.cc_* tables
-- Host: localhost:8890 (shop-database Virtuoso)

SPARQL DROP SILENT GRAPH <http://localhost:8890/schemas/atlan-cc/> ;
SPARQL CLEAR GRAPH <http://localhost:8890/schemas/atlan-cc/> ;

-- Load ontology into its graph (path may need adjust after DAV publish; here we TTLP from file if available)
-- Parent loads ontology via TTLP after copy.

-- Quad map definition
SPARQL
prefix oplsioc: <http://www.openlinksw.com/schemas/oplsioc#>
prefix sioc: <http://rdfs.org/sioc/ns#>
prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
prefix a: <http://localhost:8890/schemas/atlan-cc/>
prefix xsd: <http://www.w3.org/2001/XMLSchema#>

drop silent quad map virtrdf:AtlanCC
;

create iri class a:source_iri "http://localhost:8890/atlan-cc/source/%d#this" (in source_id integer not null) .
create iri class a:entity_iri "http://localhost:8890/atlan-cc/entity/%d#this" (in entity_id integer not null) .
create iri class a:metric_iri "http://localhost:8890/atlan-cc/metric/%d#this" (in metric_id integer not null) .
create iri class a:claim_iri "http://localhost:8890/atlan-cc/claim/%d#this" (in claim_id integer not null) .
create iri class a:opp_iri "http://localhost:8890/atlan-cc/opportunity/%d#this" (in opp_id integer not null) .

create virtrdf:AtlanCC as graph iri ("http://localhost:8890/atlan-cc#") option (exclusive)
  {
    a:source_iri (DB.kidehen.cc_source.source_id)
      a a:Source ;
      a:preferredLabel DB.kidehen.cc_source.name as a:src_name ;
      a:systemType DB.kidehen.cc_source.system_type as a:src_type ;
      rdfs:comment DB.kidehen.cc_source.description as a:src_desc .

    a:entity_iri (DB.kidehen.cc_entity.entity_id)
      a a:Entity ;
      a:preferredLabel DB.kidehen.cc_entity.preferred_label as a:ent_pref ;
      rdfs:comment DB.kidehen.cc_entity.description as a:ent_desc .

    a:metric_iri (DB.kidehen.cc_metric.metric_id)
      a a:Metric ;
      a:preferredLabel DB.kidehen.cc_metric.preferred_label as a:met_pref ;
      rdfs:comment DB.kidehen.cc_metric.description as a:met_desc ;
      a:forEntity a:entity_iri (DB.kidehen.cc_metric.entity_id) as a:met_ent .

    a:claim_iri (DB.kidehen.cc_claim.claim_id)
      a a:Claim ;
      a:claimKind DB.kidehen.cc_claim.claim_kind as a:cl_kind ;
      a:subjectRef DB.kidehen.cc_claim.subject_ref as a:cl_subj ;
      a:definitionText DB.kidehen.cc_claim.definition_text as a:cl_def ;
      a:confidence DB.kidehen.cc_claim.confidence as a:cl_conf ;
      a:validFrom DB.kidehen.cc_claim.valid_from as a:cl_from ;
      a:validTo DB.kidehen.cc_claim.valid_to as a:cl_to ;
      a:status DB.kidehen.cc_claim.status as a:cl_status ;
      a:derivedFrom a:source_iri (DB.kidehen.cc_claim.source_id) as a:cl_src .

    a:opp_iri (DB.kidehen.cc_opportunity.opp_id)
      a a:Opportunity ;
      a:preferredLabel DB.kidehen.cc_opportunity.account_name as a:opp_acct ;
      a:stage DB.kidehen.cc_opportunity.stage as a:opp_stage ;
      a:amount DB.kidehen.cc_opportunity.amount as a:opp_amt ;
      a:isNewBusiness DB.kidehen.cc_opportunity.is_new_business as a:opp_nb ;
      a:reachedQualification DB.kidehen.cc_opportunity.reached_qualification as a:opp_qual .
  }
;

-- Register /sparql graph visibility
SPARQL
  prefix virtrdf: <http://www.openlinksw.com/schemas/virtrdf#>
  insert into graph <http://localhost:8890/atlan-cc#> { }
;

-- Alternate labels as physical triples (simpler than quad map join for demo)
-- Loaded after RDF view via SPARQL INSERT from SQL in 04_alt_labels.sql
