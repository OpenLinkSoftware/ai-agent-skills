# Loading Offers into the Shop Graph
```sql
SPARQL define get:soft "no-sponge"
LOAD <file:///path/to/generated-offers.ttl>
INTO <urn:opl:shop:offering:sponging:cache:official> ;
```
## Named Graphs
| Graph | Purpose |
|-------|---------|
| `<urn:opl:shop:offering:sponging:cache:official>` | Shop/cart offer registry |
| `<urn:data:openlink:products>` | Product catalog (SEO) |
| `<urn:mdata:websites:google:seo>` | Google SEO metadata |
