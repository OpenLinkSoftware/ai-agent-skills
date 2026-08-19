# Offer IRI Patterns
## Platform Profiles
| Profile | host_hostname | host_short | host_suffix |
|---------|---------------|------------|--------------|
| URIBurner | linkeddata.uriburner.com | URIBurner | URIBurner |
| ODS-QA | ods-qa.openlinksw.com | ods-qa | Ods-qa |
| Localhost | localhost | localhost | Localhost |
`host_suffix` = `host_short` with its first letter capitalized — used only in Offer/License IRIs (see below), never in Product IRIs.
## IRI Templates
- Product (File): http://data.openlinksw.com/oplweb/{host_short}FA#this
- Product (Graph): http://data.openlinksw.com/oplweb/{host_short}DA#this
- Product (API): http://data.openlinksw.com/oplweb/{host_short}OPAL-API#this
- Product (OPAL server / Chat Service): http://data.openlinksw.com/oplweb/{host_short}OPAL#this — dual role: the **primary** licensed Product for Chat Service offers, and the OPAL ACL server referenced via `skos:related` from File/Graph/API Access Products.
- OfferGroup (File): http://data.openlinksw.com/oplweb/OfferGroupFileAccess#this
- OfferGroup (Graph): http://data.openlinksw.com/oplweb/OfferGroupGraphAccess#this
- OfferGroup (API): http://data.openlinksw.com/oplweb/OfferGroupApiAccess#this
- OfferGroup (Chat Service): http://data.openlinksw.com/oplweb/OfferGroupChatService#this
- PriceSpecification: http://data.openlinksw.com/oplweb/offer-unitprice/{OfferIdentifier}PriceSpecification#this — no `host_suffix`; a price spec may be shared across multiple offers/hosts. Example: `http://data.openlinksw.com/oplweb/offer-unitprice/DataTwinglerSpecificModuleEntryLevelPriceSpecification#this`
- License (opllic:ProductLicense): http://data.openlinksw.com/oplweb/license/{OfferIdentifier}License{host_suffix}#this. Example: `http://data.openlinksw.com/oplweb/license/DataTwinglerSpecificModuleEntryLevelLicenseOds-qa#this`
- Offer (schema:Offer): http://data.openlinksw.com/oplweb/offer/{OfferIdentifier}Offer{host_suffix}#this. Example: `http://data.openlinksw.com/oplweb/offer/DataTwinglerSpecificModuleEntryLevelOfferOds-qa#this`

`{OfferIdentifier}` is a PascalCase identifier naming the specific thing being offered (e.g. `DataTwinglerSpecificModuleEntryLevel`) — derive it from the offer's subject/description, not from the host or offer type. The SHACL gate enforces the `/offer-unitprice/`, `/license/`, `/offer/` path segments and the `PriceSpecification`/`License`/`Offer` substrings via `sh:pattern` directly on each shape (matched against the focus node's own IRI) — the old ad-hoc scheme (e.g. `http://data.openlinksw.com/oplweb/ods-qaFA-Foo-Offer#this`, with no `/offer/` path segment) now fails.
## Duration IRIs
Canonical, pre-existing `opllic:Duration` resources — reference by IRI only, never define/type a local Duration node.
| Billing Period | opllic:hasDuration IRI |
|---|---|
| Monthly (recurring "per month" price) | http://data.openlinksw.com/oplweb/license/License-Duration#ongoing-subscription |
