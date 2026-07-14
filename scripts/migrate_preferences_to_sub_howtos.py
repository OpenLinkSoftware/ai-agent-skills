#!/usr/bin/env python3
"""
Migrate preferences.ttl from 91 flat steps under :agentBehaviorGuide
to ~10 themed sub-HowTos, each with their own step list.
"""

import re
from collections import OrderedDict

import os; PREF_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'agent-rdf-memory', 'preferences.ttl')
with open(PREF_PATH, 'r') as f:
    content = f.read()

# ── Step-to-group mapping ───────────────────────────────────────────────────
# Grouped by the primary howto file each step's rdfs:seeAlso points to.

STEP_GROUPS = OrderedDict([
    ("howto-identity-webid", {
        "name": "Identity, WebID & Delegation",
        "desc": "Agent identity format, whoami triggers, WebID-TLS verification, reciprocal delegation (local+remote), On-Behalf-Of header format, WebID verification services, and YouID validation gates.",
        "seeAlso": [
            "howto/agent-identity.ttl", "howto/verified-identity.ttl",
            "howto/youid-delegation.ttl", "howto/webid-verification-services.ttl",
            "howto/webid-verification-table.ttl", "howto/delegation-insert-gate.ttl",
            "howto/youid-validation-gates.ttl",
        ],
        "steps": [
            "step-whoamiFormat", "step-webidTlsVerification", "step-verifiedWhoami",
            "step-whoamiSameAsHyperlinks", "step-urlsAsHyperlinks", "step-stripeSandboxCard",
            "step-verifyRecipDelegation", "step-verifyDelegationRemote",
            "step-webidVerificationServiceSelection", "step-webidVerificationTable",
            "step-delegationLocalFiles", "step-delegationInsertGate",
            "step-oboHeaderFormat", "step-youidValidationGate",
        ],
    }),
    ("howto-memory-management", {
        "name": "Memory Management & Session Governance",
        "desc": "Agent RDF memory protocol, session file naming, prompt recording, secret redaction, SPARQL-based memory loading, token-optimized handoffs, and no-unauthorized-deletion rules.",
        "seeAlso": [
            "howto/session-governance.ttl", "howto/memory-protocol-gate.ttl",
            "howto/token-optimized-session-handoff.ttl", "howto/sparql-memory-loading.ttl",
            "howto/no-unauthorized-deletion.ttl", "howto/no-memory-md-write.ttl",
        ],
        "steps": [
            "step-approval", "step-memoryProtocol", "step-gitWorkflow",
            "step-noFabricatedUrls", "step-curlAuth", "step-secretRedaction",
            "step-promptRecording", "step-memoryProtocolGate",
            "step-tokenOptimizedSessionHandoff", "step-soleMemoryIndex",
            "step-sparqlMemoryLoading", "step-noUnauthorizedDeletion",
            "step-noMemoryMdWrite", "step-preferencesSparse", "step-secretEchoRedaction",
        ],
    }),
    ("howto-artifact-routing", {
        "name": "Artifact Output Routing",
        "desc": "Model-specific output directory routing, model identity pre-flight gate, model-over-environment tiebreaker, artifact placement elicitation, and remote WebDAV upload.",
        "seeAlso": ["howto/artifact-routing.ttl", "howto/remote-webdav-upload.ttl"],
        "steps": [
            "step-outputDirs", "step-gpt5ChatCodexOutputDirs",
            "step-modelIdentityPreflight", "step-defaultOutputRoot",
            "step-modelOverEnvironment", "step-artifactPlacement",
            "step-remoteWebdavUpload",
        ],
    }),
    ("howto-rdf-authoring", {
        "name": "RDF Authoring & Entity Resolution",
        "desc": "Entity IRI denotation, canonical IRI compliance, external IRI verification, entity type gates, concept hyperlinking, FAQ entity IRI pre-build gate, DBpedia canonical subjects, blank node prohibitions, and language tagging.",
        "seeAlso": [
            "howto/canonical-entity-iri-denotation.ttl", "howto/entity-iri-denotation-mechanics.ttl",
            "howto/canonical-iri-compliance-gate.ttl", "howto/entity-type-gate.ttl",
            "howto/external-iri-verification.ttl", "howto/entity-link-placement.ttl",
            "howto/concept-entity-hyperlinking.ttl", "howto/faq-entity-iri-gate.ttl",
            "howto/sparql-absolute-prefix-iri.ttl", "howto/entity-href-companion-ttl.ttl",
            "howto/owl-sameas-vs-skos-related.ttl", "howto/entity-lookup-disambiguation.ttl",
            "howto/rdf-residence-vs-birthplace.ttl", "howto/no-blank-nodes-resolver-entities.ttl",
            "howto/rdf-document-authoring.ttl",
        ],
        "steps": [
            "step-entityDenotation", "step-documentEntity", "step-documentAbout",
            "step-entityTypeGate", "step-externalIriVerification",
            "step-entityLinkPlacement", "step-canonicalIriCompliance",
            "step-conceptEntityHyperlinking", "step-noBlankNodes",
            "step-faqEntityIriGate", "step-schemaAuthorOverFoafMaker",
            "step-entityHrefCompanionTTL", "step-sparqlAbsolutePrefixIRI",
            "step-owlSameAsVsSkosRelated", "step-entityLookupDisambiguation",
            "step-residenceVsBirthplace", "step-noBlankNodesForResolverEntities",
            "step-dbpediaCanonicalSubject", "step-terminologySemanticWeb",
        ],
    }),
    ("howto-html-kg-explorer", {
        "name": "HTML Infographic & KG Explorer",
        "desc": "Infographic authoring, D3.js KG Explorer patterns (simulation lifecycle, click guard, sticky drag, lazy init, single render, static D3 load), UI patterns (nav placement/collapse, controls, orphans, toolbar, settings), harness contract compliance, SPARQL workbench, footer gates, heading fragment IDs, theme toggle, and IIFE scoping.",
        "seeAlso": [
            "howto/infographic-authoring.ttl", "howto/kg-explorer-ui-patterns.ttl",
            "howto/kg-explorer-d3-patterns.ttl", "howto/kg-explorer-reuse-first.ttl",
            "howto/harness-contract-compliance.ttl", "howto/rdf-infographic-compliance-gate.ttl",
            "howto/rdf-infographic-gated-workflow.ttl", "howto/footer-sparql-explorer-gate.ttl",
            "howto/sparql-html-escape-gate.ttl", "howto/study-prior-patterns.ttl",
            "howto/kg-curation-attribution.ttl", "howto/ui-ux-expert-persona.ttl",
        ],
        "steps": [
            "step-attribution", "step-darkModeCSS", "step-kgExplorerReuse",
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
            "step-staleWorkbenchCleanup",
        ],
    }),
    ("howto-ontology-generation", {
        "name": "Ontology Generation",
        "desc": "Cross-reference gate for custom ontology terms, OWL property characterization from nine semantic categories, and shared ontology discovery via prefix.cc before inventing new predicates.",
        "seeAlso": [
            "howto/ontology-cross-reference-gate.ttl",
            "howto/owl-property-characterization.ttl",
            "howto/ontology-discovery.ttl",
        ],
        "steps": [
            "step-ontologyCrossReference", "step-owlPropertyCharacterization",
        ],
    }),
    ("howto-skill-workflows", {
        "name": "Skill Chain & Workflows",
        "desc": "kg-generator → rdf-infographic-skill chain, KG query modes, ZIP repackaging, content retrieval tool order, and OPAL session vocabulary.",
        "seeAlso": [
            "howto/skill-invocation.ttl", "howto/opal-session-vocabulary.ttl",
            "howto/uriburner-oauth-authcode-flow.ttl",
        ],
        "steps": [
            "step-skillChain", "step-kgQueryMode", "step-zipRepackage",
            "step-retrievalToolOrder", "step-opalSessionVocabulary",
            "step-uriburnerOAuthAuthCodeFlow",
        ],
    }),
    ("howto-virtuoso-sparql", {
        "name": "Virtuoso & SPARQL",
        "desc": "Virtuoso SPARQL URL format parameters by query type, workbench query deduplication via named graphs, and SPARQL absolute PREFIX IRI rules.",
        "seeAlso": [
            "howto/virtuoso-sparql-formats.ttl",
            "howto/virtuoso-workbench-query-dedup.ttl",
        ],
        "steps": [
            "step-virtuosoSparqlFormats", "step-virtuosoWorkbenchQueryDedup",
        ],
    }),
    ("howto-terminology", {
        "name": "Terminology & Conventions",
        "desc": "Mashup vs meshup terminology, a/the Semantic Web distinction, and schema:author over foaf:maker convention.",
        "seeAlso": [
            "howto/artifact-routing.ttl", "howto/rdf-document-authoring.ttl",
        ],
        "steps": [
            "step-mashupVsMeshup",
        ],
    }),
])

