"""Parse RDF documents and extract KG Explorer data + narrative sections."""

from __future__ import annotations
import re
from pathlib import Path
from rdflib import Graph, URIRef, BNode, Literal
from rdflib.namespace import RDF, RDFS, OWL, XSD, Namespace


SCHEMA = Namespace("http://schema.org/")
PROV = Namespace("http://www.w3.org/ns/prov#")
KNOWN_CLASS_URIS = {
    RDF.Property, RDFS.Class, OWL.Class, OWL.NamedIndividual,
    SCHEMA.Person, SCHEMA.Organization, SCHEMA.Article,
    SCHEMA.FAQPage, SCHEMA.Question, SCHEMA.DefinedTermSet,
    SCHEMA.DefinedTerm, SCHEMA.HowTo, SCHEMA.HowToStep,
    SCHEMA.SoftwareApplication, SCHEMA.SoftwareSourceCode,
    SCHEMA.Thing, SCHEMA.CreativeWork,
}


def classify(node_uri: URIRef, g: Graph) -> str:
    """Classify a URIRef node as Class, Property, or Instance."""
    types = set(g.objects(node_uri, RDF.type))
    if not types:
        # Check if it's used as a predicate
        if (None, node_uri, None) in g or (node_uri, RDF.type, RDF.Property) in g:
            return "Property"
        # Check if it's used as a class
        for s, p, o in g:
            if p == RDF.type and o == node_uri:
                return "Class"
        return "Instance"

    for t in types:
        if t in (RDFS.Class, OWL.Class):
            return "Class"
        if t == RDF.Property:
            return "Property"

    for t in types:
        if t in KNOWN_CLASS_URIS:
            return "Instance"

    return "Instance"


def shorten(uri: URIRef, g: Graph) -> str:
    """Try to shorten a URI using namespace prefixes from the graph."""
    for prefix, ns in g.namespaces():
        if str(uri).startswith(str(ns)):
            return f"{prefix}:{str(uri)[len(str(ns)):]}"
    # Last resort: extract local name
    uri_str = str(uri)
    if "#" in uri_str:
        return uri_str.split("#")[-1]
    return uri_str.split("/")[-1] if "/" in uri_str else uri_str


def extract_label(uri: URIRef, g: Graph) -> str:
    """Extract the best label for a URI."""
    for label in g.objects(uri, RDFS.label):
        return str(label)
    for label in g.objects(uri, SCHEMA.name):
        return str(label)
    return shorten(uri, g)


def _truncate_at_word_boundary(text: str, limit: int = 600) -> str:
    """Truncate to `limit` chars at a word boundary with a visible ellipsis,
    never mid-word with no indication. A silent [:N] slice cuts words in
    half (e.g. '...the nine SP' where the source said 'SPARQL') and gives
    the reader no signal that anything was cut -- it reads as a typo or a
    generation bug, not an intentional length limit. See
    howto/card-description-truncation-gate.ttl."""
    text = str(text)
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut.rstrip(",.;:—- ") + "…"


def extract_description_full(uri: URIRef, g: Graph) -> str:
    """Untruncated counterpart to extract_description().

    The 600-char cap in extract_description() exists so a GRID of many cards
    keeps roughly uniform heights (howto/card-description-truncation-gate.ttl).
    That rationale does not apply when a single entity IS a section's whole
    content and is rendered full-width — there capping silently discards the
    argument. Callers pick the variant that matches the layout they render.
    """
    for desc in g.objects(uri, RDFS.comment):
        return str(desc)
    for desc in g.objects(uri, SCHEMA.description):
        return str(desc)
    for desc in g.objects(uri, SCHEMA.text):
        return str(desc)
    return ""


def extract_description(uri: URIRef, g: Graph) -> str:
    """Extract description/comment/body text for a URI.

    Checks rdfs:comment and schema:description first (short summaries),
    then falls back to schema:text (the body of HowToStep, Answer, etc.,
    which carries the actual content and must not be dropped).
    """
    for desc in g.objects(uri, RDFS.comment):
        return _truncate_at_word_boundary(desc)
    for desc in g.objects(uri, SCHEMA.description):
        return _truncate_at_word_boundary(desc)
    for desc in g.objects(uri, SCHEMA.text):
        return _truncate_at_word_boundary(desc)
    return ""


