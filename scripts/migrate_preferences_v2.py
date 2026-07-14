#!/usr/bin/env python3
"""
Restructure preferences.ttl: replace flat 91-step :agentBehaviorGuide
with hub + 10 themed sub-HowTos.
Uses rdflib for reliable parsing and regeneration.
"""
import rdflib
from rdflib.namespace import RDF, RDFS, OWL, XSD
from collections import OrderedDict

SCH = rdflib.Namespace('http://schema.org/')
ONTO = rdflib.Namespace('https://www.openlinksw.com/ontology/opal/')
FOAF = rdflib.Namespace('http://xmlns.com/foaf/0.1/')

# ── Load ────────────────────────────────────────────────────────────────────
g = rdflib.Graph()
import os; _PREF_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'agent-rdf-memory', 'preferences.ttl')
g.parse(_PREF_PATH, format='turtle')

BASE = rdflib.URIRef('#')

# ── Step grouping map ───────────────────────────────────────────────────────
# step-name → sub-HowTo ID
STEP_TO_GROUP = {}

GROUPS = OrderedDict([
    ("howto-identity-webid", {
        "name": "Identity, WebID & Delegation",
        "desc": "Agent identity format, whoami triggers, WebID-TLS verification, reciprocal delegation (local+remote), On-Behalf-Of header format, WebID verification services, and YouID validation gates.",
        "seeAlso": ["howto/agent-identity.ttl", "howto/verified-identity.ttl",
                    "howto/youid-delegation.ttl", "howto/webid-verification-services.ttl",
                    "howto/webid-verification-table.ttl", "howto/delegation-insert-gate.ttl",
                    "howto/youid-validation-gates.ttl"],
        "steps": ["step-whoamiFormat", "step-webidTlsVerification", "step-verifiedWhoami",
                  "step-whoamiSameAsHyperlinks", "step-urlsAsHyperlinks", "step-stripeSandboxCard",
                  "step-verifyRecipDelegation", "step-verifyDelegationRemote",
                  "step-webidVerificationServiceSelection", "step-webidVerificationTable",
                  "step-delegationLocalFiles", "step-delegationInsertGate",
                  "step-oboHeaderFormat", "step-youidValidationGate"],
    }),
    ("howto-memory-management", {
        "name": "Memory Management & Session Governance",
        "desc": "Agent RDF memory protocol, session file naming, prompt recording, secret redaction, SPARQL-based memory loading, token-optimized handoffs, and no-unauthorized-deletion rules.",
        "seeAlso": ["howto/session-governance.ttl", "howto/memory-protocol-gate.ttl",
                    "howto/token-optimized-session-handoff.ttl", "howto/sparql-memory-loading.ttl",
                    "howto/no-unauthorized-deletion.ttl", "howto/no-memory-md-write.ttl"],
        "steps": ["step-approval", "step-memoryProtocol", "step-gitWorkflow",
                  "step-noFabricatedUrls", "step-curlAuth", "step-secretRedaction",
                  "step-promptRecording", "step-memoryProtocolGate",
                  "step-tokenOptimizedSessionHandoff", "step-soleMemoryIndex",
                  "step-sparqlMemoryLoading", "step-noUnauthorizedDeletion",
                  "step-noMemoryMdWrite", "step-preferencesSparse", "step-secretEchoRedaction"],
    }),
    ("howto-artifact-routing", {
        "name": "Artifact Output Routing",
        "desc": "Model-specific output directory routing, model identity pre-flight gate, model-over-environment tiebreaker, artifact placement elicitation, and remote WebDAV upload.",
        "seeAlso": ["howto/artifact-routing.ttl", "howto/remote-webdav-upload.ttl"],
        "steps": ["step-outputDirs", "step-gpt5ChatCodexOutputDirs",
                  "step-modelIdentityPreflight", "step-defaultOutputRoot",
                  "step-modelOverEnvironment", "step-artifactPlacement",
                  "step-remoteWebdavUpload"],
    }),
    ("howto-rdf-authoring", {
        "name": "RDF Authoring & Entity Resolution",
        "desc": "Entity IRI denotation, canonical IRI compliance, external IRI verification, entity type gates, concept hyperlinking, FAQ entity IRI pre-build gate, DBpedia canonical subjects, blank node prohibitions, and language tagging.",
        "seeAlso": ["howto/canonical-entity-iri-denotation.ttl", "howto/entity-iri-denotation-mechanics.ttl",
                    "howto/canonical-iri-compliance-gate.ttl", "howto/entity-type-gate.ttl",
                    "howto/external-iri-verification.ttl", "howto/entity-link-placement.ttl",
                    "howto/concept-entity-hyperlinking.ttl", "howto/faq-entity-iri-gate.ttl",
                    "howto/sparql-absolute-prefix-iri.ttl", "howto/entity-href-companion-ttl.ttl",
                    "howto/owl-sameas-vs-skos-related.ttl", "howto/entity-lookup-disambiguation.ttl",
                    "howto/rdf-residence-vs-birthplace.ttl", "howto/no-blank-nodes-resolver-entities.ttl",
                    "howto/rdf-document-authoring.ttl"],
        "steps": ["step-entityDenotation", "step-documentEntity", "step-documentAbout",
                  "step-entityTypeGate", "step-externalIriVerification",
                  "step-entityLinkPlacement", "step-canonicalIriCompliance",
                  "step-conceptEntityHyperlinking", "step-noBlankNodes",
                  "step-faqEntityIriGate", "step-schemaAuthorOverFoafMaker",
                  "step-entityHrefCompanionTTL", "step-sparqlAbsolutePrefixIRI",
                  "step-owlSameAsVsSkosRelated", "step-entityLookupDisambiguation",
                  "step-residenceVsBirthplace", "step-noBlankNodesForResolverEntities",
                  "step-dbpediaCanonicalSubject", "step-terminologySemanticWeb"],
    }),
    ("howto-html-kg-explorer", {
        "name": "HTML Infographic & KG Explorer",
        "desc": "Infographic authoring, D3.js KG Explorer patterns (simulation lifecycle, click guard, sticky drag, lazy init, single render, static D3 load), UI patterns, harness contract compliance, SPARQL workbench, footer gates, and heading fragment IDs.",
        "seeAlso": ["howto/infographic-authoring.ttl", "howto/kg-explorer-ui-patterns.ttl",
                    "howto/kg-explorer-d3-patterns.ttl", "howto/kg-explorer-reuse-first.ttl",
                    "howto/harness-contract-compliance.ttl", "howto/rdf-infographic-compliance-gate.ttl",
                    "howto/rdf-infographic-gated-workflow.ttl", "howto/footer-sparql-explorer-gate.ttl",
                    "howto/sparql-html-escape-gate.ttl", "howto/study-prior-patterns.ttl",
                    "howto/kg-curation-attribution.ttl", "howto/ui-ux-expert-persona.ttl"],
        "steps": ["step-attribution", "step-darkModeCSS", "step-kgExplorerReuse",
                  "step-templateSelection", "step-kgNavPlacement", "step-kgNavCollapsed",
                  "step-kgControlsMasterClose", "step-kgNoOrphans", "step-kgToolbarGroups",
                  "step-kgSettingsPanel", "step-harnessIds", "step-footerLabels",
                  "step-sparqlFormat", "step-complianceBug", "step-simulationLifecycle",
                  "step-clickGuard", "step-kgDataRegex", "step-rdfInfographicGateEnforcement",
                  "step-rdfInfographicGatedWorkflow", "step-sparqlHtmlEscape",
                  "step-reuseWorkingKG", "step-kgDragSticky", "step-iifeGlobalScope",
                  "step-sparqlBtnFooterAnchor", "step-themeToggleInNavHeader",
                  "step-headingFragmentIds", "step-staticD3Load", "step-singleRender",
                  "step-kgLazyInit", "step-studyPriorPatterns", "step-kgCurationAttribution",
                  "step-uiUxExpertPersona", "step-faqQuestionTextHyperlink",
                  "step-sparqlWorkbenchPlacement", "step-sparqlBtnMandatory",
                  "step-sparqlExplorerVisibleText", "step-footerTextAlignCascade",
                  "step-staleWorkbenchCleanup"],
    }),
    ("howto-ontology-generation", {
        "name": "Ontology Generation",
        "desc": "Cross-reference gate for custom ontology terms, OWL property characterization from nine semantic categories, and shared ontology discovery via prefix.cc before inventing new predicates.",
        "seeAlso": ["howto/ontology-cross-reference-gate.ttl", "howto/owl-property-characterization.ttl",
                    "howto/ontology-discovery.ttl"],
        "steps": ["step-ontologyCrossReference", "step-owlPropertyCharacterization"],
    }),
    ("howto-skill-workflows", {
        "name": "Skill Chain & Workflows",
        "desc": "kg-generator → rdf-infographic-skill chain, KG query modes, ZIP repackaging, content retrieval tool order, OPAL session vocabulary, and URIBurner OAuth authorization code flow.",
        "seeAlso": ["howto/skill-invocation.ttl", "howto/opal-session-vocabulary.ttl",
                    "howto/uriburner-oauth-authcode-flow.ttl"],
        "steps": ["step-skillChain", "step-kgQueryMode", "step-zipRepackage",
                  "step-retrievalToolOrder", "step-opalSessionVocabulary",
                  "step-uriburnerOAuthAuthCodeFlow"],
    }),
    ("howto-virtuoso-sparql", {
        "name": "Virtuoso & SPARQL",
        "desc": "Virtuoso SPARQL URL format parameters by query type, workbench query deduplication via named graphs, and SPARQL absolute PREFIX IRI rules.",
        "seeAlso": ["howto/virtuoso-sparql-formats.ttl", "howto/virtuoso-workbench-query-dedup.ttl"],
        "steps": ["step-virtuosoSparqlFormats", "step-virtuosoWorkbenchQueryDedup"],
    }),
    ("howto-terminology", {
        "name": "Terminology & Conventions",
        "desc": "Mashup vs meshup terminology and other terminological conventions.",
        "seeAlso": ["howto/artifact-routing.ttl", "howto/rdf-document-authoring.ttl"],
        "steps": ["step-mashupVsMeshup"],
    }),
])

