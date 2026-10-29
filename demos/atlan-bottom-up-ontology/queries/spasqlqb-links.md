# SQL permalinks (live now)

See [LIVE_RESULTS.md](../LIVE_RESULTS.md) for measured results + SQL spasqlqb links.

---

# spasqlqb permalinks — local Virtuoso showcase

**Endpoint UI:** [http://localhost:8890/spasqlqb/](http://localhost:8890/spasqlqb/)  
**User:** `kidehen` · **DSN:** `DSN=Local_Instance` · **pwd:** *(empty in links)*  
**Graph:** `http://localhost:8890/atlan-cc#`  
**Schema:** `DB.kidehen`

> Open a link after loading DDL, sample data, and RDF Views (`sql/` + `rdfviews/`).

## S1 — Competing win-rate claims (SPARQL)

[Open S1 in spasqlqb](http://localhost:8890/spasqlqb/?q=SPARQL%0APREFIX%20%3A%20%20%20%20%3Chttp%3A%2F%2Flocalhost%3A8890%2Fschemas%2Fatlan-cc%2F%3E%0APREFIX%20skos%3A%20%3Chttp%3A%2F%2Fwww.w3.org%2F2004%2F02%2Fskos%2Fcore%23%3E%0ASELECT%20%3Fclaim%20%3Fdef%20%3Fconfidence%20%3FvalidFrom%20%3FvalidTo%20%3Fstatus%20%3FsourceLabel%0AFROM%20%3Chttp%3A%2F%2Flocalhost%3A8890%2Fatlan-cc%23%3E%0AWHERE%20%7B%0A%20%20%3Fclaim%20a%20%3AClaim%20%3B%0A%20%20%20%20%20%20%20%20%20%3AsubjectRef%20%22metric%3Awin_rate%22%20%3B%0A%20%20%20%20%20%20%20%20%20%3AdefinitionText%20%3Fdef%20%3B%0A%20%20%20%20%20%20%20%20%20%3Aconfidence%20%3Fconfidence%20%3B%0A%20%20%20%20%20%20%20%20%20%3AvalidFrom%20%3FvalidFrom%20%3B%0A%20%20%20%20%20%20%20%20%20%3Astatus%20%3Fstatus%20%3B%0A%20%20%20%20%20%20%20%20%20%3AderivedFrom%20%3Fsrc%20.%0A%20%20OPTIONAL%20%7B%20%3Fclaim%20%3AvalidTo%20%3FvalidTo%20%7D%0A%20%20OPTIONAL%20%7B%20%3Fsrc%20skos%3AprefLabel%20%3FsourceLabel%20%7D%0A%7D%0AORDER%20BY%20DESC%28%3Fconfidence%29&uid=kidehen&pwd=&dsn=DSN%3DLocal_Instance)

```sql
SPARQL
PREFIX :    <http://localhost:8890/schemas/atlan-cc/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
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
}
ORDER BY DESC(?confidence)
```

## S2 — Claims valid as-of 2025-03-15

[Open S2 in spasqlqb](http://localhost:8890/spasqlqb/?q=SPARQL%0APREFIX%20%3A%20%3Chttp%3A%2F%2Flocalhost%3A8890%2Fschemas%2Fatlan-cc%2F%3E%0APREFIX%20skos%3A%20%3Chttp%3A%2F%2Fwww.w3.org%2F2004%2F02%2Fskos%2Fcore%23%3E%0APREFIX%20xsd%3A%20%3Chttp%3A%2F%2Fwww.w3.org%2F2001%2FXMLSchema%23%3E%0ASELECT%20%3Fclaim%20%3Fdef%20%3Fconfidence%20%3FvalidFrom%20%3FvalidTo%20%3FsourceLabel%0AFROM%20%3Chttp%3A%2F%2Flocalhost%3A8890%2Fatlan-cc%23%3E%0AWHERE%20%7B%0A%20%20%3Fclaim%20a%20%3AClaim%20%3B%0A%20%20%20%20%20%20%20%20%20%3AsubjectRef%20%22metric%3Awin_rate%22%20%3B%0A%20%20%20%20%20%20%20%20%20%3AclaimKind%20%22definition%22%20%3B%0A%20%20%20%20%20%20%20%20%20%3AdefinitionText%20%3Fdef%20%3B%0A%20%20%20%20%20%20%20%20%20%3Aconfidence%20%3Fconfidence%20%3B%0A%20%20%20%20%20%20%20%20%20%3AvalidFrom%20%3FvalidFrom%20%3B%0A%20%20%20%20%20%20%20%20%20%3AderivedFrom%20%3Fsrc%20.%0A%20%20OPTIONAL%20%7B%20%3Fclaim%20%3AvalidTo%20%3FvalidTo%20%7D%0A%20%20OPTIONAL%20%7B%20%3Fsrc%20skos%3AprefLabel%20%3FsourceLabel%20%7D%0A%20%20FILTER%20%28%3FvalidFrom%20%3C%3D%20%222025-03-15%22%5E%5Exsd%3Adate%29%0A%20%20FILTER%20%28%21BOUND%28%3FvalidTo%29%20%7C%7C%20%3FvalidTo%20%3E%3D%20%222025-03-15%22%5E%5Exsd%3Adate%29%0A%7D%0AORDER%20BY%20DESC%28%3Fconfidence%29&uid=kidehen&pwd=&dsn=DSN%3DLocal_Instance)

```sql
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
```

## S3 — Opportunities (facts)

[Open S3 in spasqlqb](http://localhost:8890/spasqlqb/?q=SPARQL%0APREFIX%20%3A%20%3Chttp%3A%2F%2Flocalhost%3A8890%2Fschemas%2Fatlan-cc%2F%3E%0ASELECT%20%3Fopp%20%3Faccount%20%3Fstage%20%3Famount%20%3FisNewBusiness%20%3FreachedQualification%0AFROM%20%3Chttp%3A%2F%2Flocalhost%3A8890%2Fatlan-cc%23%3E%0AWHERE%20%7B%0A%20%20%3Fopp%20a%20%3AOpportunity%20%3B%0A%20%20%20%20%20%20%20%3AaccountName%20%3Faccount%20%3B%0A%20%20%20%20%20%20%20%3Astage%20%3Fstage%20%3B%0A%20%20%20%20%20%20%20%3Aamount%20%3Famount%20%3B%0A%20%20%20%20%20%20%20%3AisNewBusiness%20%3FisNewBusiness%20%3B%0A%20%20%20%20%20%20%20%3AreachedQualification%20%3FreachedQualification%20.%0A%7D%0AORDER%20BY%20%3Fopp&uid=kidehen&pwd=&dsn=DSN%3DLocal_Instance)

```sql
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
```

## S4 — Entity SKOS labels

[Open S4 in spasqlqb](http://localhost:8890/spasqlqb/?q=SPARQL%0APREFIX%20%3A%20%3Chttp%3A%2F%2Flocalhost%3A8890%2Fschemas%2Fatlan-cc%2F%3E%0APREFIX%20skos%3A%20%3Chttp%3A%2F%2Fwww.w3.org%2F2004%2F02%2Fskos%2Fcore%23%3E%0ASELECT%20%3Fentity%20%3Fpref%20%3Falt%0AFROM%20%3Chttp%3A%2F%2Flocalhost%3A8890%2Fatlan-cc%23%3E%0AWHERE%20%7B%0A%20%20%3Fentity%20a%20%3AEntity%20%3B%20skos%3AprefLabel%20%3Fpref%20.%0A%20%20OPTIONAL%20%7B%20%3Fentity%20skos%3AaltLabel%20%3Falt%20%7D%0A%7D%0AORDER%20BY%20%3Fpref%20%3Falt&uid=kidehen&pwd=&dsn=DSN%3DLocal_Instance)

```sql
SPARQL
PREFIX : <http://localhost:8890/schemas/atlan-cc/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?entity ?pref ?alt
FROM <http://localhost:8890/atlan-cc#>
WHERE {
  ?entity a :Entity ; skos:prefLabel ?pref .
  OPTIONAL { ?entity skos:altLabel ?alt }
}
ORDER BY ?pref ?alt
```

## S5 — SQL competing claims (same truth, SQL)

[Open S5 in spasqlqb](http://localhost:8890/spasqlqb/?q=SELECT%0A%20%20c.claim_id%2C%20c.definition_text%2C%20s.name%2C%20c.confidence%2C%20c.valid_from%2C%20c.valid_to%2C%20c.status%0AFROM%20DB.kidehen.cc_claim%20AS%20c%0AJOIN%20DB.kidehen.cc_source%20AS%20s%20ON%20s.source_id%20%3D%20c.source_id%0AWHERE%20c.subject_ref%20%3D%20%27metric%3Awin_rate%27%0AORDER%20BY%20c.confidence%20DESC&uid=kidehen&pwd=&dsn=DSN%3DLocal_Instance)

```sql
SELECT
  c.claim_id, c.definition_text, s.name, c.confidence, c.valid_from, c.valid_to, c.status
FROM DB.kidehen.cc_claim AS c
JOIN DB.kidehen.cc_source AS s ON s.source_id = c.source_id
WHERE c.subject_ref = 'metric:1'
ORDER BY c.confidence DESC
```

## Notes

- If a permalink is too long for the browser, paste the query body from `06_spasql_samples.sql` into spasqlqb manually.
- SPARQL endpoint alternative: `http://localhost:8890/sparql`
- SQL port: `localhost:1111` (isql / ODBC Local_Instance)
