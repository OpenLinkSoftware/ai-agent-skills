# Draft: Jev's high-confidence routing of unrouted steps

Status: draft for review, 2026-11-12. Nothing in `preferences.ttl` or any howto has been changed.

Source: `scripts/jev-route-steps.py` run with TypeSafe Jev (`jev-latest`, served by `jev-1.14.0`) over the 171 steps attached to no topic howto. This file lists the 69 answers at confidence 0.8 or higher: **51 proposed assignments** to a topic and **18 steps Jev says belong to none** (they stay unrouted). Jev saw each step's position, name and first 300 characters of text only; 23 credential-related steps were withheld and are not here.

How an assignment would be applied: add the step to the `schema:step` list of that topic's `:howto-<topic>` block in `preferences.ttl`. Nothing else changes, and removing the line undoes it.

Read before approving: the confidence is Jev's own. In 24 of the 51 Jev and the trigger-phrase match agree; in 23 they differ; in 4 there was no phrase suggestion. Step names are truncated to 120 characters.

## html-kg-explorer (27)

| Step | Confidence | Phrase match | Step name |
|---|---|---|---|
| 148 | 0.89 | skill-workflows (differs) | Nav panel MUST be resizable when expanded AND manually hideable via the same fade/marker path — added to rdf-infographic |
| 159 | 1.00 | skill-workflows (differs) | A reused HTML template is a snapshot of the contract on its generation date — audit it feature-by-feature against the cu |
| 170 | 0.90 | html-kg-explorer (agrees) | When patching a missing footer sparqlBtn onto generator output, build the full footer-sparql-explorer-gate.ttl structure |
| 172 | 0.98 | - (no phrase hit) | Before patching in a missing sparqlBtn, check whether the page already has a SPARQL section (id, heading, or workbench)  |
| 173 | 0.99 | html-kg-explorer (agrees) | generate_infographic.py silently drops schema:CreativeWork section bodies from rendering, and its KG Explorer omits seve |
| 185 | 0.99 | html-kg-explorer (agrees) | Wrap every SPARQL-bearing section — sample query cards AND the whole KG Explorer / SPARQL Workbench sections — in a clos |
| 189 | 0.97 | html-kg-explorer (agrees) | SUPERSEDED 2026-08-20 by Step 243 — see below. KG Explorer and SPARQL Workbench MUST precede FAQ, Glossary, and HowTo —  |
| 190 | 0.87 | html-kg-explorer (agrees) | A schema:SoftwareSourceCode entity nested as a schema:hasPart child of any section (not just top-level) must not render  |
| 191 | 0.97 | html-kg-explorer (agrees) | Any container placed outside the .section/.section-alt system (a direct <body> child, or a footer sub-wrapper) needs its |
| 194 | 1.00 | html-kg-explorer (agrees) | KG Explorer and SPARQL Workbench are always-visible sections again — do NOT wrap #kg-explorer or #sparql-explorer in a s |
| 196 | 0.87 | artifact-routing (differs) | Before copying any prior HTML file as a structural base (LLM-Direct hand-authoring OR generator-assisted), grep it again |
| 201 | 0.98 | rdf-authoring (differs) | The footer SPARQL feature is the full Workbench (sample-query <details> cards + editable recipe/textarea editor + single |
| 213 | 0.87 | skill-workflows (differs) | Reference-section order is HowTo, then FAQ, then Glossary — enforced in rdf-infographic-skill's html_assembler.py and ch |
| 214 | 0.84 | rdf-authoring (differs) | generate_infographic.py no longer renders a standalone People section — person entities and canonical-identity/cross-ref |
| 217 | 0.91 | rdf-authoring (differs) | generate_infographic.py no longer renders a standalone Organizations section — organization entities and canonical-ident |
| 218 | 0.83 | skill-workflows (differs) | rdf-infographic-skill sections now alternate section/section-alt in real DOM order via a client-side pass, since html_as |
| 219 | 1.00 | skill-workflows (differs) | KG Explorer predicate labels are hover-reveal, not always-on; node labels sit below the circle with a paint-order:stroke |
| 228 | 1.00 | skill-workflows (differs) | KG Explorer predicate/edge labels MUST be visible by default (non-zero opacity), not hidden until hover; SKILL.md's Basi |
| 232 | 0.90 | rdf-authoring (differs) | A tier/category map (or any HTML section presenting an RDF-derived count or list) MUST be regenerated from the graph whe |
| 233 | 0.80 | skill-workflows (differs) | SUPERSEDED 2026-08-19 by Step 236, itself refined 2026-08-20 by Step 244 — assets/templates/thesis-framework-openlink-br |
| 245 | 1.00 | html-kg-explorer (agrees) | SPARQL workbench accordion MUST be open by default (supersedes the closed-by-default rendering) |
| 254 | 0.97 | html-kg-explorer (agrees) | A generated HTML infographic must be loaded in a real browser (local server + console-error check + DOM population check |
| 307 | 1.00 | html-kg-explorer (agrees) | KG Explorer and SPARQL Workbench are collapsible sections CLOSED BY DEFAULT — wrap #kg-explorer and #sparql-workbench in |
| 330 | 0.99 | html-kg-explorer (agrees) | The footer 'Explore the Knowledge Graph using SPARQL' workbench is a collapsible <details> (footer-accordion) CLOSED by  |
| 331 | 0.91 | skill-workflows (differs) | Exactly one query surface per page: the SPARQL Workbench; the footer 'Explore/Query the Knowledge Graph' workbench and # |
| 350 | 0.99 | html-kg-explorer (agrees) | Before trusting a generator or validator on any rule, grep preferences.ttl for the newest step on that topic; when the t |
| 351 | 0.96 | rdf-authoring (differs) | rdf-infographic-skill pages give every section and sub-section a kebab-case id from the entity IRI and a real fragment l |

## artifact-routing (5)

| Step | Confidence | Phrase match | Step name |
|---|---|---|---|
| 134 | 1.00 | artifact-routing (agrees) | Generated VSP (Virtuoso Server Page) artifacts go in a vsps/ subfolder under the model-specific output root |
| 140 | 1.00 | artifact-routing (agrees) | Generated diagram artifacts (draw.io, Mermaid exports, etc.) go in a visualizations/ subfolder under the model-specific  |
| 250 | 1.00 | skill-workflows (differs) | A drafted chat/forum-reply Markdown file is still a generated artifact subject to step-outputDirs/step-outputRootBlockin |
| 259 | 0.99 | skill-workflows (differs) | The Markdown companion is NOT uploaded to URIBurner DAV unless the user explicitly instructs it — default upload set is  |
| 289 | 1.00 | artifact-routing (agrees) | When running a noted RDF+HTML meshup prompt, generate and store under Documents/LLMs/Grok/{rdf,webpages,md}/ by default  |

## memory-management (5)

| Step | Confidence | Phrase match | Step name |
|---|---|---|---|
| 110 | 0.92 | - (no phrase hit) | DEPRECATED — replaced by step-progressiveContextLoading (position 144) |
| 152 | 0.96 | memory-management (agrees) | Reading agent-rdf-memory/sessions/ defaults to the current model's own history; elicit on the first read of each session |
| 302 | 0.85 | - (no phrase hit) | When memory is driven from Virtuoso, a SAMPLE()-based verification query (one FROM NAMED per document graph) feeds per-f |
| 306 | 0.83 | rdf-authoring (differs) | Optional System One judgment modality on the agent-rdf-memory harness: judgmentModality none/jev-shadow/jev-active; Jev/ |
| 319 | 0.98 | rdf-authoring (differs) | Run the full retrieval sequence as the first action of every session in this repo, and write the session file as the las |

## rdf-authoring (5)

| Step | Confidence | Phrase match | Step name |
|---|---|---|---|
| 132 | 0.96 | rdf-authoring (agrees) | Verify registry additions against already-read documents; exclude corpus owl:sameAs errors surfaced by a census rather t |
| 161 | 0.98 | rdf-authoring (agrees) | Resolver-link every named entity at its FIRST occurrence; every entity minted in the companion TTL must appear somewhere |
| 205 | 0.90 | rdf-authoring (agrees) | Resolver-IRI-for-every-entity-href governs first-mention prose references, not a jump-list row previewing a full section |
| 242 | 0.81 | rdf-authoring (agrees) | Run the first-reference entity-link check before delivering a freshly-generated page, not only when repairing one |
| 321 | 0.98 | rdf-authoring (agrees) | Ground every minted IRI, fragment ids included, in the source document's URL; for a local-only document presume {default |

## identity-webid (3)

| Step | Confidence | Phrase match | Step name |
|---|---|---|---|
| 273 | 0.84 | identity-webid (agrees) | Markdown article hero is the standard on-behalf-of attribution line, never an I-am-Phenny / I-am-not-Kingsley identity c |
| 296 | 1.00 | identity-webid (agrees) | The remote OBO test's PRIMARY form is dereferencing both WebIDs and checking reciprocal triples (the remote variant of l |
| 297 | 0.99 | identity-webid (agrees) | CORRECTION to Step 296/the MPP incident report: On-Behalf-Of now produces a genuine, value-checked authorization differe |

## virtuoso-sparql (3)

| Step | Confidence | Phrase match | Step name |
|---|---|---|---|
| 195 | 0.96 | rdf-authoring (differs) | Every sample/documented SPARQL query text MUST declare its own PREFIX lines, scope to the actual DAV graph IRI (except c |
| 198 | 0.87 | skill-workflows (differs) | Never claim a specific SPARQL endpoint supports RDF-star/RDF 1.2 quoted-triple syntax (or any similar spec-level feature |
| 199 | 0.99 | - (no phrase hit) | Standing preference: any live/Execute-button SPARQL sample query relying on a Virtuoso query-level pragma (DEFINE input: |

## ontology-generation (2)

| Step | Confidence | Phrase match | Step name |
|---|---|---|---|
| 150 | 0.88 | rdf-authoring (differs) | BLOCKING GATE — checking entities/ontology-terms.ttl before minting a local class is only half the gate; the OTHER half  |
| 187 | 1.00 | rdf-authoring (differs) | Minting even a tiny 2-4-term staging ontology still requires the full owl-property-characterization.ttl + ontology-cross |

## terminology (1)

| Step | Confidence | Phrase match | Step name |
|---|---|---|---|
| 283 | 0.95 | rdf-authoring (differs) | Use the indefinite article: 'a Semantic Web', never the definite 'the Semantic Web', when naming the hyperlink/IRI/SPARQ |

## Stay unrouted: Jev says none, at high confidence (18)

No change proposed. Several cluster around topics the store does not have yet (OSDI, hyperlinking, UI patterns).

| Step | Confidence | Phrase match | Step name |
|---|---|---|---|
| 139 | 0.99 | - (no phrase hit) | Write new scripts in Python by default; use JavaScript/Node only when explicitly required |
| 168 | 0.93 | - (no phrase hit) | FAQ and glossary counts must cover every distinct question-worthy claim and defined term in the source, with 10 as an an |
| 176 | 0.92 | artifact-routing (differs) | Defer the floating-nav's saveState() call until after the expand CSS transition settles, or it persists a corrupt collap |
| 193 | 0.95 | - (no phrase hit) | A shared class's spacing rule must use longhand margin-bottom (not the 3/4-value margin shorthand) or it silently overri |
| 227 | 0.85 | skill-workflows (differs) | A bundled validator's PASS is a floor not an anchor; two artifacts that look independent may have a real derive-from edg |
| 230 | 0.99 | - (no phrase hit) | A CSS comment documenting custom-property names must never contain a literal star-slash (as in an --opal-*/--ols-* glob) |
| 237 | 0.89 | - (no phrase hit) | Never fabricate, reconstruct, or attribute invented comment text to a real person |
| 251 | 0.97 | - (no phrase hit) | Any shell script with set -u and an optional/conditionally-empty array must expand it as ${ARR[@]+"${ARR[@]}"}, never ba |
| 260 | 1.00 | - (no phrase hit) | When a payment/settlement client reports success, verify independently against the underlying ledger before repeating th |
| 272 | 0.99 | html-kg-explorer (differs) | Start the DeepSeek-v4 harness with npx @deepseek-ai/dsh web |
| 274 | 0.97 | - (no phrase hit) | Access X/Twitter content via Playwright (headless Chromium) — not curl |
| 278 | 0.98 | artifact-routing (differs) | Never state a specific network port number for a real live-deployment's connection listener in published document conten |
| 291 | 0.91 | skill-workflows (differs) | When Jacqueline Hand's PRs merge into ai-agent-skills main, check for and bring them into the active working branch with |
| 305 | 0.93 | artifact-routing (differs) | LinkedIn newsletters and articles: render Markdown before posting (native hyperlinks only), put attribution/Phenny signo |
| 325 | 0.83 | memory-management (differs) | When presenting pages, URLs or deployments in a table or list, hyperlink every item as a full clickable URL; never give  |
| 325 | 0.83 | - (no phrase hit) | When presenting pages, URLs or deployments in a table or list, hyperlink every item as a full clickable URL; never give  |
| 355 | 0.87 | - (no phrase hit) | When referencing a Mac doc in Grok Bot chat: open it on the Mac, attach the box copy, and keep file: only as a location  |
| 357 | 0.87 | - (no phrase hit) | Implement every OSDI change in this sequence: 1 localhost, 2 the webdev edition on sol11 (www.webdev), 3 live; the sol11 |

## Cautions before applying

Routing a step into a topic puts it in that topic's intent pack, so every step added is a rule agents will see. Three things in the list above need a decision first:

1. **Superseded or deprecated steps.** Steps 110 (deprecated), 189 (superseded by 243) and 233 (superseded by 236 and 244) carry explicit markers. Routing them would load a retired rule. Suggest leaving them unrouted, or marking them in the topic howto.
2. **A chain of reversals on KG Explorer and SPARQL Workbench placement.** The proposed `html-kg-explorer` list contains steps that point in different directions: 185 (closed), 194 (always visible), 245 (open by default), 307 (closed by default) and 330 (footer workbench closed). From their names, 307 appears to be the latest word and the earlier ones superseded, but I have not verified the chain step by step. Routed together, a pack would show an agent contradictory rules. Check the chain first; route only the current step, or all with their supersession markers.
3. **Two steps share position 325.** The store holds two different steps numbered 325 (both about hyperlinking items in tables and lists), which is a numbering defect in its own right. Neither should be routed until one is renumbered or merged.

Setting aside steps 110, 189, 233, 185, 194 and 245, the clean batch is **45 of the 51 proposed assignments**. The two steps numbered 325 are in the stay-unrouted list and are not affected. That would leave 126 of the 171 steps unrouted for the next rounds.
