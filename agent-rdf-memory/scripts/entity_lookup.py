"""
Entity Lookup — Wikidata & DBpedia Disambiguation via Jaro-Winkler.

Importable module for workflow-based entity resolution. Searches Wikidata
and/or DBpedia for a given name, computes Jaro-Winkler similarity scores
(jellyfish), and returns matched IRIs with appropriate relationship types
(owl:sameAs, skos:related, rdfs:seeAlso) based on confidence thresholds.

Usage as module:
    from entity_lookup import lookup, EntityMatch

    results = lookup("OpenAI", entity_type="Organization")
    for m in results:
        print(f"{m.iri}  {m.relationship}  ({m.score:.2f})")

Usage as CLI:
    python entity_lookup.py --name "Snowflake Inc." --type Organization
    python entity_lookup.py --name "Tim Berners-Lee" --source wikidata
"""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Optional

try:
    import jellyfish

    def _jaro_winkler(a: str, b: str) -> float:
        return jellyfish.jaro_winkler_similarity(a.lower(), b.lower())

except ImportError:

    def _jaro_winkler(a: str, b: str) -> float:
        """Fallback Jaro-Winkler (no jellyfish). Less accurate but functional."""
        # Simple token-overlap fallback — NOT a real Jaro-Winkler implementation.
        # Install jellyfish for accurate matching: pip install jellyfish
        import difflib

        return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


# ── Thresholds ────────────────────────────────────────────────────────────────
# >= SAMEAS    → owl:sameAs       (near-certain identity)
# >= RELATED   → skos:related     (strong confidence)
# >= SEEALSO   → rdfs:seeAlso     (plausible match, needs human review)
# <  SEEALSO   → discarded

SAMEAS_THRESHOLD = 0.97
RELATED_THRESHOLD = 0.88
SEEALSO_THRESHOLD = 0.78

# ── API Endpoints ─────────────────────────────────────────────────────────────

WIKIDATA_SEARCH = (
    "https://www.wikidata.org/w/api.php"
    "?action=wbsearchentities"
    "&search={query}"
    "&language=en"
    "&limit=10"
    "&format=json"
)

WIKIDATA_ENTITY = "https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"

DBPEDIA_LOOKUP = (
    "https://lookup.dbpedia.org/api/search"
    "?query={query}"
    "&format=json"
    "&maxResults=10"
)

# ── Entity-type → Wikidata instance-of (P31) Q-ID mappings ────────────────────
# Used to scope Wikidata searches when entity_type is provided.
# Expand this map as needed for your domain.

TYPE_WIKIDATA_SCOPE: dict[str, str] = {
    "organization": "Q43229",
    "company": "Q783794",
    "corporation": "Q167037",
    "business": "Q4830453",
    "person": "Q5",
    "software": "Q7397",
    "softwareapplication": "Q166142",
    "programminglanguage": "Q9143",
    "database": "Q8513",
    "city": "Q515",
    "country": "Q6256",
    "product": "Q2424752",
    "event": "Q1656682",
    "conference": "Q2020153",
    "standard": "Q317623",
    "protocol": "Q1323643",
    "academicdiscipline": "Q11862829",
    "university": "Q3918",
    "website": "Q35127",
    "book": "Q571",
    "film": "Q11424",
    "album": "Q482994",
    "concept": "Q151885",
    "technology": "Q11016",
    "ontology": "Q324254",
    "knowledgegraph": "Q33002955",
}

# ── Entity-type → DBpedia ontology class mappings ─────────────────────────────

TYPE_DBPEDIA_SCOPE: dict[str, str] = {
    "organization": "dbo:Organisation",
    "company": "dbo:Company",
    "corporation": "dbo:Company",
    "business": "dbo:Company",
    "person": "dbo:Person",
    "software": "dbo:Software",
    "softwareapplication": "dbo:Software",
    "programminglanguage": "dbo:ProgrammingLanguage",
    "city": "dbo:City",
    "country": "dbo:Country",
    "product": "dbo:MeanOfTransportation",
    "event": "dbo:Event",
    "conference": "dbo:Convention",
    "standard": "dbo:Organisation",
    "university": "dbo:University",
    "website": "dbo:Website",
    "book": "dbo:Book",
    "film": "dbo:Film",
    "album": "dbo:Album",
}


# ── Data types ────────────────────────────────────────────────────────────────


