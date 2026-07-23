-- ODSI skin override templates.
-- Replace {URL}, {SITE}, {SKIN} before running via isql.
-- {SKIN} is a directory under /DAV/VAD/inclusion-engine/skin/ , e.g. passthrough, openlink, responsive.
-- Elicit {URL} and {SITE} from the live config graph first (see references/config-api.md);
-- documentation examples are NOT live values.

-- Per-URL override (recommended for single-page swaps: all other pages keep the site skin)
select incleng..config_set('{URL}', '{SITE}', 'xslt_sheet',
  'virt://WS.WS.SYS_DAV_RES.RES_FULL_PATH.RES_CONTENT:/DAV/VAD/inclusion-engine/skin/{SKIN}/xslt/PostProcess.xslt');

-- Site-wide override (every page on {SITE})
-- select incleng..config_set(null, '{SITE}', 'xslt_sheet',
--   'virt://WS.WS.SYS_DAV_RES.RES_FULL_PATH.RES_CONTENT:/DAV/VAD/inclusion-engine/skin/{SKIN}/xslt/PostProcess.xslt');

-- Required after any config change (content-only changes self-invalidate; this does not)
select incleng..config_flush_cache();

-- Verify what a URL now resolves to
select incleng..config_get('{URL}', '{SITE}', 'xslt_sheet');

-- Rollback the per-URL override
-- select incleng..config_unset('{URL}', '{SITE}', 'xslt_sheet');
-- select incleng..config_flush_cache();
