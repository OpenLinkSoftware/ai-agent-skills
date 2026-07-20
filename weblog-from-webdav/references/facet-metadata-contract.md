# Facet Metadata Contract

Category facets are based on custom WebDAV properties using `schema:category`.

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

## Metadata application

Use SQL server-side updates in `isql` mode or WebDAV `PROPPATCH` in WebDAV mode. In both cases:

- Do not guess categories for publication without user approval.
- Keep the raw analysis TSV or SQL staging data available for review.
- Verify by reading back properties before assuming the weblog can facet on them.