@dataclass
class EntityMatch:
    """One disambiguated external entity."""

    iri: str
    label: str
    score: float
    source: str  # "wikidata" | "dbpedia"
    relationship: str  # "owl:sameAs" | "skos:related" | "rdfs:seeAlso"
    entity_type: Optional[str] = None
    description: Optional[str] = None
    alt_label: Optional[str] = None

    def to_turtle_triple(self, subject_iri: str) -> str:
        """Format as a single Turtle triple for insertion into a TTL file."""
        rel = self.relationship
        obj = f"<{self.iri}>"
        comment = f'  # {self.label} ({self.source}, score={self.score:.3f})'
        return f"    {rel} {obj} .{comment}"

    def to_dict(self) -> dict:
        return {
            "iri": self.iri,
            "label": self.label,
            "score": round(self.score, 4),
            "source": self.source,
            "relationship": self.relationship,
            "entity_type": self.entity_type,
            "description": self.description,
            "alt_label": self.alt_label,
        }


# ── HTTP helpers ──────────────────────────────────────────────────────────────


def _get_json(url: str, timeout: int = 15) -> Optional[dict]:
    """Fetch JSON from URL. Returns None on any error."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "entity-lookup/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def _get_text(url: str, accept: str, timeout: int = 15) -> Optional[str]:
    """Fetch text from URL with Accept header. Returns None on any error."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "entity-lookup/1.0", "Accept": accept},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")
    except Exception:
        return None


# ── Wikidata ──────────────────────────────────────────────────────────────────


def _search_wikidata(query: str, entity_type: Optional[str] = None) -> list[dict]:
    """Return raw Wikidata search hits for *query*, each with id/label/description."""
    url = WIKIDATA_SEARCH.format(query=urllib.parse.quote(query))
    data = _get_json(url)
    if not data:
        return []
    hits = data.get("search", [])

    if entity_type:
        qid_scope = TYPE_WIKIDATA_SCOPE.get(entity_type.lower())
        if qid_scope:
            # Filter: keep only results whose instance-of (P31) or subclass-of
            # matches the scope Q-ID.  We check this lazily — only for candidates
            # that survived the initial text search.
            filtered: list[dict] = []
            for h in hits:
                h_qid = h.get("id", "")
                if _check_wikidata_instance(h_qid, qid_scope):
                    filtered.append(h)
            if filtered:
                hits = filtered
            # If filtering eliminated everything, fall back to raw hits
            # (the entity type scope may be too narrow).

    return [
        {
            "id": h.get("id"),
            "label": h.get("label", ""),
            "description": h.get("description", ""),
            "aliases": h.get("aliases", []),
        }
        for h in hits
    ]


def _check_wikidata_instance(qid: str, scope_qid: str) -> bool:
    """Verify *qid* is an instance of *scope_qid* (P31) or subclass (P279).

    Uses a lightweight SPARQL ASK against the Wikidata endpoint.
    """
    query = (
        "ASK { { wd:%s wdt:P31/wdt:P279* wd:%s . } "
        "UNION { wd:%s wdt:P279* wd:%s . } }" % (qid, scope_qid, qid, scope_qid)
    )
    url = (
        "https://query.wikidata.org/sparql?format=json&query="
        + urllib.parse.quote(query)
    )
    try:
        data = _get_json(url, timeout=10)
        return bool(data and data.get("boolean"))
    except Exception:
        return False


# ── DBpedia ───────────────────────────────────────────────────────────────────


def _search_dbpedia(query: str, entity_type: Optional[str] = None) -> list[dict]:
    """Return raw DBpedia lookup hits for *query*."""
    url = DBPEDIA_LOOKUP.format(query=urllib.parse.quote(query))
    data = _get_json(url)
    if not data:
        return []

    results: list[dict] = []
    for doc in data.get("docs", []):
        types_raw = doc.get("type", [])
        if isinstance(types_raw, str):
            types_raw = [types_raw]

        result = {
            "iri": doc.get("resource", [""])[0] if doc.get("resource") else "",
            "label": doc.get("label", [""])[0] if doc.get("label") else "",
            "description": (
                doc.get("comment", [""])[0] if doc.get("comment") else ""
            ),
            "categories": doc.get("category", []),
            "types": [t for t in types_raw if t],
        }
        if not result["iri"]:
            continue

        # Optional type scoping
        if entity_type:
            scope_cls = TYPE_DBPEDIA_SCOPE.get(entity_type.lower())
            if scope_cls:
                # Check if scope class appears in result types
                scope_short = scope_cls.split(":")[-1]
                if not any(
                    t.endswith("/" + scope_short)
                    or t.endswith("#" + scope_short)
                    or (":" in t and t.split(":")[-1] == scope_short)
                    for t in result["types"]
                ):
                    continue  # Skip — doesn't match requested type

        results.append(result)

    return results


# ── Scoring ───────────────────────────────────────────────────────────────────


