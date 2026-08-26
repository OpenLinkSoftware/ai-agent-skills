-- Register a site against a composite skin.
--
-- Replace before running via isql:
--   {SITE}       site shortname in the config graph
--   {BASEURL}    site's ABSOLUTE public prefix, e.g. https://www.openlinksw.com/
--                (NOT a bare path — config_url_to_site matches it with
--                 fn:starts-with against the full request URL)
--   {DAVBASE}    site's DAV base collection, e.g. /DAV/www2.openlinksw.com
--   {MANIFEST}   DAV path to skin.ttl, e.g. /DAV/VAD/opl-skins/{skin}/skin.ttl
--   {SKINCOL}    the bundle's DAV collection, e.g. /DAV/VAD/opl-skins/{skin}/
--   {ASSETPATH}  vdir lpath matching the manifest's osdi:assetBase, e.g. /skin-{skin}
--   {SITEGRAPH}  named graph the manifest's SPARQL is scoped to
--
-- Elicit every one of these from the user or from the live config graph.
-- Documentation examples are NOT live values.
--
-- Prerequisite: the bundle and the site's content/ are already in WebDAV, and
-- the site's RDF is loaded into {SITEGRAPH}.

use incleng;

-- ---------------------------------------------------------------------------
-- 1. Site record. config_add_site INSERTS rather than updates and swallows
--    errors, so re-registering an existing site would leave two foaf:homepage
--    triples. Remove the old one first.
-- ---------------------------------------------------------------------------
sparql delete from <urn:com.openlinksw.virtuoso.incleng>
 { <urn:com.openlinksw.virtuoso.incleng:s:{SITE}> <http://xmlns.com/foaf/0.1/homepage> ?o }
 where { <urn:com.openlinksw.virtuoso.incleng:s:{SITE}> <http://xmlns.com/foaf/0.1/homepage> ?o };

incleng..config_add_site('{SITE}', '{BASEURL}', '{DAVBASE}');

-- ---------------------------------------------------------------------------
-- 2. Composite skin binding. skin_manifest overrides xslt_sheet for this scope.
-- ---------------------------------------------------------------------------
incleng..config_set(null, '{SITE}', 'skin_manifest', '{MANIFEST}');
incleng..config_set(null, '{SITE}', 'site_graph',    '{SITEGRAPH}');
incleng..config_set(null, '{SITE}', 'regions_off',   '');

-- ---------------------------------------------------------------------------
-- 3. Site-shape settings. Adjust to the site, do not apply blindly.
--    url_trailing_slash 0 is required for a site presenting .html URLs.
--    inline_html5md/inline_rdfa emit visible placeholder prose on pages the
--    site graph says nothing about.
-- ---------------------------------------------------------------------------
incleng..config_set(null, '{SITE}', 'url_trailing_slash', 0);
incleng..config_set(null, '{SITE}', 'inline_html5md', 0);
incleng..config_set(null, '{SITE}', 'inline_rdfa', 0);
-- incleng..config_set(null, '{SITE}', 'tidy', 0);   -- only if content is already XHTML

-- ---------------------------------------------------------------------------
-- 4. Bundle readability. Files PUT over WebDAV are owned by the uploading
--    account and are NOT world-readable, so a browser fetching the stylesheet
--    gets 401 rather than 200 — a failure the markup looks perfectly fine for.
-- ---------------------------------------------------------------------------
update ws..sys_dav_res set RES_PERMS = '111101101NN'
 where RES_FULL_PATH like '{SKINCOL}%';
update ws..sys_dav_col set COL_PERMS = '111101101NN'
 where COL_FULL_PATH like '{SKINCOL}%';

-- ---------------------------------------------------------------------------
-- 5. Parse the manifest into its own graph. THIS IS THE MANIFEST DEPLOYMENT
--    STEP — re-run it after every skin.ttl edit.
-- ---------------------------------------------------------------------------
select incleng..osdi_skin_load('{MANIFEST}') as manifest_triples;

-- ---------------------------------------------------------------------------
-- 6. Asset vdir. Its lpath must equal the manifest's osdi:assetBase. Do not
--    assume /skin is free: on a stock instance it resolves to different
--    collections on the plain and SSL vhosts.
-- ---------------------------------------------------------------------------
DB.DBA.VHOST_REMOVE(lpath=>'{ASSETPATH}');
DB.DBA.VHOST_DEFINE(lpath=>'{ASSETPATH}', ppath=>'{SKINCOL}', is_dav=>1,
                    vsp_user=>'dba');

-- ---------------------------------------------------------------------------
-- 7. Clear compiled XSLT and the page cache. config_flush_cache() alone is not
--    sufficient — the composer is XSLT and Virtuoso caches it compiled.
-- ---------------------------------------------------------------------------
select incleng..staleall() as xslt_cache_cleared;
select incleng..config_flush_cache() as page_cache_flushed;

-- ---------------------------------------------------------------------------
-- 8. Verify. Confirm the resolved values, then load a page IN A BROWSER —
--    markup can diff clean while the stylesheet 401s or a debug trailer
--    renders as visible text.
-- ---------------------------------------------------------------------------
select incleng..config_get(null, '{SITE}', 'skin_manifest') as manifest;
select incleng..config_get(null, '{SITE}', 'site_graph') as site_graph;
select incleng..site2baseurl('{SITE}') as base_url;
select incleng..osdi_url_slug('{BASEURL}index', incleng..site2baseurl('{SITE}')) as slug_of_root;

-- Teardown
-- incleng..config_unset(null, '{SITE}', 'skin_manifest');
-- incleng..config_unset(null, '{SITE}', 'site_graph');
-- incleng..config_unset(null, '{SITE}', 'regions_off');
-- select incleng..staleall();