# ── Collect all expected steps ──────────────────────────────────────────────
ALL_STEPS = set()
for group in STEP_GROUPS.values():
    for s in group["steps"]:
        ALL_STEPS.add(s)

# ── Parse existing file to extract step definitions ─────────────────────────
# Find all step definitions and their text (from ":step-X a schema:HowToStep" through the trailing "." or next section)
step_blocks = {}
current_step = None
current_block = []
in_block = False

for line in content.split('\n'):
    # Detect start of a step definition
    m = re.match(r'^(:step-\w+)\s+a\s+schema:HowToStep\s*;', line)
    if m:
        if current_step and current_block:
            step_blocks[current_step] = '\n'.join(current_block)
        current_step = m.group(1)
        current_block = [line]
        in_block = True
        continue

    if in_block:
        current_block.append(line)
        # Detect end of step definition (line with just "    ." or a new section starting with "#" or ":")
        if re.match(r'^\s*\.\s*$', line):
            step_blocks[current_step] = '\n'.join(current_block)
            in_block = False
            current_step = None
            current_block = []
        elif re.match(r'^[#:]', line) and not line.startswith('    ') and not line.startswith('\t'):
            # New section started — close previous block
            step_blocks[current_step] = '\n'.join(current_block)
            in_block = False
            current_step = None
            current_block = []

