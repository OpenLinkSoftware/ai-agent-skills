# XMLA Client Showcases

These examples were verified against the public OpenLink Virtuoso XMLA service at `https://demo.openlinksw.com/XMLA` using `DSN=Local_Instance`.

They demonstrate two distinct capabilities:

1. SQL over XMLA against a Virtuoso catalog table.
2. SPASQL over XMLA, with SPARQL-FED delegating part of the query to DBpedia.

## Setup

Run commands from the `xmla-client` directory. Supply credentials through environment variables so they do not appear in the command line, SOAP evidence, or shell history:

```bash
export XMLA_PROPERTY_USERNAME='<XMLA username>'
read -rs XMLA_PROPERTY_PASSWORD
export XMLA_PROPERTY_PASSWORD
```

The OpenLink demo tests used the endpoint's public demo account. Obtain or confirm current credentials from the endpoint operator rather than embedding them in scripts.

## Showcase 1: SQL against `Demo..Customers`

This bounded query retrieves ten customer records:

```bash
python3 scripts/xmla_client.py \
  --endpoint https://demo.openlinksw.com/XMLA \
  --data-source-info 'DSN=Local_Instance' \
  --catalog Demo \
  execute \
  --statement 'SELECT TOP 10 * FROM Demo..Customers' \
  --output-format json
```

Verified result: 10 rows with these columns:

```text
CustomerID, CompanyName, ContactName, ContactTitle, Address, City,
Region, PostalCode, Country, CountryCode, Phone, Fax
```

Sample rows:

| CustomerID | CompanyName | City | Country |
|---|---|---|---|
| `ALFKI` | Alfreds Futterkiste | Berlin | Germany |
| `ANATR` | Ana Trujillo Emparedados y helados | México D.F. | Mexico |
| `ANTON` | Antonio Moreno Taquería | México D.F. | Mexico |
| `AROUT` | Around the Horn | London | United Kingdom |
| `BERGS` | Berglunds snabbköp | Luleå | Sweden |

The client represents XML `xsi:nil="1"` values as an `@attributes` object in normalized JSON, preserving the distinction between a null field and an empty string.

## Showcase 2: SPASQL and SPARQL-FED against DBpedia

This query is SQL at the outer layer, SPARQL inside the derived table, and SPARQL-FED at the `SERVICE` boundary. The inner `LIMIT` bounds work performed by the remote DBpedia endpoint.

```bash
python3 scripts/xmla_client.py \
  --endpoint https://demo.openlinksw.com/XMLA \
  --data-source-info 'DSN=Local_Instance' \
  --catalog DB \
  --timeout 45 \
  execute --stdin --output-format json <<'SQL'
SELECT movie
FROM (SPARQL
  PREFIX dbr: <http://dbpedia.org/resource/>
  PREFIX dbo: <http://dbpedia.org/ontology/>
  SELECT ?movie
  WHERE {
    SERVICE <https://dbpedia.org/sparql> {
      SELECT DISTINCT ?movie
      WHERE {
        ?movie a dbo:Film ;
               dbo:director dbr:Spike_Lee .
      }
      ORDER BY ?movie
      LIMIT 20
    }
  }
) AS movies
ORDER BY movie
SQL
```

Verified result: 20 DBpedia movie IRIs, including:

```text
http://dbpedia.org/resource/25th_Hour
http://dbpedia.org/resource/4_Little_Girls
http://dbpedia.org/resource/Bamboozled
http://dbpedia.org/resource/BlacKkKlansman
http://dbpedia.org/resource/Chi-Raq
http://dbpedia.org/resource/Crooklyn
http://dbpedia.org/resource/Da_5_Bloods
http://dbpedia.org/resource/Do_the_Right_Thing
http://dbpedia.org/resource/He_Got_Game
http://dbpedia.org/resource/Inside_Man
```

The successful execution chain was:

```text
XMLA Execute
  -> Virtuoso SQL
    -> SPASQL derived table
      -> SPARQL-FED SERVICE
        -> DBpedia SPARQL endpoint
```

### Federation portability note

Projecting DBpedia's language-tagged `rdfs:label` directly through this specific federation path produced Virtuoso error `SR549` while materializing the RDF literal. Converting that label with a computed alias inside the remote `SERVICE` subquery then produced `SP031`, because the remote service binding did not advertise support for that result-set extension.

Projecting the movie IRIs is the demonstrated interoperable form. Resolve labels separately when the provider can do so without crossing this literal-conversion boundary.

## Protocol notes

- XMLA is tested with a SOAP `POST`; a browser-style `GET /XMLA` may return 404 even when XMLA works.
- Start endpoint inspection with `DISCOVER_DATASOURCES`, then `DISCOVER_SCHEMA_ROWSETS` and `DISCOVER_PROPERTIES`.
- The OpenLink demo advertises `UserName` and `Password` as XMLA `PropertyList` values. The client sources these from `XMLA_PROPERTY_USERNAME` and `XMLA_PROPERTY_PASSWORD`.
- Preserve `--response-out` when diagnosing provider faults; the client writes the raw SOAP response even when the HTTP status is 500.

See [SKILL.md](SKILL.md) for operating instructions and [references/xmla-protocol.md](references/xmla-protocol.md) for protocol details.