def _step_position(step, g: Graph) -> int:
    """schema:position for ordering HowToStep entities; unpositioned/blank
    steps sort last rather than raising or silently reordering randomly."""
    if isinstance(step, URIRef):
        for pos in g.objects(step, SCHEMA.position):
            try:
                return int(pos)
            except (TypeError, ValueError):
                pass
    return 10**9


def build_kgdata(rdf_path: str | Path) -> dict:
    """Build kgData payload from an RDF file.

    Returns: {'nodes': [...], 'links': [...]}
    """
    g = Graph()
    g.parse(str(rdf_path))

    nodes_map: dict[str, dict] = {}
    links: list[dict] = []
    seen_predicates: set[str] = set()

    for s, p, o in g:
        if isinstance(s, BNode) or isinstance(o, BNode) and isinstance(p, URIRef):
            continue

        pred_short = shorten(p, g) if isinstance(p, URIRef) else str(p)
        seen_predicates.add(pred_short)

        subj_id = str(s) if isinstance(s, URIRef) else f"_:{s}"
        obj_id = str(o) if isinstance(o, URIRef) else f"_:{o}"

        # Add subject node
        if subj_id not in nodes_map and isinstance(s, URIRef):
            nodes_map[subj_id] = {
                "id": subj_id,
                "group": classify(s, g),
                "label": extract_label(s, g),
                "desc": extract_description(s, g),
                "iri": str(s),
            }

        # Add object node
        if obj_id not in nodes_map and isinstance(o, URIRef):
            nodes_map[obj_id] = {
                "id": obj_id,
                "group": classify(o, g),
                "label": extract_label(o, g),
                "desc": extract_description(o, g),
                "iri": str(o),
            }

        # Add link
        if isinstance(p, URIRef) and isinstance(s, (URIRef, BNode)) and isinstance(o, (URIRef, BNode)):
            link = {
                "source": subj_id,
                "target": obj_id,
                "predicate": pred_short,
                "label": pred_short,
            }
            links.append(link)

    nodes = list(nodes_map.values())

    # Orphan check
    incident_ids: set[str] = set()
    for link in links:
        incident_ids.add(link["source"] if isinstance(link["source"], str) else link["source"])
        incident_ids.add(link["target"] if isinstance(link["target"], str) else link["target"])
    orphans = [n for n in nodes if n["id"] not in incident_ids]
    if orphans:
        orphan_ids = [n["id"] for n in orphans]
        print(f"Warning: {len(orphans)} orphan nodes found: {orphan_ids}")

    return {
        "nodes": nodes,
        "links": links,
    }