def _score_and_assign(
    query: str, candidates: list[dict], source: str
) -> list[EntityMatch]:
    """Score candidates against *query*, assign relationship, sort desc."""
    matches: list[EntityMatch] = []
    q = query.lower()

    for c in candidates:
        label = c.get("label", "")
        if not label:
            continue

        # Primary score: Jaro-Winkler on exact labels
        score = _jaro_winkler(q, label)

        # Boost: check aliases too
        for alias in c.get("aliases", []) or []:
            alias_score = _jaro_winkler(q, alias)
            if alias_score > score:
                score = alias_score

        if score < SEEALSO_THRESHOLD:
            continue

        rel = (
            "owl:sameAs"
            if score >= SAMEAS_THRESHOLD
            else "skos:related"
            if score >= RELATED_THRESHOLD
            else "rdfs:seeAlso"
        )

        iri = (
            f"http://www.wikidata.org/entity/{c['id']}"
            if source == "wikidata"
            else c.get("iri", "")
        )
        if not iri:
            continue

        matches.append(
            EntityMatch(
                iri=iri,
                label=label,
                score=score,
                source=source,
                relationship=rel,
                description=c.get("description"),
                alt_label=c.get("aliases", [None])[0] if c.get("aliases") else None,
            )
        )

    matches.sort(key=lambda m: m.score, reverse=True)
    return matches


# ── Public API ────────────────────────────────────────────────────────────────


def lookup(
    name: str,
    entity_type: Optional[str] = None,
    data_source: str = "both",
    threshold: float = SEEALSO_THRESHOLD,
) -> list[EntityMatch]:
    """Find Wikidata / DBpedia IRIs matching *name* with Jaro-Winkler scoring.

    Parameters
    ----------
    name : str
        Entity label to disambiguate (e.g. "Snowflake Inc.", "Tim Berners-Lee").
    entity_type : str, optional
        Scope the search by type (e.g. "Organization", "Person", "Software").
        Uses predefined Wikidata P31 Q-ID and DBpedia ontology class mappings.
    data_source : str
        "wikidata", "dbpedia", or "both" (default).
    threshold : float
        Minimum Jaro-Winkler score (0.0–1.0). Default 0.78.

    Returns
    -------
    list[EntityMatch]
        Sorted by score descending.  Empty list if nothing found above threshold.
    """
    all_matches: list[EntityMatch] = []

    if data_source in ("wikidata", "both"):
        hits = _search_wikidata(name, entity_type)
        all_matches.extend(_score_and_assign(name, hits, "wikidata"))

    if data_source in ("dbpedia", "both"):
        hits = _search_dbpedia(name, entity_type)
        all_matches.extend(_score_and_assign(name, hits, "dbpedia"))

    # Re-sort combined results
    all_matches.sort(key=lambda m: m.score, reverse=True)

    # Apply caller's threshold (respecting the global floor)
    effective = max(threshold, SEEALSO_THRESHOLD)
    return [m for m in all_matches if m.score >= effective]


def best(
    name: str,
    entity_type: Optional[str] = None,
    data_source: str = "both",
) -> Optional[EntityMatch]:
    """Return the single best match, or None."""
    results = lookup(name, entity_type, data_source)
    return results[0] if results else None


# ── CLI ───────────────────────────────────────────────────────────────────────


def _cli():
    import argparse

    parser = argparse.ArgumentParser(
        description="Wikidata / DBpedia entity disambiguation via Jaro-Winkler",
    )
    parser.add_argument(
        "--name", "-n", required=True, help="Entity name to look up"
    )
    parser.add_argument(
        "--type", "-t", dest="entity_type", default=None,
        help="Entity type for scoped search (e.g. Organization, Person, Software)",
    )
    parser.add_argument(
        "--source", "-s", default="both",
        choices=["wikidata", "dbpedia", "both"],
    )
    parser.add_argument(
        "--threshold", default=SEEALSO_THRESHOLD, type=float,
        help=f"Minimum Jaro-Winkler score (default {SEEALSO_THRESHOLD})",
    )
    parser.add_argument(
        "--json", "-j", action="store_true",
        help="Output as JSON array",
    )
    parser.add_argument(
        "--subject", default=None,
        help="If set, output Turtle triples with this IRI as subject",
    )
    args = parser.parse_args()

    results = lookup(
        name=args.name,
        entity_type=args.entity_type,
        data_source=args.source,
        threshold=args.threshold,
    )

    if args.subject and results:
        for m in results:
            print(m.to_turtle_triple(args.subject))
    elif args.json:
        print(json.dumps([m.to_dict() for m in results], indent=2))
    else:
        if not results:
            print(f"No matches found for '{args.name}'", file=sys.stderr)
            sys.exit(1)
        for i, m in enumerate(results):
            src_tag = f"[{m.source}]"
            print(
                f"{i+1}. {m.label:40s} {src_tag:12s} "
                f"{m.relationship:16s} {m.score:.4f}  → {m.iri}"
            )
            if m.description:
                print(f"   {m.description[:100]}")


if __name__ == "__main__":
    _cli()
