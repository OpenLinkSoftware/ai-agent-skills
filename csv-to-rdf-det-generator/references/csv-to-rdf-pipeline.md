# CSV to RDF Pipeline

Recommended sequence:

1. Accept CSV upload through `_DAV_RES_UPLOAD`.
2. Store the DAV resource row.
3. Parse CSV content.
4. Transform CSV rows to RDF triples using the chosen mapping model.
5. Load the generated RDF into the Quad Store.
6. Persist DET metadata:
   - source path
   - graph IRI
   - content type
   - mapping/profile identifier if applicable

Design choices to make explicit:

- one graph per folder or one graph per upload
- subject IRI strategy
- datatype conversion rules
- header normalization rules
- treatment of missing values

