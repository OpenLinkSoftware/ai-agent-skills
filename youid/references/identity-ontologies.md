# YouID Identity Ontology Reference

This reference documents the semantic web ontologies and vocabularies used in YouID identity profiles, certificates, and public key documents.

## Namespaces

| Prefix | Namespace IRI | Description |
|--------|---------------|-------------|
| `foaf` | `http://xmlns.com/foaf/0.1/` | Friend-of-a-Friend — people, agents, social networks |
| `schema` | `http://schema.org/` | Schema.org — general-purpose vocabulary |
| `cert` | `http://www.w3.org/ns/auth/cert#` | WebID crypto — RSA public keys |
| `oplcert` | `http://www.openlinksw.com/schemas/cert#` | OpenLink certificate ontology |
| `xsig` | `http://www.w3.org/2000/09/xmldsig#` | XML Digital Signature — digest types |
| `xsd` | `http://www.w3.org/2001/XMLSchema#` | XML Schema — data types |
| `rdfs` | `http://www.w3.org/2000/01/rdf-schema#` | RDF Schema |
| `owl` | `http://www.w3.org/2002/07/owl#` | Web Ontology Language |
| `xhv` | `http://www.w3.org/1999/xhtml/vocab#` | XHTML vocabulary — link relations |
| `dcterms` | `http://purl.org/dc/terms/` | Dublin Core Terms |
| `pim` | `http://www.w3.org/ns/pim/space#` | Personal Information Model |
| `rsa` | `http://www.w3.org/ns/auth/rsa#` | RSA key ontology (legacy) |
| `vcard` | `http://www.w3.org/2006/vcard/ns#` | vCard ontology |
| `skos` | `http://www.w3.org/2004/02/skos/core#` | SKOS — concept labels |
| `acl` | `http://www.w3.org/ns/auth/acl#` | Web Access Control |
| `ldp` | `http://www.w3.org/ns/ldp#` | Linked Data Platform |
| `as` | `http://www.w3.org/ns/activitystreams#` | Activity Streams (`as:alsoKnownAs` is the RDF term behind DID `alsoKnownAs`) |
| `sec` | `https://w3id.org/security#` | W3C Security / CID v1 — `sec:Multikey`, `sec:publicKeyMultibase` (datatype `sec:multibase`), `sec:controller`, `sec:verificationMethod`; used for did:nostr keys (see `did-nostr.md`) |

## Core Ontologies

### FOAF — Friend-of-a-Friend

FOAF describes people, agents, and their social connections. In YouID profiles, it provides the base identity description.

| Class | Description | Used In |
|-------|-------------|---------|
| `foaf:Person` | A person | profile.ttl, profile.jsonld, manual_bundle |
| `foaf:Agent` | An agent (person, group, software) | profile.ttl (conditional PDP block) |
| `foaf:PersonalProfileDocument` | A profile document about someone | manual_bundle |
| `foaf:profileDocument` | A profile document about something | profile.ttl, profile.jsonld |

| Property | Domain | Range | Description |
|----------|--------|-------|-------------|
| `foaf:name` | foaf:Agent | xsd:string | Full name |
| `foaf:mbox` | foaf:Agent | owl:Thing | Email mailbox |
| `foaf:mbox_sha1sum` | foaf:Agent | xsd:string | SHA-1 of email |
| `foaf:primaryTopic` | foaf:Document | owl:Thing | The main thing a doc is about |
| `foaf:maker` | foaf:Document | foaf:Agent | The creator of a document |
| `foaf:knows` | foaf:Person | foaf:Person | Relationship |
| `foaf:based_near` | foaf:Agent | spatial:Location | Location |

### cert — WebID Crypto Ontology (W3C)

The cert ontology describes cryptographic keys bound to WebIDs.

| Class | Description | Used In |
|-------|-------------|---------|
| `cert:RSAPublicKey` | RSA public key | All public_key templates, profile.ttl |
| `cert:Key` | Abstract key | Through inheritance |

| Property | Domain | Range | Description |
|----------|--------|-------|-------------|
| `cert:key` | foaf:Agent | cert:Key | Links agent to public key |
| `cert:modulus` | cert:RSAPublicKey | xsd:hexBinary | RSA modulus (N) |
| `cert:exponent` | cert:RSAPublicKey | xsd:int | RSA public exponent (E) |

