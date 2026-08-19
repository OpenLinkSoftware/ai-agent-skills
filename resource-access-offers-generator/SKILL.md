---
name: resource-access-offers-generator
description: "Generate RDF Turtle offer/license/price bundles for File Access, Graph Access, API Access, and Chat Service products. Trigger on phrases like 'generate offers', 'create license bundle', 'make a file access offer', 'generate graph access offer', 'create API access offers', 'create chat service offers', or any request to produce resource-access offers in Turtle format."
---
# Resource Access Offers Generator
Generate valid RDF Turtle documents containing File Access, Graph Access, API Access, or Chat Service offers.
## Minimum Input Requirements
| Input | Required | Example |
|-------|----------|---------|
| License resource IRI | Yes (not for Chat Service — see its own section) | URL of protected file/graph |
| Price | Yes | `2.99` |
| Description | Yes | Free text — name/prefLabel/comment auto-derived |
| Host platform | No (default: URIBurner) | `linkeddata.uriburner.com` |
## Host Platform Profiles
URIBurner (`linkeddata.uriburner.com`), ODS-QA (`ods-qa.openlinksw.com`), Localhost (`localhost`)
## Workflow
1. Elicit offer type (file/graph/api/chatservice), host, license IRI, price, description
2. Derive name, prefLabel, comment from description
3. Load prompt template from `prompts/`
4. Substitute placeholders, generate Turtle
5. Validate syntax (rdflib), validate SHACL (`scripts/validate-offers-shacl.py`)
6. Run Post-Generation Checklist, save to `/Users/jacqui/source/ttl/my_git_forks/virtuoso-82-offers-description/` (default output directory for all generated offer files), provide loading instructions
## Document Metadata Block (source:)
Immediately after the `@prefix` declarations, every generated file MUST open with a `schema:CreativeWork` block describing **the Turtle file being generated itself** — never the licensed resource (file/graph/API being sold). Declare:
```turtle
@prefix source: <http://virtuoso.openlinksw.com/data/turtle/{output-filename}> .
@prefix :       <#> .

source: a schema:CreativeWork ;
    schema:name "{Document title}" ;
    schema:description "{What this document's offers cover}" ;
    schema:author <http://www.openlinksw.com/#this> ;
    cc:attributionName "OpenLink Software" ;
    schema:datePublished "{dateTime}"^^xsd:dateTime ;
    schema:dateModified "{dateTime}"^^xsd:dateTime .
```
`{output-filename}` is the actual filename this Turtle file will be saved as (matching the convention in the two prior art files: `http://virtuoso.openlinksw.com/data/turtle/FileAccessOffers-License-Prices.ttl`, `http://virtuoso.openlinksw.com/data/turtle/OPALOffers-Licenses-Prices-ods-qa-SPARQL-API.ttl`) — this host/path is fixed regardless of which host platform profile the licensed resource lives on.
Every generated Offer, License, and PriceSpecification node MUST carry `wdrs:describedby source:` pointing at this document node — that relation is what "identifies" the document as their source. The licensed resource itself is never separately described as a `schema:CreativeWork` — it's referenced only via `opllic:uriParameter`/`opllic:graphParameter`. The SHACL gate enforces `wdrs:describedby` (`sh:class schema:CreativeWork`) as required on Offer, License, and PriceSpecification shapes, and `DocumentShape` requires `schema:name`/`schema:author`/`schema:datePublished`/`schema:dateModified` on whatever node that resolves to.
## Entity IRI Naming Convention
The Offer, License, and PriceSpecification each get their own dedicated path segment — see `references/offer-iri-patterns.md` for the full template table and `host_suffix` derivation:
- PriceSpecification: `http://data.openlinksw.com/oplweb/offer-unitprice/{OfferIdentifier}PriceSpecification#this` — no host suffix.
- License: `http://data.openlinksw.com/oplweb/license/{OfferIdentifier}License{host_suffix}#this`
- Offer: `http://data.openlinksw.com/oplweb/offer/{OfferIdentifier}Offer{host_suffix}#this`

