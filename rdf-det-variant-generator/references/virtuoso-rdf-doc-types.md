# Virtuoso RDF Document Type Guidance

When generating a DET variant, support RDF document types that Virtuoso can load through its RDF import routines.

Typical supported categories:

- RDF/XML
- Turtle
- N3
- JSON-LD
- N-Triples
- other RDF syntaxes already handled by existing Virtuoso RDF loaders in the target deployment

Generation guidance:

- define explicit MIME/type routing rules
- map each supported type to the corresponding Quad Store load path
- avoid guessing unsupported syntaxes; inspect the target deployment’s existing RDF loader usage if needed
- keep content-type checks centralized in a helper