### oplcert — OpenLink Certificate Ontology

OpenLink's extension to the W3C cert ontology for full X.509 certificate descriptions.

| Class | Description | Used In |
|-------|-------------|---------|
| `oplcert:Certificate` | An X.509 certificate | All certificate templates, profile.ttl |

| Property | Domain | Range | Description |
|----------|--------|-------|-------------|
| `oplcert:hasCertificate` | foaf:Agent | oplcert:Certificate | Links agent to its certificate |
| `oplcert:hasPublicKey` | oplcert:Certificate | cert:RSAPublicKey | Certificate contains this key |
| `oplcert:hasIdentityDelegate` | foaf:Agent | foaf:Agent | Delegation: A delegates to B |
| `oplcert:onBehalfOf` | foaf:Agent | foaf:Agent | A acts on behalf of B |
| `oplcert:owns` | foaf:Agent | oplcert:Certificate | Agent owns this certificate |
| `oplcert:SAN` | oplcert:Certificate | xsd:anyURI | Subject Alternative Name (the WebID) |
| `oplcert:IAN` | oplcert:Certificate | xsd:anyURI | Issuer Alternative Name (CA WebID) |
| `oplcert:subject` | oplcert:Certificate | xsd:string | X.509 Subject Distinguished Name |
| `oplcert:issuer` | oplcert:Certificate | xsd:string | X.509 Issuer Distinguished Name |
| `oplcert:serial` | oplcert:Certificate | xsd:string | Certificate serial number |
| `oplcert:notBefore` | oplcert:Certificate | xsd:dateTime | Validity start |
| `oplcert:notAfter` | oplcert:Certificate | xsd:dateTime | Validity end |
| `oplcert:fingerprint` | oplcert:Certificate | xsd:string | SHA-1 fingerprint (hex) |
| `oplcert:fingerprint-digest` | oplcert:Certificate | xsig:digest | SHA-1 and SHA-256 digest typed values |

### Schema.org

Schema.org provides a widely-understood vocabulary for structured data.

| Type | Description | Used In |
|------|-------------|---------|
| `schema:Person` | A person | All profile templates |
| `schema:Organization` | An organization | profile.ttl, profile.jsonld |
| `schema:Place` | A location (address) | profile.ttl, profile.jsonld |
| `schema:CreativeWork` | A creative work | profile.ttl (the document itself) |
| `schema:WebPage` | A web page | profile.ttl, profile.jsonld |

| Property | Description |
|----------|-------------|
| `schema:name` | Name of the person/organization |
| `schema:email` | Email address |
| `schema:worksFor` | Organization affiliation |
| `schema:address` | Physical address (uses schema:Place) |
| `schema:addressCountry` | Country (e.g., "US") |
| `schema:addressRegion` | State/province |
| `schema:sameAs` | Same-as relationship across platforms |
| `schema:mainEntity` | Primary entity of a page |
| `schema:url` | URL reference |
| `schema:additionalType` | Additional types |
| `schema:author` | Author of a document |
| `schema:isRelatedTo` | Related resource |
| `schema:about` | Subject of a document |

### Key Design Patterns

#### Public Key + Certificate Binding

The YouID profile binds an agent to a public key through the certificate:

```
agent → cert:key → RSAPublicKey (modulus, exponent)
agent → oplcert:hasCertificate → Certificate (fingerprint, SAN, subject, issuer, notBefore, notAfter)
Certificate → oplcert:hasPublicKey → RSAPublicKey
```

#### WebID-TLS and owl:sameAs

The WebID is the primary URI for the identity. Additional profile representations are linked via `owl:sameAs`:

```
WebID identity → owl:sameAs → JSON-LD profile identity
WebID identity → owl:sameAs → RDFa profile identity
WebID identity → owl:sameAs → Turtle profile identity
```

#### NI/DI URIs

The certificate fingerprint generates two content-addressed URIs:

| URI Pattern | Meaning |
|-------------|---------|
| `ni:///sha-256;{base64url-digest}` | Named Information — content-addressed identifier |
| `urn:di:sha-256;{hex-digest}` | Digest Identifier — alternative content-addressed form |

These are linked via `owl:sameAs` to the `cert:RSAPublicKey` entity.
