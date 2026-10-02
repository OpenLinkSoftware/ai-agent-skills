SPARQL
prefix DB: <http://demo.openlinksw.com/schemas/DB/> 
create iri class DB:cc_source "http://^{URIQADefaultHost}^/DB/cc_source/source_id/%d#this" (in _source_id integer not null) . ;
SPARQL
prefix DB: <http://demo.openlinksw.com/schemas/DB/> 
create iri class DB:cc_entity "http://^{URIQADefaultHost}^/DB/cc_entity/entity_id/%d#this" (in _entity_id integer not null) . ;
SPARQL
prefix DB: <http://demo.openlinksw.com/schemas/DB/> 
create iri class DB:cc_entity_alt_label "http://^{URIQADefaultHost}^/DB/cc_entity_alt_label/entity_id/%d/alt_label/%U#this" (in _entity_id integer not null,in _alt_label varchar not null) . ;
SPARQL
prefix DB: <http://demo.openlinksw.com/schemas/DB/> 
create iri class DB:cc_metric "http://^{URIQADefaultHost}^/DB/cc_metric/metric_id/%d#this" (in _metric_id integer not null) . ;
SPARQL
prefix DB: <http://demo.openlinksw.com/schemas/DB/> 
create iri class DB:cc_property "http://^{URIQADefaultHost}^/DB/cc_property/property_id/%d#this" (in _property_id integer not null) . ;
SPARQL
prefix DB: <http://demo.openlinksw.com/schemas/DB/> 
create iri class DB:cc_relationship "http://^{URIQADefaultHost}^/DB/cc_relationship/rel_id/%d#this" (in _rel_id integer not null) . ;
SPARQL
prefix DB: <http://demo.openlinksw.com/schemas/DB/> 
create iri class DB:cc_claim "http://^{URIQADefaultHost}^/DB/cc_claim/claim_id/%d#this" (in _claim_id integer not null) . ;
SPARQL
prefix DB: <http://demo.openlinksw.com/schemas/DB/> 
create iri class DB:cc_opportunity "http://^{URIQADefaultHost}^/DB/cc_opportunity/opp_id/%d#this" (in _opp_id integer not null) . ;


SPARQL
prefix DB: <http://demo.openlinksw.com/schemas/DB/> 
prefix aowl: <http://bblfish.net/work/atom-owl/2006-06-06/> 
alter quad storage virtrdf:DefaultQuadStorage 
 from "DB"."kidehen"."cc_source" as cc_source_s
 { 
   create DB:qm-cc_source as graph iri ("http://^{URIQADefaultHost}^/DB#")  
    { 
      # Maps from columns of "DB.kidehen.cc_source"
      DB:cc_source (cc_source_s."source_id")  a DB:cc_source ;
      DB:source_id cc_source_s."source_id" as DB:kidehen-cc_source-source_id ;
      DB:name cc_source_s."name" as DB:kidehen-cc_source-name ;
      DB:system_type cc_source_s."system_type" as DB:kidehen-cc_source-system_type ;
      DB:description cc_source_s."description" as DB:kidehen-cc_source-description .

    }
 }

;

SPARQL
prefix DB: <http://demo.openlinksw.com/schemas/DB/> 
prefix aowl: <http://bblfish.net/work/atom-owl/2006-06-06/> 
alter quad storage virtrdf:DefaultQuadStorage 
 from "DB"."kidehen"."cc_entity" as cc_entity_s
 { 
   create DB:qm-cc_entity as graph iri ("http://^{URIQADefaultHost}^/DB#")  
    { 
      # Maps from columns of "DB.kidehen.cc_entity"
      DB:cc_entity (cc_entity_s."entity_id")  a DB:cc_entity ;
      DB:entity_id cc_entity_s."entity_id" as DB:kidehen-cc_entity-entity_id ;
      DB:preferred_label cc_entity_s."preferred_label" as DB:kidehen-cc_entity-preferred_label ;
      DB:description cc_entity_s."description" as DB:kidehen-cc_entity-description .

    }
 }

;

SPARQL
prefix DB: <http://demo.openlinksw.com/schemas/DB/> 
prefix aowl: <http://bblfish.net/work/atom-owl/2006-06-06/> 
alter quad storage virtrdf:DefaultQuadStorage 
 from "DB"."kidehen"."cc_entity_alt_label" as cc_entity_alt_label_s
 { 
   create DB:qm-cc_entity_alt_label as graph iri ("http://^{URIQADefaultHost}^/DB#")  
    { 
      # Maps from columns of "DB.kidehen.cc_entity_alt_label"
      DB:cc_entity_alt_label (cc_entity_alt_label_s."entity_id",cc_entity_alt_label_s."alt_label")  a DB:cc_entity_alt_label ;
      DB:entity_id cc_entity_alt_label_s."entity_id" as DB:kidehen-cc_entity_alt_label-entity_id ;
      DB:alt_label cc_entity_alt_label_s."alt_label" as DB:kidehen-cc_entity_alt_label-alt_label .

    }
 }

;

SPARQL
prefix DB: <http://demo.openlinksw.com/schemas/DB/> 
prefix aowl: <http://bblfish.net/work/atom-owl/2006-06-06/> 
alter quad storage virtrdf:DefaultQuadStorage 
 from "DB"."kidehen"."cc_metric" as cc_metric_s
 { 
   create DB:qm-cc_metric as graph iri ("http://^{URIQADefaultHost}^/DB#")  
    { 
      # Maps from columns of "DB.kidehen.cc_metric"
      DB:cc_metric (cc_metric_s."metric_id")  a DB:cc_metric ;
      DB:metric_id cc_metric_s."metric_id" as DB:kidehen-cc_metric-metric_id ;
      DB:entity_id cc_metric_s."entity_id" as DB:kidehen-cc_metric-entity_id ;
      DB:preferred_label cc_metric_s."preferred_label" as DB:kidehen-cc_metric-preferred_label ;
      DB:description cc_metric_s."description" as DB:kidehen-cc_metric-description .

    }
 }

