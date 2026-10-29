-- =============================================================================
-- 06_spasql_samples.sql — SPASQL over RDF View graph http://localhost:8890/atlan-cc#
-- Run in isql or http://localhost:8890/spasqlqb/
-- =============================================================================

-- S1: Competing win-rate claims (surface disagreement)
SPARQL
PREFIX :    <http://localhost:8890/schemas/atlan-cc/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX prov: <http://www.w3.org/ns/prov#>
SELECT ?claim ?def ?confidence ?validFrom ?validTo ?status ?sourceLabel
FROM <http://localhost:8890/atlan-cc#>
WHERE {
  ?claim a :Claim ;
         :subjectRef "metric:1" ;
         :definitionText ?def ;
         :confidence ?confidence ;
         :validFrom ?validFrom ;
         :status ?status ;
         :derivedFrom ?src .
  OPTIONAL { ?claim :validTo ?validTo }
  OPTIONAL { ?src skos:prefLabel ?sourceLabel }
  FILTER (?confidence > 0)
}
ORDER BY DESC(?confidence)
;

-- S2: Claims valid as-of 2025-03-15
SPARQL
PREFIX : <http://localhost:8890/schemas/atlan-cc/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT ?claim ?def ?confidence ?validFrom ?validTo ?sourceLabel
FROM <http://localhost:8890/atlan-cc#>
WHERE {
  ?claim a :Claim ;
         :subjectRef "metric:1" ;
         :claimKind "definition" ;
         :definitionText ?def ;
         :confidence ?confidence ;
         :validFrom ?validFrom ;
         :derivedFrom ?src .
  OPTIONAL { ?claim :validTo ?validTo }
  OPTIONAL { ?src skos:prefLabel ?sourceLabel }
  FILTER (?validFrom <= "2025-03-15"^^xsd:date)
  FILTER (!BOUND(?validTo) || ?validTo >= "2025-03-15"^^xsd:date)
}
ORDER BY DESC(?confidence)
;

-- S3: Opportunities + stages (facts behind the three formulas)
SPARQL
PREFIX : <http://localhost:8890/schemas/atlan-cc/>
SELECT ?opp ?account ?stage ?amount ?isNewBusiness ?reachedQualification
FROM <http://localhost:8890/atlan-cc#>
WHERE {
  ?opp a :Opportunity ;
       :accountName ?account ;
       :stage ?stage ;
       :amount ?amount ;
       :isNewBusiness ?isNewBusiness ;
       :reachedQualification ?reachedQualification .
}
ORDER BY ?opp
;

-- S4: Entity preferred + alt labels (SKOS authority control)
SPARQL
PREFIX : <http://localhost:8890/schemas/atlan-cc/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?entity ?pref ?alt
FROM <http://localhost:8890/atlan-cc#>
WHERE {
  ?entity a :Entity ;
          skos:prefLabel ?pref .
  OPTIONAL { ?entity skos:altLabel ?alt }
}
ORDER BY ?pref ?alt
;

-- S5: Hybrid SPASQL — SQL win-rate A alongside SPARQL claim metadata
SELECT
  'A: closed-won / all-closed' AS formula,
  CAST(SUM(CASE WHEN stage = 'closed-won' THEN 1 ELSE 0 END) AS DECIMAL(18,4))
    / NULLIF(SUM(CASE WHEN stage IN ('closed-won','closed-lost','disqualified') THEN 1 ELSE 0 END), 0)
    AS sql_win_rate
FROM DB.kidehen.cc_opportunity;

SPARQL
PREFIX : <http://localhost:8890/schemas/atlan-cc/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?def ?confidence ?sourceLabel
FROM <http://localhost:8890/atlan-cc#>
WHERE {
  ?claim a :Claim ;
         :subjectRef "metric:1" ;
         :claimKind "definition" ;
         :definitionText ?def ;
         :confidence ?confidence ;
         :derivedFrom ?src .
  OPTIONAL { ?src skos:prefLabel ?sourceLabel }
  FILTER (CONTAINS(LCASE(?def), "all closed"))
}
;
