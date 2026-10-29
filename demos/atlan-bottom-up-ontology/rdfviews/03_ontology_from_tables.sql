-- =============================================================================
-- 03_ontology_from_tables.sql
-- Virtuoso RDF View / Quad Map scaffolding for DB.kidehen → atlan-cc ontology
-- Graph:     http://localhost:8890/atlan-cc#
-- Ontology:  http://localhost:8890/schemas/atlan-cc/
-- Instances: http://localhost:8890/atlan-cc/{type}/{id}#this
-- =============================================================================

-- Load T-Box (run once; adjust path if loading from isql FILE)
-- SPARQL LOAD <file:///path/to/ontology/atlan-cc.ttl> INTO GRAPH <http://localhost:8890/schemas/atlan-cc/> ;

SPARQL CLEAR GRAPH <http://localhost:8890/schemas/atlan-cc/> ;

-- Inline minimal T-Box insert if file load unavailable
SPARQL
PREFIX owl:  <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX :     <http://localhost:8890/schemas/atlan-cc/>
INSERT DATA {
  GRAPH <http://localhost:8890/schemas/atlan-cc/> {
    <http://localhost:8890/schemas/atlan-cc/> a owl:Ontology ;
      rdfs:label "Atlan CC Showcase Ontology" .
    :Claim a owl:Class ; rdfs:label "Claim" .
    :Source a owl:Class ; rdfs:label "Source" .
    :Entity a owl:Class ; rdfs:label "Business Entity" .
    :Metric a owl:Class ; rdfs:label "Metric" .
    :Property a owl:Class ; rdfs:label "Property" .
    :Relationship a owl:Class ; rdfs:label "Relationship" .
    :Opportunity a owl:Class ; rdfs:label "Opportunity" .
  }
};

-- -----------------------------------------------------------------------------
-- IRI classes (classic Virtuoso RDF Views)
-- Host fixed to localhost:8890 per local showcase
-- -----------------------------------------------------------------------------

create function DB.DBA.ATLAN_CC_SOURCE_IRI (in id integer)
  returns varchar
{
  return sprintf('http://localhost:8890/atlan-cc/source/%d#this', id);
};

create function DB.DBA.ATLAN_CC_SOURCE_IRI_INVERSE (in iri varchar)
  returns integer
{
  declare parts any;
  parts := sprintf_inverse(iri, 'http://localhost:8890/atlan-cc/source/%d#this', 0);
  if (parts is not null)
    return parts[0];
  return null;
};

create function DB.DBA.ATLAN_CC_ENTITY_IRI (in id integer)
  returns varchar
{
  return sprintf('http://localhost:8890/atlan-cc/entity/%d#this', id);
};

create function DB.DBA.ATLAN_CC_ENTITY_IRI_INVERSE (in iri varchar)
  returns integer
{
  declare parts any;
  parts := sprintf_inverse(iri, 'http://localhost:8890/atlan-cc/entity/%d#this', 0);
  if (parts is not null)
    return parts[0];
  return null;
};

create function DB.DBA.ATLAN_CC_METRIC_IRI (in id integer)
  returns varchar
{
  return sprintf('http://localhost:8890/atlan-cc/metric/%d#this', id);
};

create function DB.DBA.ATLAN_CC_METRIC_IRI_INVERSE (in iri varchar)
  returns integer
{
  declare parts any;
  parts := sprintf_inverse(iri, 'http://localhost:8890/atlan-cc/metric/%d#this', 0);
  if (parts is not null)
    return parts[0];
  return null;
};

create function DB.DBA.ATLAN_CC_PROPERTY_IRI (in id integer)
  returns varchar
{
  return sprintf('http://localhost:8890/atlan-cc/property/%d#this', id);
};

create function DB.DBA.ATLAN_CC_PROPERTY_IRI_INVERSE (in iri varchar)
  returns integer
{
  declare parts any;
  parts := sprintf_inverse(iri, 'http://localhost:8890/atlan-cc/property/%d#this', 0);
  if (parts is not null)
    return parts[0];
  return null;
};

create function DB.DBA.ATLAN_CC_REL_IRI (in id integer)
  returns varchar
{
  return sprintf('http://localhost:8890/atlan-cc/relationship/%d#this', id);
};

create function DB.DBA.ATLAN_CC_REL_IRI_INVERSE (in iri varchar)
  returns integer
{
  declare parts any;
  parts := sprintf_inverse(iri, 'http://localhost:8890/atlan-cc/relationship/%d#this', 0);
  if (parts is not null)
    return parts[0];
  return null;
};

