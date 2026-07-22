# Facet Metadata Contract

Category facets are based on custom WebDAV properties using `schema:category`.

Pinned ordering is based on the custom WebDAV property `schema:position`.

## Property

- Prefix: `schema`
- Namespace: `https://schema.org/`
- Local name: `category`
- Expected values: semicolon-delimited or comma-delimited text labels, or repeated property values when supported by the client.

## Facet requirements

- Category labels must be displayed as human-readable text, not numeric internal IDs.
- Counts must reflect the currently scoped result set.
- The selected category should be visible and removable.
- If no `schema:category` values are present in the target collection, hide the facet section.
- Facet controls must preserve active search and calendar filters when applying or clearing a category.

## Metadata application

Use SQL server-side updates in `isql` mode or WebDAV `PROPPATCH` in WebDAV mode. In both cases:

- Prefer `scripts/publish_with_metadata.py` for managed WebDAV uploads so the post and `schema:category` metadata are published together.
- Use the scheduled refresh SQL for mounted-folder and third-party WebDAV uploads that bypass the helper.
- Do not guess categories for publication without user approval unless the user has selected a known profile-based auto-categorization workflow.
- Keep the raw analysis TSV, generated SQL, or dry-run output available for review.
- Verify by reading back properties before assuming the weblog can facet on them.

## Clean recategorization

For a clean slate, the target-specific scheduler SQL should:

1. Remove existing `schema:category` values for eligible post resources in the target collection.
2. Run `DB.DBA.WEBLOG_DAV_REFRESH_CATEGORIES` with `update_all = 1`.
3. Schedule `DB.DBA.WEBLOG_DAV_REFRESH_CATEGORIES` for future missing-only refreshes, defaulting to five minutes.

This avoids stale labels after a category profile changes while preserving automatic categorization for future uploads.

## Pinning metadata

- Property: `schema:position`
- Expected pinned value: `1`
- Expected unpinned value: missing or `0`
- The weblog engine treats any non-empty, non-zero string value as pinned.
- The core engine seeds the newest valid post as the default pin only when no explicit pin exists.
- Pinning should be handled as a designated-weblog action: identify the public weblog route, map it to the DAV collection, resolve the post filename or URL, update the resource property, then verify the recency list.

## Scheduled refresh

When posts can arrive through ordinary mounted WebDAV folders, install `templates/register-category-refresh-scheduler.sql`. The scheduler uses `DB.DBA.SYS_SCHEDULED_EVENT` and defaults to a five-minute interval. It should normally update only missing `schema:category` values; use the `update_all` flag for deliberate recomputation.