def _extract_deck(g: Graph, main_entity) -> dict:
    """Extract the data slots of the synopsis executive-summary deck.

    Generic, RDF-driven, and fully optional (graceful degradation):
      - meta:          article author / publisher / publication date
      - spotlight:     instances of document-ontology classes (classes declared
                       rdfs:isDefinedBy an owl:Ontology in the graph) that carry
                       a name and description, grouped by class; the instance
                       the article schema:about's is featured (tag = its
                       schema:alternateName, fallback "Featured")
      - citations:     URIRef objects of the article's schema:citation
      - quotation:     the first schema:Quotation in the graph (text + author)

    Any slot that cannot be populated is simply omitted by the renderer.
    """
    deck = {
        "meta": {"author_name": "", "author_iri": "", "publisher_name": "",
                 "publisher_iri": "", "date": ""},
        "spotlight_groups": [],
        "citation_chips": [],
        "quotation": None,
    }
    if main_entity is None or not isinstance(main_entity, URIRef):
        return deck

    for a in g.objects(main_entity, SCHEMA.author):
        if isinstance(a, URIRef):
            deck["meta"]["author_iri"] = str(a)
            deck["meta"]["author_name"] = extract_label(a, g)
            break
    for p in g.objects(main_entity, SCHEMA.publisher):
        if isinstance(p, URIRef):
            deck["meta"]["publisher_iri"] = str(p)
            deck["meta"]["publisher_name"] = extract_label(p, g)
            break
    for d in g.objects(main_entity, SCHEMA.datePublished):
        deck["meta"]["date"] = str(d)[:10]
        break

    onto_iris = set(g.subjects(RDF.type, OWL.Ontology))
    doc_classes = set()
    for cls in set(g.subjects(RDF.type, RDFS.Class)) | set(g.subjects(RDF.type, OWL.Class)):
        if isinstance(cls, URIRef) and onto_iris & set(g.objects(cls, RDFS.isDefinedBy)):
            doc_classes.add(cls)

    about_iri = g.value(main_entity, SCHEMA.about)
    about_iri = str(about_iri) if isinstance(about_iri, URIRef) else None

    for cls in doc_classes:
        items = []
        for inst in g.subjects(RDF.type, cls):
            if not isinstance(inst, URIRef):
                continue
            name = extract_label(inst, g)
            desc = extract_description(inst, g)
            if not name or not desc:
                continue
            pos = g.value(inst, SCHEMA.position)
            try:
                pos = int(pos)
            except (TypeError, ValueError):
                pos = 9999
            items.append({
                "name": name,
                "desc": _truncate_at_word_boundary(desc, 150),
                "iri": str(inst),
                "pos": pos,
                "featured": about_iri is not None and str(inst) == about_iri,
            })
        if not items:
            continue
        items.sort(key=lambda i: i["pos"])
        title = next((str(n) for n in g.objects(cls, SCHEMA.name)), "")
        if not title:
            title = next((str(l) for l in g.objects(cls, RDFS.label)), "")
        if not title:
            title = "Key Concepts"
        tag = ""
        if any(i["featured"] for i in items):
            feat = next(i for i in items if i["featured"])
            tag = next((str(t) for t in g.objects(URIRef(feat["iri"]), SCHEMA.alternateName)), "")
            if not tag:
                tag = "Featured"
        # Cap displayed rows so the spotlight sidebar stays proportionate to
        # the lede/body column instead of stretching the whole deck to the
        # panel's height (a class with a large instance count -- e.g. one row
        # per correction pattern -- otherwise dwarfs a short abstract).
        total = len(items)
        cap = 14
        overflow = max(0, total - cap)
        if overflow and not any(i["featured"] for i in items[cap:]):
            items = items[:cap]
        elif overflow:
            featured_idx = next(i for i, it in enumerate(items) if it["featured"])
            if featured_idx >= cap:
                items = items[: cap - 1] + [items[featured_idx]]
            else:
                items = items[:cap]
        deck["spotlight_groups"].append({
            "title": title,
            "class_iri": str(cls),
            "items": items,
            "tag": tag,
            "overflow_count": overflow,
        })

    for c in g.objects(main_entity, SCHEMA.citation):
        if isinstance(c, URIRef):
            label = extract_label(c, g)
            if label:
                deck["citation_chips"].append({"name": label, "iri": str(c)})
                if len(deck["citation_chips"]) >= 8:
                    break

    for q in g.subjects(RDF.type, SCHEMA.Quotation):
        if not isinstance(q, URIRef):
            continue
        text = str(g.value(q, SCHEMA.text) or "").strip()
        if not text:
            continue
        qd = {"text": text, "author_name": "", "author_iri": ""}
        for a in g.objects(q, SCHEMA.author):
            if isinstance(a, URIRef):
                qd["author_iri"] = str(a)
                qd["author_name"] = extract_label(a, g)
            break
        deck["quotation"] = qd
        break

    return deck