create function DB.DBA.ATLAN_CC_CLAIM_IRI (in id integer)
  returns varchar
{
  return sprintf('http://localhost:8890/atlan-cc/claim/%d#this', id);
};

create function DB.DBA.ATLAN_CC_CLAIM_IRI_INVERSE (in iri varchar)
  returns integer
{
  declare parts any;
  parts := sprintf_inverse(iri, 'http://localhost:8890/atlan-cc/claim/%d#this', 0);
  if (parts is not null)
    return parts[0];
  return null;
};

create function DB.DBA.ATLAN_CC_OPP_IRI (in id integer)
  returns varchar
{
  return sprintf('http://localhost:8890/atlan-cc/opportunity/%d#this', id);
};

create function DB.DBA.ATLAN_CC_OPP_IRI_INVERSE (in iri varchar)
  returns integer
{
  declare parts any;
  parts := sprintf_inverse(iri, 'http://localhost:8890/atlan-cc/opportunity/%d#this', 0);
  if (parts is not null)
    return parts[0];
  return null;
};

grant execute on DB.DBA.ATLAN_CC_SOURCE_IRI to public;
grant execute on DB.DBA.ATLAN_CC_SOURCE_IRI_INVERSE to public;
grant execute on DB.DBA.ATLAN_CC_ENTITY_IRI to public;
grant execute on DB.DBA.ATLAN_CC_ENTITY_IRI_INVERSE to public;
grant execute on DB.DBA.ATLAN_CC_METRIC_IRI to public;
grant execute on DB.DBA.ATLAN_CC_METRIC_IRI_INVERSE to public;
grant execute on DB.DBA.ATLAN_CC_PROPERTY_IRI to public;
grant execute on DB.DBA.ATLAN_CC_PROPERTY_IRI_INVERSE to public;
grant execute on DB.DBA.ATLAN_CC_REL_IRI to public;
grant execute on DB.DBA.ATLAN_CC_REL_IRI_INVERSE to public;
grant execute on DB.DBA.ATLAN_CC_CLAIM_IRI to public;
grant execute on DB.DBA.ATLAN_CC_CLAIM_IRI_INVERSE to public;
grant execute on DB.DBA.ATLAN_CC_OPP_IRI to public;
grant execute on DB.DBA.ATLAN_CC_OPP_IRI_INVERSE to public;

-- Register IRI classes for Quad Map
SPARQL
create iri class <http://localhost:8890/schemas/atlan-cc/iri/source>
  "http://localhost:8890/atlan-cc/source/%d#this"
  (in source_id integer not null)
  option (returns "http://localhost:8890/atlan-cc/source/%d#this") .

create iri class <http://localhost:8890/schemas/atlan-cc/iri/entity>
  "http://localhost:8890/atlan-cc/entity/%d#this"
  (in entity_id integer not null)
  option (returns "http://localhost:8890/atlan-cc/entity/%d#this") .

create iri class <http://localhost:8890/schemas/atlan-cc/iri/metric>
  "http://localhost:8890/atlan-cc/metric/%d#this"
  (in metric_id integer not null)
  option (returns "http://localhost:8890/atlan-cc/metric/%d#this") .

create iri class <http://localhost:8890/schemas/atlan-cc/iri/property>
  "http://localhost:8890/atlan-cc/property/%d#this"
  (in property_id integer not null)
  option (returns "http://localhost:8890/atlan-cc/property/%d#this") .

create iri class <http://localhost:8890/schemas/atlan-cc/iri/relationship>
  "http://localhost:8890/atlan-cc/relationship/%d#this"
  (in rel_id integer not null)
  option (returns "http://localhost:8890/atlan-cc/relationship/%d#this") .

create iri class <http://localhost:8890/schemas/atlan-cc/iri/claim>
  "http://localhost:8890/atlan-cc/claim/%d#this"
  (in claim_id integer not null)
  option (returns "http://localhost:8890/atlan-cc/claim/%d#this") .

create iri class <http://localhost:8890/schemas/atlan-cc/iri/opportunity>
  "http://localhost:8890/atlan-cc/opportunity/%d#this"
  (in opp_id integer not null)
  option (returns "http://localhost:8890/atlan-cc/opportunity/%d#this") .
;

-- Ensure Linked Data Views graph exists
SPARQL CREATE SILENT GRAPH <http://localhost:8890/atlan-cc#> ;
