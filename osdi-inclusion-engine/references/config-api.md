# OSDI Config API Reference

All configuration lives in the quadstore graph `<urn:com.openlinksw.virtuoso.incleng>`. The legacy `incleng..sites` table is obsolete (migration helper: `incleng..config_migrate(dangerous)`); never write to it.

## Graph Structure

- **Sites**: subjects `urn:com.openlinksw.virtuoso.incleng:s:{shortname}`, type `sioc:Site`, with `rdfs:label` (shortname), `foaf:homepage` (base URL), and `iecp:webdav_base` where `iecp:` = `urn:com.openlinksw.virtuoso.incleng:p:`.
- **Global settings**: subject `urn:com.openlinksw.virtuoso.incleng:incl.eng` with `iecp:` properties.
- **Per-URL / per-site overrides**: the same `iecp:` properties asserted with a request URL or site subject.

## Parameters

| Param | Meaning |
|---|---|
| `xslt_sheet` | `virt://WS.WS.SYS_DAV_RES.RES_FULL_PATH.RES_CONTENT:/DAV/VAD/inclusion-engine/skin/{skin}/xslt/PostProcess.xslt` |
| `webdav_base` | Site's DAV base collection (site-scoped) |
| `debug_level` | >0 → console debug logging |
| `notfoundurl` | Redirect target on 404 (e.g. `/404.vsp`) |
| `inline_ttl` / `inline_jsonld` | >0 → embed Turtle / JSON-LD data island per page |
| `search_graphs` | Space-separated graph IRIs searched for page metadata |
| `search_requrl` | 1 → also search the request-URL-as-graph |
| `search_site_graphs` | 1 → also search all site homepages as graphs |
| `allow_edit` | DAV user's password to enable in-site editing (leave unset in production) |

## Functions

```sql
-- Site management
incleng..config_add_site(in sname varchar, in baseURL varchar, in webdavbase varchar)
incleng..config_remove_site(in sname varchar)

-- Parameter access; resolution order: requrl match → site match → global
incleng..config_get(in requrl varchar, in site varchar, in param any, in defval any := null)
incleng..config_set(in uri varchar, in site varchar, in param any, in pvalue any)
incleng..config_unset(in uri varchar, in site varchar, in param any)

-- Helpers
incleng..config_url_to_site(in requrl varchar, in davbase varchar := null)
incleng..config_flush_cache()
incleng..staleall()            -- flush compiled XSLT + cache table
incleng..config_propagate_index_vsp(user, password)   -- defaults 'dav'
incleng..config_migrate(in dangerous integer := 0)
```

`config_set` scoping: pass the **request URL** as `uri` for a per-URL override (site may still be passed for context); pass `null` uri + site shortname for site scope; `null`/`null` for global. `config_get` mirrors this in its lookup order, which is what makes a homepage-only skin override safe: every other page falls through to the site/global `xslt_sheet`.

## Ready-to-Run Inspection Queries (isql)

Enumerate registered sites:

```sql
SPARQL
SELECT ?s ?label ?home ?base
FROM <urn:com.openlinksw.virtuoso.incleng>
WHERE {
  ?s a <http://rdfs.org/sioc/ns#Site> ;
     <http://www.w3.org/2000/01/rdf-schema#label> ?label ;
     <http://xmlns.com/foaf/0.1/homepage> ?home .
  OPTIONAL { ?s <urn:com.openlinksw.virtuoso.incleng:p:webdav_base> ?base }
};
```

Dump the whole config graph:

```sql
SPARQL SELECT ?s ?p ?o FROM <urn:com.openlinksw.virtuoso.incleng> WHERE { ?s ?p ?o } ORDER BY ?s ?p;
```

Read a site's DAV base and the skin a given URL will resolve to:

```sql
select incleng..config_get(null, 'virtuoso', 'webdav_base');
select incleng..config_get('https://virtuoso.openlinksw.com/', 'virtuoso', 'xslt_sheet');
```

List existing per-URL `xslt_sheet` overrides (audit before adding more):

```sql
SPARQL
SELECT ?s ?o FROM <urn:com.openlinksw.virtuoso.incleng>
WHERE { ?s <urn:com.openlinksw.virtuoso.incleng:p:xslt_sheet> ?o } ;
```