# Build reverse map
for gid, group in GROUPS.items():
    for s in group["steps"]:
        STEP_TO_GROUP[s] = gid

# ── Collect existing step URIs ──────────────────────────────────────────────
existing_steps = set()
for s in g.subjects(RDF.type, SCH.HowToStep):
    fragment = str(s).split('#')[-1]
    if fragment.startswith('step-'):
        existing_steps.add(fragment)

all_expected = set(STEP_TO_GROUP.keys())
missing = all_expected - existing_steps
extra = existing_steps - all_expected
if missing:
    print(f"⚠ Steps not in graph: {sorted(missing)}")
if extra:
    print(f"⚠ Steps in graph but not grouped: {sorted(extra)}")
print(f"Grouped steps: {len(all_expected & existing_steps)}/{len(all_expected)}")

# ── Build new graph ─────────────────────────────────────────────────────────
from rdflib import Graph, Literal, URIRef, BNode

ng = Graph()

# Bind prefixes
ng.bind('', URIRef('#'), override=True)
ng.bind('schema', SCH)
ng.bind('xsd', XSD)
ng.bind('rdfs', RDFS)
ng.bind('onto', ONTO)
ng.bind('opal', rdflib.Namespace('https://www.openlinksw.com/ontology/opal/'))
ng.bind('owl', OWL)
ng.bind('foaf', FOAF)