;

SPARQL
prefix DB: <http://demo.openlinksw.com/schemas/DB/> 
prefix aowl: <http://bblfish.net/work/atom-owl/2006-06-06/> 
alter quad storage virtrdf:DefaultQuadStorage 
 from "DB"."kidehen"."cc_property" as cc_property_s
 { 
   create DB:qm-cc_property as graph iri ("http://^{URIQADefaultHost}^/DB#")  
    { 
      # Maps from columns of "DB.kidehen.cc_property"
      DB:cc_property (cc_property_s."property_id")  a DB:cc_property ;
      DB:property_id cc_property_s."property_id" as DB:kidehen-cc_property-property_id ;
      DB:entity_id cc_property_s."entity_id" as DB:kidehen-cc_property-entity_id ;
      DB:preferred_label cc_property_s."preferred_label" as DB:kidehen-cc_property-preferred_label ;
      DB:description cc_property_s."description" as DB:kidehen-cc_property-description .

    }
 }

;

SPARQL
prefix DB: <http://demo.openlinksw.com/schemas/DB/> 
prefix aowl: <http://bblfish.net/work/atom-owl/2006-06-06/> 
alter quad storage virtrdf:DefaultQuadStorage 
 from "DB"."kidehen"."cc_relationship" as cc_relationship_s
 { 
   create DB:qm-cc_relationship as graph iri ("http://^{URIQADefaultHost}^/DB#")  
    { 
      # Maps from columns of "DB.kidehen.cc_relationship"
      DB:cc_relationship (cc_relationship_s."rel_id")  a DB:cc_relationship ;
      DB:rel_id cc_relationship_s."rel_id" as DB:kidehen-cc_relationship-rel_id ;
      DB:from_entity_id cc_relationship_s."from_entity_id" as DB:kidehen-cc_relationship-from_entity_id ;
      DB:to_entity_id cc_relationship_s."to_entity_id" as DB:kidehen-cc_relationship-to_entity_id ;
      DB:preferred_label cc_relationship_s."preferred_label" as DB:kidehen-cc_relationship-preferred_label .

    }
 }

;

SPARQL
prefix DB: <http://demo.openlinksw.com/schemas/DB/> 
prefix aowl: <http://bblfish.net/work/atom-owl/2006-06-06/> 
alter quad storage virtrdf:DefaultQuadStorage 
 from "DB"."kidehen"."cc_claim" as cc_claim_s
 { 
   create DB:qm-cc_claim as graph iri ("http://^{URIQADefaultHost}^/DB#")  
    { 
      # Maps from columns of "DB.kidehen.cc_claim"
      DB:cc_claim (cc_claim_s."claim_id")  a DB:cc_claim ;
      DB:claim_id cc_claim_s."claim_id" as DB:kidehen-cc_claim-claim_id ;
      DB:claim_kind cc_claim_s."claim_kind" as DB:kidehen-cc_claim-claim_kind ;
      DB:subject_ref cc_claim_s."subject_ref" as DB:kidehen-cc_claim-subject_ref ;
      DB:definition_text cc_claim_s."definition_text" as DB:kidehen-cc_claim-definition_text ;
      DB:source_id cc_claim_s."source_id" as DB:kidehen-cc_claim-source_id ;
      DB:confidence cc_claim_s."confidence" as DB:kidehen-cc_claim-confidence ;
      DB:valid_from cc_claim_s."valid_from" as DB:kidehen-cc_claim-valid_from ;
      DB:valid_to cc_claim_s."valid_to" as DB:kidehen-cc_claim-valid_to ;
      DB:status cc_claim_s."status" as DB:kidehen-cc_claim-status ;
      DB:reviewed_by cc_claim_s."reviewed_by" as DB:kidehen-cc_claim-reviewed_by ;
      DB:reviewed_at cc_claim_s."reviewed_at" as DB:kidehen-cc_claim-reviewed_at .

    }
 }

;

SPARQL
prefix DB: <http://demo.openlinksw.com/schemas/DB/> 
prefix aowl: <http://bblfish.net/work/atom-owl/2006-06-06/> 
alter quad storage virtrdf:DefaultQuadStorage 
 from "DB"."kidehen"."cc_opportunity" as cc_opportunity_s
 { 
   create DB:qm-cc_opportunity as graph iri ("http://^{URIQADefaultHost}^/DB#") option (exclusive) 
    { 
      # Maps from columns of "DB.kidehen.cc_opportunity"
      DB:cc_opportunity (cc_opportunity_s."opp_id")  a DB:cc_opportunity ;
      DB:opp_id cc_opportunity_s."opp_id" as DB:kidehen-cc_opportunity-opp_id ;
      DB:account_name cc_opportunity_s."account_name" as DB:kidehen-cc_opportunity-account_name ;
      DB:stage cc_opportunity_s."stage" as DB:kidehen-cc_opportunity-stage ;
      DB:amount cc_opportunity_s."amount" as DB:kidehen-cc_opportunity-amount ;
      DB:created_at cc_opportunity_s."created_at" as DB:kidehen-cc_opportunity-created_at ;
      DB:closed_at cc_opportunity_s."closed_at" as DB:kidehen-cc_opportunity-closed_at ;
      DB:is_new_business cc_opportunity_s."is_new_business" as DB:kidehen-cc_opportunity-is_new_business ;
      DB:reached_qualification cc_opportunity_s."reached_qualification" as DB:kidehen-cc_opportunity-reached_qualification .

    }
 }

;
