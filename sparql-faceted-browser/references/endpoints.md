# Endpoints

These are the presets the app ships with, copied from its endpoint menu. The app checked each one with a live ASK
on 2026-10-14. The skill accepts any other endpoint through `--ep`.

| Endpoint | Name | Engine (verified 2026-10-15) | Notes |
|---|---|---|---|
| https://linkeddata.uriburner.com/sparql | URIBurner (UB) | Virtuoso | Default endpoint (app and scripts); holds the UB Blog companion graphs; VoID class partitions |
| https://dbpedia.org/sparql | DBpedia | Virtuoso | Pass `--ep https://dbpedia.org/sparql` (the worked examples do) |
| https://query.wikidata.org/sparql | Wikidata | Wikidata | Answers in SPARQL XML; types via `wdt:P31` |
| https://wikidata.demo.openlinksw.com/sparql | Wikidata, OpenLink instance | Virtuoso | Sends CORS headers for any origin since 2026-10-16, so the app connects directly |
| https://demo.openlinksw.com/sparql | OpenLink demo server | Virtuoso | Added 2026-10-17. CORS for any origin. A mixed demo store (Transfermarkt players, TCRD genes, NFL plays, LUBM, UMLS…) |
| https://vec.demo.openlinksw.com/sparql | OpenLink vector demo (DBpedia) | Virtuoso | Added 2026-10-22. CORS echoes the requesting origin. Has a vector index, so the **by meaning** search scope (`bif:knnSimilar`) appears; the first query after idle can take ~19 s |
| https://sparql.uniprot.org/sparql | UniProt | Generic SPARQL 1.1 | No Anytime; descriptions are not folded |
| https://publications.europa.eu/webapi/rdf/sparql | EU Publications Office | detected at run time | No CORS: the app needs the proxy |
| https://data.europa.eu/sparql | EU data portal (Cordis) | detected at run time | |
| https://api.parliament.uk/sparql | UK Parliament | detected at run time | |
| https://sparql.cellosaurus.org/sparql | Cellosaurus | detected at run time | |
| https://data.gov.cz/sparql | Czech Government | detected at run time | |
| https://data.idref.fr/sparql | IdRef (Sudoc authorities) | detected at run time | |
| https://www.nakala.fr/sparql | Nakala | detected at run time | |
| https://agrovoc.fao.org/sparql | AGROVOC | detected at run time | |
| https://scienceplus.abes.fr/sparql | science plus (ABES) | detected at run time | |
| https://opendata.aragon.es/sparql | Aragon Open Data | detected at run time | |
| https://data.bibliotheken.nl/sparql | KB, National Library of the Netherlands | detected at run time | |
| https://vocab.nerc.ac.uk/sparql/ | NERC Vocabulary Service | detected at run time | |
| https://data.muziekschatten.nl/sparql | Muziekschatten | detected at run time | |
| https://dati.camera.it/sparql | Italian Chamber of Deputies | Virtuoso | Added 2026-10-15. Intermittent 502s on 2026-10-15 and 2026-10-17; answering again |
| https://lod.dati.gov.it/sparql/ | dati.gov.it (Italian open data) | Virtuoso | Added 2026-10-15 |
| https://datos.gob.es/virtuoso/sparql | datos.gob.es (Spanish open data) | Virtuoso | Added 2026-10-15 |
| https://graph.data.era.europa.eu/repositories/rinf-plus | ERA RINF — EU Register of Railway Infrastructure | GraphDB (generic profile) | Added 2026-10-17. CORS for any origin. https://rinf.data.era.europa.eu/endpoint is the portal's web page, not the SPARQL service. Label search is a full scan (11–15 s). |
| https://graph.data.era.europa.eu/repositories/ERA-Onto | ERA vocabulary & requirements | GraphDB (generic profile) | Added 2026-10-17. CORS for any origin. ERA ontology (341 OWL classes), concept schemes and legal requirements |
| https://graph.data.era.europa.eu/repositories/OCR-KG | ERA OCR — Organisation Code Register | GraphDB (generic profile) | Added 2026-10-17. CORS for any origin. 5,614 railway bodies and their sites |
| https://graph.data.era.europa.eu/repositories/era-lex | ERA-Lex — EU railway legislation | GraphDB (generic profile) | Added 2026-10-17. CORS for any origin. ELI legal resources (7,317), their subdivisions and language expressions |
| https://fedlex.data.admin.ch/sparqlendpoint | Fedlex — Swiss federal law | Non-Virtuoso (generic profile) | Added 2026-10-17. CORS for any origin. https://fedlex.data.admin.ch/en-CH/sparql is the portal page. JOLux: acts are labelled from their expressions (`jolux:isRealizedBy/jolux:title`, language from `jolux:language`). Its gateway rejects any request mentioning `http://xmlns.com/` (FOAF); the app detects this and leaves FOAF terms out |
| https://data.legilux.public.lu/sparqlendpoint | Legilux — Luxembourg legislation | Virtuoso, no free-text index (search uses CONTAINS) | Added 2026-10-17. CORS for any origin. https://data.legilux.public.lu/sparql is the portal page. JOLux, labelled as for Fedlex |
| https://datos.bcn.cl/sparql | BCN, Library of the National Congress of Chile | Virtuoso | No CORS on https; the http vhost sends CORS only on its redirect. The app needs the proxy; the scripts do not |
| https://www1.siop.planejamento.gov.br/sparql/ | SIOP, Brazilian federal budget | Virtuoso 06.01 | No CORS: the app needs the proxy. No free-text index, so no search samples |
| https://libris.kb.se/sparql | LIBRIS, National Library of Sweden | Virtuoso | Labels use kbv:name / kbv:prefLabel, outside the app's label properties, so label search finds nothing; use `--any-literal` |
| https://dataforhumanities.abes.fr/sparql | Data for Humanities (ABES) | Virtuoso | Added 2026-10-15 |
| https://sparql.wikipathways.org/sparql | WikiPathways | Virtuoso | Labels are not free-text indexed, so text search returns nothing |
| https://sparql.omabrowser.org/sparql/ | OMA orthology browser | Virtuoso | Gene symbols as labels (TP53, INS) |
| https://sparql.orthodb.org/sparql | OrthoDB | Virtuoso | Large; labels are mostly identifiers |
| https://www.3lgm2.de/sparql | 3LGM², IHE integration profiles | Virtuoso | Added 2026-10-15 |