# ── Document entity ─────────────────────────────────────────────────────────
doc = URIRef('')
ng.add((doc, RDF.type, SCH.CreativeWork))
ng.add((doc, SCH.name, Literal('preferences.ttl', lang='en')))
ng.add((doc, SCH.description, Literal('Configuration for agent RDF memory management and semantic memory skill usage. Hub structure: :agentBehaviorGuide delegates to themed sub-HowTos, each owning its own schema:step list and rdfs:seeAlso to companion howto/*.ttl files.')))
ng.add((doc, SCH.dateModified, Literal('2026-07-01T12:00:00Z', datatype=XSD.dateTime)))
ng.add((doc, SCH.dateCreated, Literal('2026-05-29T17:22:00Z', datatype=XSD.dateTime)))
ng.add((doc, SCH.author, URIRef('https://linkedin.com/in/kidehen#this')))
ng.add((doc, SCH.about, URIRef('#agentBehaviorGuide')))

# ── Identity equivalences ───────────────────────────────────────────────────
kingsley = URIRef('https://linkedin.com/in/kidehen#this')
ng.add((kingsley, OWL.sameAs, URIRef('https://www.linkedin.com/in/kidehen#this')))

tony = URIRef('https://www.linkedin.com/in/tonyseale#this')
ng.add((tony, OWL.sameAs, URIRef('https://uk.linkedin.com/in/tonyseale#this')))
ng.add((tony, OWL.sameAs, URIRef('https://www.linkedin.com/in/tonyseale/#this')))

