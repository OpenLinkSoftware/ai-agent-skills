# CSV Mapping Design

Document these mapping choices before generating the DET:

- header to predicate mapping
- row to subject mapping
- namespace/base IRI strategy
- datatype inference rules
- multi-valued cell handling
- null/empty cell behavior
- whether mapping is fixed, generated, or user-supplied

Recommended practice:

- avoid hidden inference where possible
- keep mapping rules explicit and inspectable
- generate validation examples for sample rows