`{OfferIdentifier}` is a PascalCase name for the specific thing being offered (e.g. `DataTwinglerSpecificModuleEntryLevel`), derived from the offer's subject — not an ad-hoc slug and not reusing the Product's IRI shape. `{host_suffix}` is `host_short` with its first letter capitalized (`URIBurner` → `URIBurner`, `ods-qa` → `Ods-qa`, `localhost` → `Localhost`). The SHACL gate enforces the path segment and substring for each (`sh:pattern` on the shape itself, checked against the focus node's own IRI) — an Offer/License/PriceSpecification IRI that doesn't follow this shape now fails, even if every other property is correct.
## File Access Product (WebAPI) Description Template
The Product node for a **File Access** offer MUST follow this full template — not a minimal stub:
```turtle
<http://data.openlinksw.com/oplweb/{host_short}FA#this> a schema:WebAPI ;
    schema:name "File access via {host_short}"@en ;
    schema:applicationCategory "File Access"@en ;
    schema:applicationSubCategory "ACL controlled file access"@en ;
    schema:description """Attribute-based, access control constrained access to a File hosted by {host_hostname}."""@en ;
    skos:related <http://data.openlinksw.com/oplweb/{host_short}OPAL#this> ;
    schema:provider [
        a schema:Organization ;
        schema:name "OpenLink Software"@en ;
        schema:url <https://www.openlinksw.com/> ;
    ] ;
    schema:url <https://{host_hostname}/> ;
    schema:hasPart [
        a schema:WebAPI ;
        schema:name "WebDAV Service Endpoint"@en ;
        schema:description """WebDAV Endpoint for file interactions."""@en ;
        schema:serviceType "WebDAV Service"@en ;
        schema:url <https://{host_hostname}/DAV>
    ] .
```
Notes:
- All the literal values shown (`"File Access"@en`, `"ACL controlled file access"@en`, `"WebDAV Service"@en`) are fixed conventions, including the `@en` language tag — the gate checks exact term equality, so a plain string without the tag fails.
- `schema:url` on the top-level Product is the **host root** (`https://{host_hostname}/`), not the `/DAV` path — the `/DAV` endpoint belongs to the nested `schema:hasPart` sub-resource's `schema:url`.
- `skos:related` points at the OPAL ACL server Product (`http://data.openlinksw.com/oplweb/{host_short}OPAL#this`, see `references/offer-iri-patterns.md`) — required because an OPAL server is what actually creates the ACLs backing file access.
- The SHACL gate targets this shape via `sh:targetSubjectsOf schema:applicationCategory` rather than `sh:targetClass schema:WebAPI` — the nested WebDAV sub-resource is also `a schema:WebAPI` but has no `schema:applicationCategory`, so it's correctly excluded from this shape and validated only by its own (lighter) constraints (`schema:name`, `schema:description`, `schema:serviceType "WebDAV Service"@en`, `schema:url`).
## Graph Access Product (WebAPI+Service) Description Template
The Product node for a **Graph Access** offer MUST follow this full template — not a minimal stub. It mirrors the File Access template one-for-one, substituting the SPARQL/knowledge-graph vocabulary:
```turtle
<http://data.openlinksw.com/oplweb/{host_short}DA#this> a schema:WebAPI, schema:Service ;
    schema:name "Knowledge graph access via {host_short}"@en ;
    schema:applicationCategory "Data Access"@en ;
    schema:applicationSubCategory "ACL controlled knowledge graph access"@en ;
    schema:description """Attribute-based, access control constrained SPARQL access to a named graph hosted by {host_hostname}."""@en ;
    skos:related <http://data.openlinksw.com/oplweb/{host_short}OPAL#this> ;
    schema:provider [
        a schema:Organization ;
        schema:name "OpenLink Software"@en ;
        schema:url <https://www.openlinksw.com/> ;
    ] ;
    schema:url <https://{host_hostname}/> ;
    schema:hasPart [
        a schema:WebAPI ;
        schema:name "SPARQL Query Service Endpoint"@en ;
        schema:description """HTTP SPARQL Query Service Endpoint providing access to the named graph."""@en ;
        schema:serviceType "SPARQL Query Service"@en ;
        schema:url <https://{host_hostname}/sparql>
    ] .
```
Notes (identical reasoning to the File Access template, see `references/offer-iri-patterns.md` for the `{host_short}DA#this` / `{host_short}OPAL#this` IRI patterns):
- Fixed-convention literals (`"Data Access"@en`, `"ACL controlled knowledge graph access"@en`, `"SPARQL Query Service"@en`) all need the `@en` tag — exact term equality.
- `schema:url` on the top-level Product is the **host root**, not `/sparql` — the SPARQL endpoint path belongs on the nested `schema:hasPart` sub-resource's `schema:url`.
- The Product is typed **both** `schema:WebAPI` and `schema:Service` (unlike File Access, which is `schema:WebAPI` only).
- Same `sh:targetSubjectsOf schema:applicationCategory` scoping trick as File Access — the nested SPARQL sub-resource is also `a schema:WebAPI` but has no `applicationCategory`, so it's excluded from this shape and validated only by its own lighter nested constraints.
- The License's `opllic:graphParameter` should be the actual named graph IRI being sold access to (e.g. `urn:jch:test`), not the SPARQL endpoint URL — the endpoint URL belongs on the Product's `hasPart` sub-resource. A sample `opllic:uriParameter` query URL scoping `default-graph-uri` to that graph is good practice (see the two prior-art reference files) but not gate-enforced.
## Graph Access Authorization Block (ConditionalGroup + acl:Authorization)
Every generated **Graph Access** offer file MUST also include, in the same output file, a self-contained authorization block granting the purchaser actual read access to the sold graph — otherwise the offer/license/price bundle exists but nothing enforces it. This mirrors the pattern in the prior-art `Offers-authorizations-and-restrictions.ttl` (see `oplacl:demo-graph-access-world-cup-meshup` / `<.../group/DemoGraphAccessUsersWorldCupMeshup#this>`), reusing the same `oplofr:{OfferIdentifier}Offer` resource-specific type from the Entity IRI/Type conventions above as the purchase-check predicate:
```turtle
<http://data.openlinksw.com/oplweb/group/{OfferIdentifier}GraphAccessUsers#this> a oplacl:ConditionalGroup ;
    foaf:name "Users identified using a NetID based Identifier who have purchased the {offer name} offer and whose license is in date" ;
    oplacl:hasCondition [
        a oplacl:GroupCondition, oplacl:QueryCondition ;
        oplacl:hasQuery """prefix oplprchs: <http://www.openlinksw.com/ontology/purchases#>
          prefix opllic:  <http://www.openlinksw.com/ontology/licenses#>
          prefix oplofr:  <http://www.openlinksw.com/ontology/offers#>
          prefix schema:  <http://schema.org/>
          prefix oplshop: <http://www.openlinksw.com/ontology/shop#>
          prefix owl:     <http://www.w3.org/2002/07/owl#>
          ask where {
            { graph <urn:openlinksw.com.shop:registry> { ?shop oplshop:hasPurchaseCache ?cg } }
            union
            { bind(<urn:openlinksw.com:shop:purchases:cache> as ?cg) }
            graph ?cg {
              { ^{uri}^ oplprchs:madePurchase ?purchase . }
              union
              { ?o owl:sameAs ^{uri}^ ; oplprchs:madePurchase ?purchase . }
              ?purchase oplprchs:contains ?offer ;
                        oplprchs:purchaseDate ?purchaseDate .
              ?offer a oplofr:{OfferIdentifier}Offer ;
                     schema:itemOffered ?license .
              ?license opllic:hasDuration ?duration .
              optional {?duration opllic:durationYears ?years .}
              filter ((?duration like <http://data.openlinksw.com/oplweb/license/License-Duration#ongoing-subscription> ) or
                      (bif:dateadd ('day', xsd:integer(?years) * 365, ?purchaseDate) > bif:now()) ) .
            }
          }"""
    ] .

<http://data.openlinksw.com/oplweb/acl/{OfferIdentifier}GraphAccess#this> a acl:Authorization ;
    schema:name "Rule to allow access to the <{graph IRI}> graph" ;
    acl:accessTo <{graph IRI}> ;
    oplacl:hasAccessMode oplacl:Read ;
    oplacl:hasRealm oplacl:DefaultRealm ;
    oplacl:hasScope oplacl:PrivateGraphs ;
    acl:agent <http://data.openlinksw.com/oplweb/group/{OfferIdentifier}GraphAccessUsers#this> ;
    wdrs:describedby source: .
```
Notes:
- `{graph IRI}` in `acl:accessTo` MUST be the exact same IRI as the License's `opllic:graphParameter` — this is what actually ties the purchase to real access. The SHACL gate enforces this cross-link with a `sh:sparql` constraint on `GraphAccessOfferShape`: it fails if no `acl:Authorization` exists with `acl:accessTo` equal to the Offer's License's `graphParameter` and `oplacl:hasAccessMode oplacl:Read`.
- The embedded SPARQL `ASK` query text inside `oplacl:hasQuery` is NOT gate-validated for content (it's a plain string literal, and string-matching against arbitrarily-formatted embedded SPARQL would be too fragile) — get the `oplofr:{OfferIdentifier}Offer` reference right by hand, matching the resource-specific type actually used on the Offer.
- `oplacl:ConditionalGroup` (needs `foaf:name` and `oplacl:hasCondition`/`oplacl:GroupCondition`/`oplacl:hasQuery`) and `acl:Authorization` (needs `acl:accessTo`, `oplacl:hasAccessMode oplacl:Read`, `oplacl:hasRealm oplacl:DefaultRealm`, `oplacl:hasScope oplacl:PrivateGraphs`, `acl:agent` pointing at the group, `wdrs:describedby`) are both independently gate-enforced as structural shapes.
- The prior-art reference file also includes an additional `filter (sql:stripe_customer_has_active_product_subscription(...))` clause for Stripe-backed recurring subscriptions — include it when the offer is a recurring subscription (see Subscription Pricing above), matching the style of `oplacl:demo-graph-access-world-cup-meshup`'s group condition.
- This authorization block is currently required for **Graph Access offers only** (per explicit scope decision) — File Access and API Access offers don't need it yet.
## API Access Product (WebAPI) Description Template + 4-Tier Offer Structure
Unlike File/Graph Access (one specific resource per offer), an **API Access** offer file describes ONE shared OPAL Chat API Product per host, sold as **exactly 4 separate Offer/License/PriceSpecification triples** — Entry (free), Medium ($9.99/mo), Advanced ($19.99/mo), Max ($49.99/mo) — all sharing the same Product. This matches the two dedicated prior-art files (`OPALOffers-Licenses-Prices-ODS-QA-API.ttl`, `OPALOffers-Licenses-Prices-URIBurner-API.ttl`). There is no user-supplied "resource identifier" the way File/Graph Access needs one — the tier names themselves (`ApiAccessEntryLevel` / `ApiAccessMediumLevel` / `ApiAccessAdvancedLevel` / `ApiAccessMax`) ARE the `{OfferIdentifier}` for each of the 4 offers.
Product template (one per host, shared across all 4 tiers):
```turtle
<http://data.openlinksw.com/oplweb/{host_short}OPAL-API#this> a schema:WebAPI ;
    schema:name "OPAL Chat API via {host_short}"@en ;
    schema:description """API endpoint for interacting with OPAL on {host_short}, enabling programmatic Machine-Centric Programming (MCP) chat sessions."""@en ;
    schema:serviceType "MCP-compliant AI Chat Agent API"@en ;
    schema:url <https://{host_hostname}/chat/api> ;
    skos:related <http://data.openlinksw.com/oplweb/{host_short}OPAL#this> ;
    schema:provider [
        a schema:Organization ;
        schema:name "OpenLink Software"@en ;
        schema:url <https://www.openlinksw.com/> ;
    ] ;
    schema:documentation <https://opal.openlinksw.com/install/> ;
    schema:exampleOfWork <https://www.openlinksw.com/data//html/opal-system-functions-or-agents-apis-developer-journey-gemini-17.html> ;
    schema:hasPart [
        a schema:EntryPoint ;
        schema:name "OPAL Chat Endpoint" ;
        schema:urlTemplate "https://{host_hostname}/chat/api" ;
        schema:httpMethod "POST" ;
        schema:contentType "application/json" ;
        schema:actionPlatform <http://schema.org/OnlinePlatform>
    ] ;
    schema:potentialAction [
        a schema:CommunicateAction ;
        schema:name "SendMessage" ;
        schema:target [
            a schema:EntryPoint ;
            schema:urlTemplate "https://{host_hostname}/chat/api" ;
            schema:httpMethod "POST"
        ] ;
        schema:expects [ a schema:Text ; schema:description "JSON payload containing message content and metadata for OPAL" ] ;
        schema:result [ a schema:Text ; schema:description "JSON response containing the OPAL chat reply or status" ]
    ] .
```
Each of the 4 tiers is its own Offer/License/PriceSpecification, e.g. for Entry:
```turtle
<http://data.openlinksw.com/oplweb/offer/ApiAccessEntryLevelOffer{host_suffix}#this>
    a schema:Offer, oplofr:SubscriptionOffer, oplofr:ApiAccessEntryLevelOffer ;
    schema:itemOffered <http://data.openlinksw.com/oplweb/license/ApiAccessEntryLevelLicense{host_suffix}#this> ;
    schema:priceSpecification <http://data.openlinksw.com/oplweb/offer-unitprice/ApiAccessEntryLevelPriceSpecification#this> ;
    schema:url <https://{host_hostname}/chat/api> ;
    skos:prefLabel "OPAL API Access on {host_short} - Entry Level (BYOK)" ;
    ... (offerNumber, name, comment, description, businessFunction gr:Sell, isMemberOf OfferGroupApiAccess, validFrom/Through, potentialAction cart URL, wdrs:describedby — same as any other Offer) .

<http://data.openlinksw.com/oplweb/offer-unitprice/ApiAccessEntryLevelPriceSpecification#this>
    a schema:UnitPriceSpecification ;
    schema:priceCurrency "USD"^^xsd:string ;
    schema:price "0.00"^^xsd:decimal ;
    ... (validFrom/Through, wdrs:describedby — NO oplofr:interval/intervalCount, since Entry is free) .

<http://data.openlinksw.com/oplweb/license/ApiAccessEntryLevelLicense{host_suffix}#this>
    a opllic:ProductLicense, opllic:Product, opllic:ACLOnly, opllic:SubscriptionLicense ;
    opllic:productLicenseOf <http://data.openlinksw.com/oplweb/{host_short}OPAL-API#this> ;
    skos:related <https://{host_hostname}/oauth/applications.vsp> ;
    ... (name, description, prefLabel, image, partOf, hasDuration, OS/DB family, wdrs:describedby — same as any other License; NO opllic:uriParameter/graphParameter for API Access) .
```
The other 3 tiers (Medium $9.99, Advanced $19.99, Max $49.99) follow the identical structure with `oplofr:interval "month"^^xsd:string` + `oplofr:intervalCount "1"^^xsd:integer` added to their PriceSpecification (required for any non-$0.00 price — the gate enforces this pairing via `ApiAccessPaidPriceShape`'s `sh:or`).
Notes:
- `schema:image` on the License: prefer `<https://www.openlinksw.com/DAV/oplweb3/images/opal-license.png>` (the API-Access-specific convention from both prior-art files) over the generic fallback image.
- `schema:documentation` and `schema:exampleOfWork` are fixed, host-independent values (identical across both prior-art files) — the gate enforces them as exact matches.
- `skos:related` is required on both the Product (→ the host's OPAL server Product, same as File/Graph) and the License (→ the host's OAuth applications page, `https://{host_hostname}/oauth/applications.vsp`) — these are two different things despite the same predicate.
- Every Offer needs `skos:prefLabel` (gate-enforced for API Access specifically — this isn't required on Offers generally, only on Licenses).
- The tier types (`oplofr:ApiAccessEntryLevelOffer` etc.) already satisfy the universal "resource-specific offer type" rule on their own — no separate generic marker class is needed (unlike File/Graph's `DemoFileAccessOffer`/`DemoGraphAccessOffer` + resource-specific-type combo).
- **Bug fixed while building this out**: the pre-existing `ApiAccessPaidPriceShape` unconditionally required `oplofr:interval`/`intervalCount` on every API Access price, which would have wrongly rejected the free Entry tier. It's now conditional (`sh:or`: either price is exactly `"0.00"^^xsd:decimal`, or interval+intervalCount are present) — also fixed the interval value itself from a bare `"month"` to `"month"^^xsd:string` to match this skill's own established literal-typing convention (see priceCurrency rule below), which the bare form silently failed to match.
- **4-tier completeness gate**: `ApiAccessProductShape` includes a `sh:sparql` constraint requiring that, for the shared Product, all 4 tiers exist — a License with `opllic:productLicenseOf` this Product whose `opllic:partOf`-linked Offer is typed `oplofr:ApiAccessEntryLevelOffer`, another for `oplofr:ApiAccessMediumLevelOffer`, another for `oplofr:ApiAccessAdvancedLevelOffer`, another for `oplofr:ApiAccessMaxOffer`. Generating only some of the 4 tiers now fails the gate. **Note on SHACL-SPARQL**: `VALUES` clauses are disallowed inside `sh:sparql` constraints per the SHACL spec (confirmed via pyshacl: "A SPARQL Constraint must not contain a VALUES clause") — the check is written as a `UNION` of 4 separate `FILTER NOT EXISTS` branches instead. Checking by exact tier *type* (not price point) was a deliberate choice — the tier's identity is what matters, and prices are a business detail that could reasonably change later without affecting the invariant "all 4 tiers exist."
## Chat Service Product/License/Offer Description Template
Unlike the other three types, a **Chat Service** offer is NOT tied to a specific file/graph/API-endpoint resource — it sells interactive use of the OPAL AI agent platform itself (module-specific assistants, or generic Bring-Your-Own-Key/system-wide tiers). There is no "License resource IRI" input for this type. Structurally it is the most open-ended of the four: unlike API Access's rigid single-Product/4-fixed-tiers bundle, Chat Service can have an arbitrary number of independent **offer families** (e.g. Data Twingler, Support Assistant, generic BYOK/Max), each typically at 4 tiers (Entry/Plus/Pro/Max), all sharing ONE Product per host.
Product template (one per host, shared across every family/tier):
```turtle
<http://data.openlinksw.com/oplweb/{host_short}OPAL#this> a schema:Service ;
    schema:name "OPAL via {host_short}"@en ;
    schema:applicationCategory "AI Agent Platform"@en ;
    schema:applicationSubCategory "LLM-Integrated AI Agent Middleware"@en ;
    schema:description """OPAL (OpenLink AI Layer) instance hosted by {host_short}, enabling AI Agent interaction with Data Spaces using natural language and the MCP protocol."""@en ;
    schema:softwareVersion "1.0"@en ;
    schema:provider [ a schema:Organization ; schema:name "OpenLink Software"@en ; schema:url <https://www.openlinksw.com/> ] ;
    schema:url <https://{host_hostname}/> ;
    schema:hasPart
        [ a schema:WebAPI ; schema:name "OPAL Chat Endpoint"@en ; schema:description "..."@en ; schema:serviceType "MCP-compliant AI Chat Agent"@en ; schema:url <https://{host_hostname}/chat> ; schema:documentation <https://opal.openlinksw.com/install/> ; schema:termsOfService <https://opal.openlinksw.com/tos/> ],
        [ a schema:WebAPI ; schema:name "OPAL Assist-Metal Endpoint"@en ; schema:description "..."@en ; schema:serviceType "MCP-compliant AI Assist Agent"@en ; schema:url <https://{host_hostname}/assist-metal> ; schema:documentation <https://opal.openlinksw.com/install/> ; schema:termsOfService <https://opal.openlinksw.com/tos/> ],
        [ a schema:WebAPI ; schema:name "MCP Server (Streamable HTTP)"@en ; schema:description "..."@en ; schema:serviceType "MCP Server (Streamable HTTP)"@en ; schema:url <https://{host_hostname}/chat/mcp/messages> ; schema:documentation <https://opal.openlinksw.com/install/> ; schema:termsOfService <https://opal.openlinksw.com/tos/> ],
        [ a schema:WebAPI ; schema:name "MCP Server (Server Sent Events)"@en ; schema:description "..."@en ; schema:serviceType "MCP Server (SSE)"@en ; schema:url <https://{host_hostname}/chat/mcp/sse> ; schema:documentation <https://opal.openlinksw.com/install/> ; schema:termsOfService <https://opal.openlinksw.com/tos/> ] .
```
This is the same shared `{host_short}OPAL#this` IRI already documented in `references/offer-iri-patterns.md` as the OPAL ACL server referenced via `skos:related` from File/Graph/API Access Products — here it plays its **primary** role, as the licensed Product itself.
Each tier (of each family) is a standard Offer/License/PriceSpecification triple with `oplofr:isMemberOf <http://data.openlinksw.com/oplweb/OfferGroupChatService#this>`, `opllic:productLicenseOf` pointing at the shared `{host_short}OPAL#this` node, and its own resource-specific `oplofr:{OfferIdentifier}Offer` type (e.g. `oplofr:DataTwinglerSpecificModuleEntryLevelOffer`, `oplofr:BringYourOwnKeyPlusOffer`, `oplofr:MaxOffer`). Unlike API Access, the Offer does NOT carry `schema:url` directly (only the Product/its `hasPart` sub-resources do).
Notes:
- `schema:hasPart` requires (gate-enforced) all 4 named sub-endpoints present — Chat, Assist-Metal, MCP Streamable HTTP, MCP SSE — confirmed identical across both prior-art host files (only the URL host differs). Uses `sh:qualifiedValueShape`/`sh:qualifiedMinCount` (one clause per required `serviceType`) rather than a rigid `hasPart` count, so adding a 5th endpoint later won't break the shape.
- `schema:image` on the License: same `opal-license.png` convention as API Access.
- License does NOT need `skos:related` (unlike API Access's OAuth-applications-page requirement) — Chat Service licenses in prior art don't carry it.
- Every Offer needs `skos:prefLabel` (same as API Access — not required on Offers generally).
- **No completeness gate for the multi-family structure** (deliberately, this round): unlike API Access's fixed single bundle, Chat Service's open-ended family/tier structure doesn't map cleanly onto a fixed exclusion-list or fixed-class SPARQL check. If a future request wants "all 4 tiers of a given family must exist," that's a natural follow-up, matching how Graph Access's authorization block and API Access's completeness gate were each separately requested after their initial template work.
- **Bugs fixed in the underlying prior-art file while building this out** (same due-diligence pass as the File/Graph/API Access work): one License (`BringYourOwnKeyProLicenseOds-qa`) was missing `opllic:partOf` entirely; all 12 offers' `schema:potentialAction` cart URLs were missing the `/shop/` path segment (`shop.openlinksw.com/cart.vsp` instead of `shop.openlinksw.com/shop/cart.vsp`) — both fixed when regenerating from this template.
- **Validation note**: `scripts/validate-offers-shacl.py --type chatservice` (or bare auto-detect) now validates against `chat-service-offer-shape.ttl` + `common-offer-shape.ttl`.
## Auto-Derivation
- name: First sentence ≤80 chars
- pref_label: Abbreviated ≤60 chars
- comment: "Purchasing this offer grants {description}"
- description: The Offer node MUST also carry its own `schema:description` (distinct from `schema:comment` above) — required, e.g. "{Offer type} offer providing {description}." Omitting it is not just a SHACL gate failure: `OPLSHOP.DBA.offers_sparql_base()` in the live shop's `opl_shop_offer_ui.sql` requires `schema:description` as a non-optional triple in its main catalog listing query — an Offer without it is silently excluded from every offer listing in the shop, even though nothing else about the file is wrong.
- itemOffered: `schema:itemOffered` on the Offer MUST point at the **License** IRI (the `opllic:ProductLicense` node), never at the Product (the `schema:WebAPI` node). The shop's detail-population queries (`get_offer_info`, `get_offer_dbms_info`, `get_subscription_info`, `get_eval_action`, `get_service_uri` in `opl_shop_offer_ui.sql`) all do `?offer schema:itemOffered ?lic` and then read License-only properties off `?lic` (`schema:image`, `oplsof:hasOperatingSystemFamily`, `opllic:productLicenseOf`, `opllic:hasDuration`, ...). Pointing `itemOffered` at the Product instead makes every one of those AJAX calls return empty, breaking the offer card's detail rendering even if the offer otherwise appears in the catalog list.
- duration: If price is a recurring monthly price ("per month"), `opllic:hasDuration` MUST be the canonical `<http://data.openlinksw.com/oplweb/license/License-Duration#ongoing-subscription>` IRI (see `references/offer-iri-patterns.md`) — never invent/type a local Duration node.
- potentialAction: `schema:potentialAction` on the Offer MUST always be a direct "add to cart" IRI on the production shop, **regardless of which host platform profile the licensed resource itself lives on** (URIBurner, ODS-QA, Localhost — the cart is always `shop.openlinksw.com`): `https://shop.openlinksw.com/shop/cart.vsp?command=add&item={percent-encoded Offer IRI}`. Percent-encode the full Offer IRI (`:` → `%3A`, `/` → `%2F`, `#` → `%23`) as the `item` value. Never emit a blank-node `schema:Action`/`EntryPoint` structure — the shop's listing query reads `schema:potentialAction` as a flat triple and expects the value itself to be the clickable cart URL.
- subscription pricing: Whenever the input price is phrased as "per <unit>" (per month, per year, ...) — i.e. it recurs on a billing cadence rather than being a one-time charge — the PriceSpecification MUST carry `oplofr:interval "<unit>"^^xsd:string` (e.g. `"month"`) and `oplofr:intervalCount "<n>"^^xsd:integer` (e.g. `1`), and the Offer MUST carry an additional `rdf:type oplofr:SubscriptionOffer` alongside `schema:Offer` and the offer-type-specific classes (`oplofr:DAVOffer`/`oplofr:DemoFileAccessOffer` etc.). One-time, non-recurring prices carry neither `oplofr:interval` nor the `SubscriptionOffer` type. The SHACL gate enforces the pairing both ways: a PriceSpecification with `oplofr:interval` but no `oplofr:intervalCount` fails, and an Offer whose price has `oplofr:interval` but isn't typed `oplofr:SubscriptionOffer` fails.
- validity: Unless the user gives an explicit validity window, default `schema:validFrom` on **both** the Offer and its PriceSpecification to the file's creation date/time (the same instant used for the `source:` document's `schema:datePublished`), and default `schema:validThrough` to exactly 3 months after that. Keep the Offer's and the PriceSpecification's validity window identical to each other unless told otherwise.
- image: The License MUST carry `schema:image`. If the user doesn't specify a particular image for this offer, default to `<https://www.openlinksw.com/DAV/oplweb3/images/controlled-access-to-data-assets.jpg>`.
- license typing: Every License (File Access, Graph Access, or API Access — all three) MUST be typed with all four classes, not just `opllic:ProductLicense`: `a opllic:ProductLicense, opllic:Product, opllic:ACLOnly, opllic:SubscriptionLicense`. This applies regardless of whether the price is one-time or recurring. The SHACL gate checks each of the three extra types as an independent required value on `rdf:type` — a License missing any one of them fails, with a separate violation naming exactly which type is absent.
- priceCurrency literal form: `schema:priceCurrency` MUST always be written with an explicit `^^xsd:string` datatype annotation — `schema:priceCurrency "USD"^^xsd:string ;` — never the bare/plain form (`schema:priceCurrency "USD" ;`). This is a serialization convention only, not something the SHACL gate can check: a plain string and an explicitly-typed `"USD"^^xsd:string` are the same RDF term under RDF 1.1 simple-literal semantics, so `sh:datatype xsd:string` already accepts both and can't tell them apart. Get it right at generation time.
- resource-specific offer type: Every Offer (all three offer types) MUST carry an additional `rdf:type` in the `oplofr:` namespace named `oplofr:{OfferIdentifier}Offer` — specific to the resource being sold, not to the host serving it. `{OfferIdentifier}` is the exact same PascalCase identifier used in the Offer/License/PriceSpecification IRIs (see Entity IRI Naming Convention) — no `{host_suffix}`. Example: for the Offer at `.../offer/JchTestGraphOfferOds-qa#this` (selling access to `urn:jch:test`), add `oplofr:JchTestGraphOffer` alongside `schema:Offer`, `oplofr:DemoGraphAccessOffer`, `oplofr:SubscriptionOffer`. The SHACL gate enforces this on `BaseOfferShape` via a qualified value shape: at least one `rdf:type` value must be an `oplofr:` IRI ending in `Offer` that is NOT one of the known host-generic classes (`oplofr:DAVOffer`, `oplofr:DemoFileAccessOffer`, `oplofr:DemoGraphAccessOffer`, `oplofr:SubscriptionOffer`) — **if a new host-generic offer class is ever added (e.g. for API Access), add it to that exclusion list in `shacl/common-offer-shape.ttl`'s `BaseOfferShape`, or a real resource-specific offer would incorrectly satisfy the check by accident, or worse, a missing resource-specific type could go undetected.**
## GATE: 0 FAIL
`python3 scripts/validate-offers-shacl.py output.ttl --type {file|graph|api|chatservice}` — must pass before delivery.
## Loading into Shop
```sql
SPARQL define get:soft "no-sponge" LOAD <file:///path/to/output.ttl> INTO <urn:opl:shop:offering:sponging:cache:official> ;
```
## License
AGPL-3.0