# Capture last step if file ends with it
if current_step and current_block:
    step_blocks[current_step] = '\n'.join(current_block)

print(f"Extracted {len(step_blocks)} step definitions")
missing = ALL_STEPS - set(step_blocks.keys())
if missing:
    print(f"WARNING: {len(missing)} steps not found in file: {sorted(missing)}")

# ── Extract the preamble (everything before :agentBehaviorGuide section) ────
# Find the start of :agentBehaviorGuide
guide_start = content.find(':agentBehaviorGuide a schema:HowTo ;')
if guide_start < 0:
    print("ERROR: Cannot find :agentBehaviorGuide")
    exit(1)

# Find end of the guide (end of its property list — the "." line)
guide_end = content.find('\n\n#', guide_start)
if guide_end < 0:
    guide_end = content.find('\n\n:', guide_start)
if guide_end < 0:
    print("ERROR: Cannot find end of :agentBehaviorGuide")
    exit(1)

preamble = content[:guide_start]

# ── Extract identity equivalences ───────────────────────────────────────────
# These are after preamble but before :agentBehaviorGuide
id_equiv_start = content.find('<https://linkedin.com/in/kidehen#this>')
id_equiv_end = content.find(':agentBehaviorGuide')
id_equiv = content[id_equiv_start:id_equiv_end].strip()

# ── Build new file ──────────────────────────────────────────────────────────
lines = []
lines.append(preamble.rstrip())
lines.append("")
lines.append(id_equiv)
lines.append("")

# ── Hub :agentBehaviorGuide ─────────────────────────────────────────────────
lines.append(":agentBehaviorGuide a schema:HowTo ;")
lines.append('    schema:name "Agent Standing Instructions"@en ;')
lines.append('    schema:description "Procedural rules the agent must follow in every session. Organized as themed sub-HowTos, each delegating to companion howto/*.ttl files for full specification text."@en ;')
lines.append("    schema:about " + ", ".join([f":topic-{gid.split('-',2)[-1]}" for gid in STEP_GROUPS.keys()]) + " ;")