def extract_narrative(rdf_path: str | Path, base_iri: str) -> dict:
    """Extract narrative sections (FAQ, glossary, HowTo, People, Orgs) from RDF."""
    g = Graph()
    g.parse(str(rdf_path))

    result = {
        "synopsis": None,
        "faq": [],
        "glossary": [],
        "howto": [],
        "howto_groups": [],
        "people": [],
        "organizations": [],
        "sections": [],
        "source_code": [],
    }

    # Synopsis: the main article/report entity — prefer schema:Article, then
    # any subject with the most schema:hasPart links (the de facto hub node).
    main_entity = None
    for candidate in g.subjects(RDF.type, SCHEMA.Article):
        main_entity = candidate
        break
    if main_entity is None:
        best_count = -1
        for s in set(g.subjects(SCHEMA.hasPart, None)):
            count = len(list(g.objects(s, SCHEMA.hasPart)))
            if count > best_count:
                best_count = count
                main_entity = s
    if main_entity is not None:
        headline = ""
        for h in g.objects(main_entity, SCHEMA.headline):
            headline = str(h)
            break
        if not headline:
            headline = extract_label(main_entity, g) if isinstance(main_entity, URIRef) else ""
        abstract = ""
        for a in g.objects(main_entity, SCHEMA.abstract):
            abstract = str(a)
            break
        if not abstract:
            for a in g.objects(main_entity, SCHEMA.articleBody):
                abstract = str(a)[:600]
                break
        if not abstract:
            # Last-resort fallback: schema:description is commonly set on the
            # main entity even when schema:abstract/articleBody are not. Using
            # it here prevents a silent, sparse-looking synopsis deck (kicker +
            # heading + spotlight panel + CTA, but no lede/body prose at all)
            # when an author supplies only schema:description. See
            # preferences.ttl step-synopsisRequiresAbstract /
            # howto/synopsis-deck-design-system.ttl.
            for a in g.objects(main_entity, SCHEMA.description):
                abstract = str(a)
                break
        if headline or abstract:
            result["synopsis"] = {
                "headline": headline,
                "abstract": abstract,
                "iri": str(main_entity) if isinstance(main_entity, URIRef) else "",
            }

    # FAQ
    for faq in g.subjects(RDF.type, SCHEMA.FAQPage):
        for q_item in g.objects(faq, SCHEMA.hasPart):
            q_text = extract_label(q_item, g) if isinstance(q_item, URIRef) else str(q_item)
            a_iri = None
            for a_item in g.objects(q_item, SCHEMA.acceptedAnswer):
                a_iri = a_item
                break
            a_text = ""
            for txt in g.objects(a_item, SCHEMA.text):
                a_text = str(txt)
                break
            for txt in g.objects(a_item, RDFS.comment):
                if not a_text:
                    a_text = str(txt)
                break
            if q_text and a_text:
                result["faq"].append({
                    "question": q_text,
                    "answer": a_text,
                    "iri": str(q_item) if isinstance(q_item, URIRef) else "",
                })

    # Fallback: look for Question nodes directly
    if not result["faq"]:
        for q in g.subjects(RDF.type, SCHEMA.Question):
            q_text = extract_label(q, g) or ""
            for a in g.objects(q, SCHEMA.acceptedAnswer):
                a_text = ""
                for txt in g.objects(a, SCHEMA.text):
                    a_text = str(txt)
                    break
                if q_text and a_text:
                    result["faq"].append({
                        "question": q_text,
                        "answer": a_text,
                        "iri": str(q) if isinstance(q, URIRef) else "",
                    })

    # Glossary
    for term_set in g.subjects(RDF.type, SCHEMA.DefinedTermSet):
        for term in g.objects(term_set, SCHEMA.hasPart):
            term_text = extract_label(term, g) if isinstance(term, URIRef) else str(term)
            term_desc = extract_description(term, g) if isinstance(term, URIRef) else ""
            if term_text and term_desc:
                result["glossary"].append({
                    "term": term_text,
                    "definition": term_desc,
                    "iri": str(term) if isinstance(term, URIRef) else "",
                })

    # Fallback glossary: DefinedTerm nodes
    if not result["glossary"]:
        for term in g.subjects(RDF.type, SCHEMA.DefinedTerm):
            term_text = extract_label(term, g) or ""
            desc = extract_description(term, g) or ""
            if term_text:
                result["glossary"].append({
                    "term": term_text,
                    "definition": desc,
                    "iri": str(term) if isinstance(term, URIRef) else "",
                })

    # HowTo — grouped by parent schema:HowTo entity so a document with
    # several distinct procedures (e.g. a build pipeline plus multiple
    # scenario-specific guides) renders as separate titled, separately
    # numbered guides rather than one flattened, misleadingly continuous
    # step sequence. Each group carries its own name/description/iri plus
    # a "steps" list; "howto" itself stays a flat list of all steps across
    # every group for any caller that only needs the ungrouped step count.
    howto_subjects = sorted(
        g.subjects(RDF.type, SCHEMA.HowTo),
        key=lambda h: (-len(list(g.objects(h, SCHEMA.step))), extract_label(h, g) or str(h)),
    )
    for howto in howto_subjects:
        group_name = extract_label(howto, g) or ""
        group_desc = extract_description(howto, g) or ""
        steps = []
        for step in sorted(
            g.objects(howto, SCHEMA.step),
            key=lambda s: _step_position(s, g),
        ):
            step_text = extract_label(step, g) if isinstance(step, URIRef) else str(step)
            step_desc = extract_description(step, g) if isinstance(step, URIRef) else ""
            if step_text:
                entry = {
                    "step": step_text,
                    "description": step_desc,
                    "iri": str(step) if isinstance(step, URIRef) else "",
                }
                steps.append(entry)
                result["howto"].append(entry)
        if steps:
            result.setdefault("howto_groups", []).append({
                "name": group_name,
                "description": group_desc,
                "iri": str(howto) if isinstance(howto, URIRef) else "",
                "steps": steps,
            })

    # People
    for person in g.subjects(RDF.type, SCHEMA.Person):
        name = extract_label(person, g)
        if name:
            desc = extract_description(person, g)
            result["people"].append({
                "name": name,
                "description": desc,
                "iri": str(person) if isinstance(person, URIRef) else "",
            })

    # Organizations
    for org in g.subjects(RDF.type, SCHEMA.Organization):
        name = extract_label(org, g)
        if name:
            desc = extract_description(org, g)
            result["organizations"].append({
                "name": name,
                "description": desc,
                "iri": str(org) if isinstance(org, URIRef) else "",
            })

    # Generic narrative content sections (article-body substance beyond
    # FAQ/glossary/HowTo/People/Organizations) — e.g. a schema:CreativeWork
    # or schema:ItemList that is schema:hasPart of the main article, whose
    # own children carry the actual analysis. Without this, an infographic
    # can pass every structural check while silently dropping the source's
    # substantive narrative (see generator-script-output-not-a-substitute-
    # for-contract-check.ttl for the recurring pattern this closes).
    if main_entity is not None:
        excluded_types = {SCHEMA.FAQPage, SCHEMA.DefinedTermSet, SCHEMA.HowTo, OWL.Ontology}
        excluded_iris = set()
        for faq in g.subjects(RDF.type, SCHEMA.FAQPage):
            excluded_iris.add(faq)
        for ts in g.subjects(RDF.type, SCHEMA.DefinedTermSet):
            excluded_iris.add(ts)
        for ht in g.subjects(RDF.type, SCHEMA.HowTo):
            excluded_iris.add(ht)
        for onto in g.subjects(RDF.type, OWL.Ontology):
            excluded_iris.add(onto)

        for part in g.objects(main_entity, SCHEMA.hasPart):
            if not isinstance(part, URIRef) or part in excluded_iris:
                continue
            part_types = set(g.objects(part, RDF.type))
            if not (part_types & {SCHEMA.CreativeWork, SCHEMA.ItemList}) or (part_types & excluded_types):
                continue
            sec_name = extract_label(part, g)
            if not sec_name:
                continue
            sec_abstract = ""
            for a in g.objects(part, SCHEMA.abstract):
                sec_abstract = str(a)
                break
            if not sec_abstract:
                for a in g.objects(part, SCHEMA.description):
                    sec_abstract = str(a)
                    break

            # Children: entities that declare schema:isPartOf this section
            # (schema:hasPart / schema:itemListElement give the same set via
            # the inverse-relationship contract), excluding media objects AND
            # schema:SoftwareSourceCode. The latter exclusion mirrors the
            # top-level SoftwareSourceCode skip further below (see its comment):
            # a query/code entity nested under an arbitrary container section
            # (e.g. a "Demo Instance Data and SPARQL Queries" section wrapping
            # several SPARQL recipes) would otherwise render as a second,
            # non-interactive, read-only card duplicating the exact same query
            # that already appears as a live Execute card in the canonical
            # #sparql-explorer workbench below it — the container-nesting case
            # slips past that guard because it checks top-level rdf:type
            # SoftwareSourceCode subjects, not schema:hasPart children of an
            # unrelated section. Caught 2026-08-12 on a document whose "Demo
            # Instance Data and SPARQL Queries" section duplicated its own
            # SPARQL Workbench sample-query cards one-for-one.
            child_iris = set(g.subjects(SCHEMA.isPartOf, part))
            child_iris |= set(g.objects(part, SCHEMA.hasPart))
            child_iris |= set(g.objects(part, SCHEMA.itemListElement))
            children = []
            for child in child_iris:
                if not isinstance(child, URIRef) or child == part:
                    continue
                child_types = set(g.objects(child, RDF.type))
                if child_types & {SCHEMA.ImageObject, SCHEMA.VideoObject, SCHEMA.AudioObject, SCHEMA.SoftwareSourceCode}:
                    continue
                c_name = extract_label(child, g)
                if not c_name:
                    continue
                c_desc = extract_description(child, g)
                c_pos = None
                for p in g.objects(child, SCHEMA.position):
                    try:
                        c_pos = int(p)
                    except (TypeError, ValueError):
                        pass
                    break
                # schema:PropertyValue children carry a headline figure in
                # schema:value (optionally qualified by schema:unitText) —
                # captured here so the assembler can render them as a stat
                # band rather than as prose cards. See
                # howto/rdf-driven-figures-and-stat-band.ttl.
                c_value = next((str(v) for v in g.objects(child, SCHEMA.value)), "")
                c_unit = next((str(u) for u in g.objects(child, SCHEMA.unitText)), "")
                children.append({
                    "name": c_name,
                    "description": c_desc,
                    "description_full": extract_description_full(child, g),
                    "iri": str(child),
                    "position": c_pos if c_pos is not None else 9999,
                    "value": c_value,
                    "unit": c_unit,
                    "is_metric": SCHEMA.PropertyValue in child_types and bool(c_value),
                })
            children.sort(key=lambda c: c["position"])

            # An inline SVG figure carried as a schema:image LITERAL (rather
            # than a URL or ImageObject) is trusted author-controlled markup,
            # rendered raw — the same trust model schema:abstract already uses
            # for the synopsis deck. A literal beginning with "<svg" is an
            # unambiguous signal: no real image URL can start that way, so
            # this cannot collide with conventional schema:image usage.
            sec_figure = ""
            for img in g.objects(part, SCHEMA.image):
                if isinstance(img, Literal) and str(img).strip().startswith("<svg"):
                    sec_figure = str(img).strip()
                    break

            sec_pos = None
            for sp in g.objects(part, SCHEMA.position):
                try:
                    sec_pos = int(sp)
                except (TypeError, ValueError):
                    pass
                break

            if sec_abstract or children or sec_figure:
                result["sections"].append({
                    "name": sec_name,
                    "abstract": sec_abstract,
                    "iri": str(part),
                    "items": children,
                    "figure": sec_figure,
                    "position": sec_pos if sec_pos is not None else 9999,
                })

        # Narrative order is an editorial decision, so honour an explicit
        # schema:position on the sections themselves. Without it the order
        # falls out of rdflib's hasPart iteration, which is not a guaranteed
        # contract — stable in practice for a freshly parsed file, but not
        # something a document's reading order should depend on. Sections
        # without a position keep their original relative order (stable sort).
        result["sections"].sort(key=lambda s: s.get("position", 9999))

    # Source-code / query entities (e.g. SPARQL, Cypher) — rendered as their
    # own accordion showcase, not just left invisible inside a nested
    # schema:hasPart chain the shallow section renderer can't reach.
    for code in g.subjects(RDF.type, SCHEMA.SoftwareSourceCode):
        name = extract_label(code, g) or ""
        lang = ""
        for l in g.objects(code, SCHEMA.programmingLanguage):
            lang = str(l)
            break
        text = ""
        for t in g.objects(code, SCHEMA.text):
            text = str(t)
            break
        if not text:
            continue
        comment = ""
        for c in g.objects(code, RDFS.comment):
            comment = str(c)
            break
        target = ""
        for tg in g.objects(code, SCHEMA.target):
            target = str(tg)
            break
        result["source_code"].append({
            "name": name or lang or "Query",
            "language": lang,
            "text": text,
            "comment": comment,
            "target": target,
            "iri": str(code),
        })

    # Synopsis executive-summary deck slots (meta, spotlight groups, citation
    # chips, quotation) -- generic and optional; see _extract_deck docstring.
    result["deck"] = _extract_deck(g, main_entity)

    return result


def get_base_iri(rdf_path: str | Path) -> str:
    """Extract the base IRI from an RDF file if available."""
    g = Graph()
    g.parse(str(rdf_path))
    for s in set(g.subjects()):
        if isinstance(s, URIRef):
            uri = str(s)
            if "#" in uri:
                return uri.split("#")[0] + "#"
            return uri.rsplit("/", 1)[0] + "/"
    return "https://linkedin.com/pulse/"


def get_entity_count(rdf_path: str | Path) -> int:
    """Return the number of triples in the RDF file."""
    g = Graph()
    g.parse(str(rdf_path))
    return len(g)


def validate_orphans(kgdata: dict) -> list[str]:
    """Return list of orphan node IDs (nodes with no incident links)."""
    incident: set[str] = set()
    for link in kgdata["links"]:
        src = link["source"] if isinstance(link["source"], str) else link["source"]["id"]
        tgt = link["target"] if isinstance(link["target"], str) else link["target"]["id"]
        incident.add(src)
        incident.add(tgt)
    orphans = [n["id"] for n in kgdata["nodes"] if n["id"] not in incident]
    return orphans