**Dropped 2026-10-17:** `https://sparql.datao.net/sparql` failed the `ASK { ?s ?p ?o }` probe with HTTP 503 in
repeated runs. `https://dati.camera.it/sparql` failed with HTTP 502 in one run that day but answered again later, so it
stays.

**Left out:** `http://datos.infolobby.cl/sparql`. The app cannot reach it by any route:
- its https certificate is issued for `*.cplt.cl`, not this host;
- plain http is blocked on an https page;
- it refuses the URIBurner proxy with 403.

## CORS: why the chat answer and the app can differ in reach

`fct_query.py` calls endpoints from the agent's machine, so CORS does not apply to it. The app runs in the viewer's
browser and can only read endpoints that send CORS headers.

For an endpoint marked "No CORS":
1. Answer in chat as usual.
2. When linking the app, tell the user to turn on **Settings → Use the URIBurner SPARQL-FED proxy**. The setting
   isn't carried in the link.

## Choosing the endpoint from the request

| The user mentions | Endpoint |
|---|---|
| Wikipedia-derived facts, films, people, places | DBpedia, or Wikidata |
| Wikidata, Q-ids, P-ids | Wikidata |
| URIBurner, the UB Blog, OpenLink how-tos, FAQs, glossaries | URIBurner |
| Proteins, genes, orthology, pathways | UniProt, OMA, OrthoDB or WikiPathways |
| An endpoint URL | That URL, through `--ep` |
