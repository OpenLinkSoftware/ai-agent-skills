-- OSDI skin override and region-suppression templates.
-- Replace {URL}, {SITE}, {SKIN}, {REGIONS} before running via isql.
-- Elicit {URL} and {SITE} from the live config graph first (see references/config-api.md);
-- documentation examples are NOT live values.
--
-- Read the live skin for the URL BEFORE choosing between these:
--   select incleng..config_get('{URL}', '{SITE}', 'skin_manifest');   -- composite?
--   select incleng..config_get('{URL}', '{SITE}', 'xslt_sheet');      -- legacy skin


-- ---------------------------------------------------------------------------
-- PATH C — region suppression. Composite-skin sites only, and the preferred
-- remediation where available: the page supplies its own chrome yet keeps
-- canonical, feeds, data islands, analytics and the OPAL widget.
-- {REGIONS} is a comma-delimited list of region names as declared in the
-- skin's manifest, e.g. 'nav,footer'. scripts/check_chrome_conflict.py
-- --composite prints the exact value for a given document.
-- ---------------------------------------------------------------------------
select incleng..config_set('{URL}', '{SITE}', 'regions_off', '{REGIONS}');
select incleng..config_flush_cache();

-- Rollback
-- select incleng..config_unset('{URL}', '{SITE}', 'regions_off');
-- select incleng..config_flush_cache();


-- ---------------------------------------------------------------------------
-- PATH A — passthrough override. Legacy-skin sites. The page keeps its own
-- layout but forfeits the engine-supplied head services listed above.
-- {SKIN} is a directory under /DAV/VAD/inclusion-engine/skin/ (passthrough,
-- openlink, responsive, clean, …) or under /DAV/VAD/opl-skins/ (matrix,
-- bootstrap-2022, docs-v3, …) — adjust the path accordingly.
-- ---------------------------------------------------------------------------

-- Per-URL override (recommended for single-page swaps: all other pages keep the site skin)
select incleng..config_set('{URL}', '{SITE}', 'xslt_sheet',
  'virt://WS.WS.SYS_DAV_RES.RES_FULL_PATH.RES_CONTENT:/DAV/VAD/inclusion-engine/skin/{SKIN}/xslt/PostProcess.xslt');

-- Site-wide override (every page on {SITE})
-- select incleng..config_set(null, '{SITE}', 'xslt_sheet',
--   'virt://WS.WS.SYS_DAV_RES.RES_FULL_PATH.RES_CONTENT:/DAV/VAD/inclusion-engine/skin/{SKIN}/xslt/PostProcess.xslt');

-- Required after any config change (content-only changes self-invalidate; this does not).
-- Use staleall() instead if a skin's XSLT file itself was edited — Virtuoso
-- caches compiled XSLT and config_flush_cache() does not clear it.
select incleng..config_flush_cache();

-- Verify what the URL now resolves to
select incleng..config_get('{URL}', '{SITE}', 'skin_manifest');
select incleng..config_get('{URL}', '{SITE}', 'xslt_sheet');
select incleng..config_get('{URL}', '{SITE}', 'regions_off');

-- Rollback the per-URL override
-- select incleng..config_unset('{URL}', '{SITE}', 'xslt_sheet');
-- select incleng..config_flush_cache();


-- ---------------------------------------------------------------------------
-- PATH B needs no SQL at all: strip the page's own masthead/nav/footer and the
-- head includes the live skin already injects, then WebDAV PUT it. Content-only
-- changes self-invalidate on mtime, so no flush is required.
-- ---------------------------------------------------------------------------
