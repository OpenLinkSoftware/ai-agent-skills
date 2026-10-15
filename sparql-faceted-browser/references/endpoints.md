# Endpoints

These are the presets the app ships with, copied from its endpoint menu. The app checked each one with a live ASK
on 2026-10-14. The skill accepts any other endpoint through `--ep`.

| Endpoint | Name | Engine (verified 2026-10-15) | Notes |
|---|---|---|---|
| https://dbpedia.org/sparql | DBpedia | Virtuoso | Default endpoint |
| https://linkeddata.uriburner.com/sparql | URIBurner (UB) | Virtuoso | Holds the UB Blog companion graphs; VoID class partitions |
| https://query.wikidata.org/sparql | Wikidata | Wikidata | Answers in SPARQL XML; types via `wdt:P31` |
| https://wikidata.demo.openlinksw.com/sparql | Wikidata, OpenLink instance | detected at run time | The app needs its UB proxy setting for this one (no CORS); the scripts do not |
| https://sparql.uniprot.org/sparql | UniProt | Generic SPARQL 1.1 | No Anytime; descriptions are not folded |
| https://publications.europa.eu/webapi/rdf/sparql | EU Publications Office | detected at run time | No CORS: the app needs the proxy |
| https://sparql.proconsortium.org/virtuoso/sparql | Protein Ontology | detected at run time | |
| https://data.europa.eu/sparql | EU data portal (Cordis) | detected at run time | |
| https://api.parliament.uk/sparql | UK Parliament | detected at run time | |
| https://sparql.cellosaurus.org/sparql | Cellosaurus | detected at run time | |
| https://data.gov.cz/sparql | Czech Government | detected at run time | |
| https://data.idref.fr/sparql | IdRef (Sudoc authorities) | detected at run time | |
| https://www.nakala.fr/sparql | Nakala | detected at run time | |
| https://agrovoc.fao.org/sparql | AGROVOC | detected at run time | |
| https://scienceplus.abes.fr/sparql | science plus (ABES) | detected at run time | |
| https://opendata.aragon.es/sparql | Aragon Open Data | detected at run time | |
| https://sparql.datao.net/sparql | Datao | detected at run time | Was returning 503 on 2026-10-14 |
| https://data.bibliotheken.nl/sparql | KB, National Library of the Netherlands | detected at run time | |
| https://vocab.nerc.ac.uk/sparql/ | NERC Vocabulary Service | detected at run time | |
| https://data.muziekschatten.nl/sparql | Muziekschatten | detected at run time | |

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
| Proteins, genes | UniProt or Protein Ontology |
| An endpoint URL | That URL, through `--ep` |
