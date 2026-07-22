# VSP Template Contract

The weblog VSP must make a WebDAV folder usable as a weblog without changing the document-authoring workflow.

## Required behavior

- Enumerate HTML and Markdown posts from the associated DAV collection.
- Exclude macOS sidecar files and hidden system files.
- Render the selected post in the main pane.
- Keep a recency-ordered sidebar list of posts.
- Promote pinned posts ahead of ordinary recency ordering when a post has a non-zero `schema:position` custom DAV property.
- Provide working RSS and Atom buttons plus POSH feed autodiscovery links.
- Preserve source HTML documents as self-contained documents inside the frame.
- Prevent scrolling beyond the embedded document into large empty space before the outer footer.
- Provide a dark/light control scoped to the outer weblog frame.

## Facet variant behavior

- Add scoped full-text search.
- Add calendar date range controls.
- Add category facets from `schema:category` custom WebDAV properties.
- Hide facets if no category metadata exists.
- Search results should be shown in the main pane as a result list rather than pretending an arbitrary first post is the answer.

## Pinning behavior

- Pinning is metadata-driven; do not rename or touch the source post file to pin it.
- Use `schema:position` as a resource-level custom DAV property. A non-zero string value pins the post.
- Pinned posts appear before ordinary posts. Within the pinned group, keep the normal recency order.
- Unpinning removes `schema:position` or sets it to `0`.
- A prompt such as "pin this post on the UB weblog" should resolve the designated weblog, verify the post resource, set the DAV metadata through WebDAV or SQL, and verify the rendered order.

## Known error patterns

- Raw VSP text in the browser means the DAV mapping is serving static content or the VSP syntax is invalid before execution.
- `FT042` means `contains` is not in a top-level `AND` predicate.
- `XM029` on multi-word search means the free-text expression was not escaped or quoted properly.
- `SR007 trim ... INTEGER` means a property value or parameter was used without string coercion.
- Category facet counts of zero usually mean the aggregate dictionary is being read incorrectly or categories were attached under a different property IRI.
