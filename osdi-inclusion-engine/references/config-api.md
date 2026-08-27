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
| `skin_manifest` | DAV path to a composite skin's `skin.ttl`. **Setting this switches the scope to composite rendering and overrides `xslt_sheet`** |
| `site_graph` | Named graph a composite skin's SPARQL bindings are scoped to — what lets one skin dress several sites |
| `regions_off` | Comma-delimited composite-skin region names to omit for this scope (per-page chrome suppression) |
| `url_trailing_slash` | 1 (default) canonicalises every request to a trailing slash. **Set 0 for a site presenting `.html` URLs**, or every request 302s |
| `tidy` | 0 skips the HTML Tidy pass — correct when content is already well-formed XHTML |
| `inline_html5md` / `inline_rdfa` | >0 embeds HTML-Microdata / RDFa islands. With no statements about a page these emit **visible placeholder prose**; set 0 unless the site graph describes its pages |

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

### `?skin=` — the per-impression override

Not a config parameter, but it resolves ahead of every one of them. `?skin=<name>` selects a bundle under `/DAV/VAD/opl-skins/`: a legacy skin if the directory has `xslt/PostProcess.xslt`, a composite one if it has `skin.ttl`. Either **overrides `skin_manifest`**, so a composite site remains previewable under any other skin. See `references/composite-skins.md`.

```sql
incleng..skin_param_to_xslt(in skin varchar)      -- -> legacy PostProcess.xslt, or null
incleng..skin_param_to_manifest(in skin varchar)  -- -> composite skin.ttl, or null
```

## Composite Skin Functions

Defined in `inclusion-engine/common/skin-api.sql`. See `references/composite-skins.md` for the manifest vocabulary these read.

```sql
-- Parse skin.ttl into urn:osdi:skin:{manifest}. Idempotent (clears first).
-- RE-RUN AFTER EVERY MANIFEST EDIT — this is the manifest deployment step.
incleng..osdi_skin_load(in manifest varchar)

-- The three XML trees handed to the generic composer.
incleng..osdi_skin_theme(in manifest varchar)                   -- <skintheme>
incleng..osdi_skin_templates(in manifest varchar)               -- <skintemplate>
incleng..osdi_skin_data(in manifest varchar, in site_graph varchar,
                        in url varchar, in slug varchar)        -- <skindata>

-- Helpers
incleng..osdi_skin_layout(inout skindata any, in dflt varchar := 'default')
incleng..osdi_url_slug(in url varchar, in sitebase varchar)
incleng..osdi_skin_graph(in manifest varchar)
incleng..osdi_skin_dir(in manifest varchar)
```

A manifest edit needs BOTH `osdi_skin_load()` and `staleall()`: the first re-parses the manifest, the second clears Virtuoso's compiled-XSLT cache. `config_flush_cache()` alone is not sufficient for either.

### Site registration caveats

`config_add_site(sname, baseURL, webdavbase)` writes the site into the config graph but has a blanket `exit handler` that returns null on any error, and it **inserts** rather than updates — re-running it on an existing site adds a second `foaf:homepage` triple instead of replacing the first. Delete the old triple before re-registering.

`baseURL` must be the **absolute** public prefix (`http://host:port/path/`), not a bare path: `config_url_to_site` matches it with `fn:starts-with` against the full request URL, and `url_davfile` strips it from the URL to derive the content path. A path-only value silently yields a mangled DAV path.

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