# hasPart list
hasPart_items = [f":{gid}" for gid in STEP_GROUPS.keys()]
for i, hp in enumerate(hasPart_items):
    if i < len(hasPart_items) - 1:
        lines.append(f"    schema:hasPart {hp} ,")
    else:
        lines.append(f"    schema:hasPart {hp} .")
lines.append("")

# ── Topic entities ──────────────────────────────────────────────────────────
for gid, group in STEP_GROUPS.items():
    topic_id = f"topic-{gid.split('-', 2)[-1]}"
    lines.append(f":{topic_id} a schema:Thing ;")
    lines.append(f'    schema:name "{group["name"]}"@en ;')
    lines.append(f'    schema:description "{group["desc"]}"@en .')
    lines.append("")

# ── Sub-HowTo entities ──────────────────────────────────────────────────────
for gid, group in STEP_GROUPS.items():
    lines.append(f":{gid} a schema:HowTo ;")
    lines.append(f'    schema:name "{group["name"]}"@en ;')
    lines.append(f'    schema:description "{group["desc"]}"@en ;')

    # rdfs:seeAlso
    for i, sa in enumerate(group["seeAlso"]):
        if i == 0:
            lines.append(f"    rdfs:seeAlso <{sa}>")
        else:
            lines.append(f"        , <{sa}>")
    lines[-1] = lines[-1] + " ;"

    # schema:step
    steps_found = [s for s in group["steps"] if s in step_blocks]
    steps_missing = [s for s in group["steps"] if s not in step_blocks]
    if steps_missing:
        print(f"  ⚠ {gid}: {len(steps_missing)} steps not found: {steps_missing}")

    for i, s in enumerate(steps_found):
        if i == 0:
            lines.append(f"    schema:step :{s}")
        else:
            lines.append(f"        , :{s}")

    if steps_found:
        lines[-1] = lines[-1] + " ."
    else:
        # No steps — close the previous line
        prev = lines[-1].rstrip(' ;')
        lines[-1] = prev + " ."
    lines.append("")

# ── All Step Definitions ────────────────────────────────────────────────────
lines.append("# ═══════════════════════════════════════════════════════════════════")
lines.append("# ── Step Definitions (referenced by sub-HowTos above) ───────────")
lines.append("# ═══════════════════════════════════════════════════════════════════")
lines.append("")

# Output steps grouped by sub-HowTo
for gid, group in STEP_GROUPS.items():
    lines.append(f"# ── {group['name']} ──")
    for s in group["steps"]:
        if s in step_blocks:
            block = step_blocks[s]
            lines.append(block)
            lines.append("")
    lines.append("")

output = '\n'.join(lines)

# Write
with open(PREF_PATH, 'w') as f:
    f.write(output)

print(f"\n✅ Written {len(output):,} chars to preferences.ttl")

# Validate
import rdflib
g = rdflib.Graph()
try:
    g.parse(PREF_PATH, format='turtle')
    print(f"✅ Valid Turtle: {len(g):,} triples")

    from rdflib.namespace import RDF, RDFS
    SCH = rdflib.Namespace('http://schema.org/')

    # Count sub-HowTos
    sub_howtos = list(g.objects(rdflib.URIRef('#agentBehaviorGuide'), SCH.hasPart))
    print(f"✅ Sub-HowTos referenced by hub: {len(sub_howtos)}")

    # Count steps per sub-HowTo
    for sht in sub_howtos:
        name = list(g.objects(sht, SCH.name))
        steps = list(g.objects(sht, SCH.step))
        print(f"   {str(name[0]) if name else str(sht)}: {len(steps)} steps")

    # Verify all expected steps are linked somewhere
    orphan_steps = []
    for step_name in ALL_STEPS:
        step_uri = rdflib.URIRef(f'#{step_name}')
        # Check if any sub-HowTo references it
        found = False
        for sht in sub_howtos:
            if step_uri in list(g.objects(sht, SCH.step)):
                found = True
                break
        if not found:
            orphan_steps.append(step_name)

    if orphan_steps:
        print(f"⚠ Orphan steps (not linked to any sub-HowTo): {orphan_steps}")
    else:
        print(f"✅ All {len(ALL_STEPS)} steps linked to sub-HowTos")

except Exception as e:
    print(f"❌ Parse error: {e}")