# ── Hub :agentBehaviorGuide ─────────────────────────────────────────────────
hub = URIRef('#agentBehaviorGuide')
ng.add((hub, RDF.type, SCH.HowTo))
ng.add((hub, SCH.name, Literal('Agent Standing Instructions', lang='en')))
ng.add((hub, SCH.description, Literal('Procedural rules the agent must follow in every session. Organized as 10 themed sub-HowTos, each delegating to companion howto/*.ttl files for full specification text.', lang='en')))

# schema:about — topic entities
for gid in GROUPS:
    topic_uri = URIRef(f'#topic-{gid.split("-", 2)[-1]}')
    ng.add((hub, SCH.about, topic_uri))

# schema:hasPart — sub-HowTos
for gid in GROUPS:
    howto_uri = URIRef(f'#{gid}')
    ng.add((hub, SCH.hasPart, howto_uri))

# ── Topic entities ──────────────────────────────────────────────────────────
for gid, group in GROUPS.items():
    topic_uri = URIRef(f'#topic-{gid.split("-", 2)[-1]}')
    ng.add((topic_uri, RDF.type, SCH.Thing))
    ng.add((topic_uri, SCH.name, Literal(group["name"], lang='en')))
    ng.add((topic_uri, SCH.description, Literal(group["desc"], lang='en')))

# ── Sub-HowTo entities ──────────────────────────────────────────────────────
for gid, group in GROUPS.items():
    howto_uri = URIRef(f'#{gid}')
    ng.add((howto_uri, RDF.type, SCH.HowTo))
    ng.add((howto_uri, SCH.name, Literal(group["name"], lang='en')))
    ng.add((howto_uri, SCH.description, Literal(group["desc"], lang='en')))

    # rdfs:seeAlso
    for sa in group["seeAlso"]:
        ng.add((howto_uri, RDFS.seeAlso, URIRef(sa)))

    # schema:step — only steps that exist in the original graph
    for step_name in group["steps"]:
        step_uri = URIRef(f'#{step_name}')
        if step_name in existing_steps:
            ng.add((howto_uri, SCH.step, step_uri))

# ── Step definitions (copied from original graph) ───────────────────────────
# Copy all triples where subject is a step, plus all HowToStep-specific properties
step_subjects = set()
for s in g.subjects(RDF.type, SCH.HowToStep):
    step_subjects.add(s)

for step_subj in step_subjects:
    for p, o in g.predicate_objects(step_subj):
        ng.add((step_subj, p, o))

# Also copy the :claudeCodeSettings PropertyValue
for p, o in g.predicate_objects(URIRef('#claudeCodeSettings')):
    ng.add((URIRef('#claudeCodeSettings'), p, o))

# ── Serialize ───────────────────────────────────────────────────────────────
output = ng.serialize(format='turtle', encoding='utf-8').decode('utf-8')

# Fix rdflib's formatting: use @prefix instead of PREFIX, clean up
output = output.replace('PREFIX ', '@prefix ')
output = output.replace('\n\n\n', '\n\n')

# Write
path = _PREF_PATH
with open(path, 'w') as f:
    f.write(output)

print(f"✅ Written {len(output):,} chars")

# ── Validate ────────────────────────────────────────────────────────────────
vg = rdflib.Graph()
vg.parse(path, format='turtle')
print(f"✅ Valid Turtle: {len(vg):,} triples")

# Count sub-HowTos
sub_howtos = list(vg.objects(URIRef('#agentBehaviorGuide'), SCH.hasPart))
print(f"✅ Sub-HowTos: {len(sub_howtos)}")

total_linked = 0
for sht in sub_howtos:
    name = list(vg.objects(sht, SCH.name))
    steps = list(vg.objects(sht, SCH.step))
    total_linked += len(steps)
    print(f"   {str(name[0]) if name else '?'}: {len(steps)} steps")
print(f"✅ Total steps linked: {total_linked}")
