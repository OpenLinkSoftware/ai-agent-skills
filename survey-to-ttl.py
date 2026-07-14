#!/usr/bin/env python3
"""
Generate Turtle RDF knowledge graph from Google Sheets survey data.
Converts survey responses into linked data with custom ontology
(cross-reference gate compliant), SKOS concept schemes, and
fragment-based IRI scheme.

Usage: python3 survey-to-ttl.py
Output: /Users/kidehen/Documents/RDF_DATA/data-survey-2026.ttl
"""

import csv
import io
import os
import re
import sys
import urllib.request

# ── Configuration ──────────────────────────────────────────────

BASE_IRI = "https://docs.google.com/spreadsheets/d/1y41pbKPR-HBlMZFMi95fXBydm3BNcrUmiu8vtDtaGgQ/edit?gid=1924769362"
CSV_URL = "https://docs.google.com/spreadsheets/d/1y41pbKPR-HBlMZFMi95fXBydm3BNcrUmiu8vtDtaGgQ/export?format=csv&gid=1924769362"
OUTPUT_PATH = "/Users/kidehen/Documents/RDF_DATA/data-survey-2026.ttl"

# ── Question definitions ──────────────────────────────────────
# (col_index, slug, class_name, property_name, question_label)

QUESTIONS = [
    (1, "leadership-reality",     "LeadershipReality",      "hasLeadershipReality",
     'When you hear "lack of leadership direction" in data, which best describes your reality?'),
    (2, "infrastructure-owner",   "InfrastructureOwner",    "hasInfrastructureOwner",
     "Who owns data infrastructure in your org? (technical assets - jobs, transformations, pipelines)"),
    (3, "product-owner",          "ProductOwner",           "hasProductOwner",
     "Who owns data products in your org? (things stakeholders consume - datasets, dashboards, models)"),
    (4, "requirements-arrival",   "RequirementsProcess",    "hasRequirementsProcess",
     "How do requirements for data work typically arrive?"),
    (5, "firefighting-trigger",   "FirefightingTrigger",    "hasFirefightingTrigger",
     "What's the most common trigger for firefighting on your team?"),
    (6, "reactive-work-pct",      "ReactiveWorkPercentage", "hasReactiveWorkPct",
     "Roughly what percentage of your work week goes to unplanned or reactive work?"),
    (7, "fix-one-problem",        "FixOneProblem",          "wouldFixProblem",
     "If you could fix ONE organizational problem tomorrow, which would it be?"),
    (8, "ai-impact",              "AIImpact",               "aiImpact",
     "Has AI made your organizational dysfunction better or worse?"),
]

# Free-text column (index 9) — "organizational-change" (schema:text)
FREE_TEXT_COL = 9
DATE_COL = 0

# ── Cross-references (verified) ───────────────────────────────
# DBpedia resources verified via HTTP HEAD/GET

DBPEDIA = {
    "LeadershipReality":      "http://dbpedia.org/resource/Leadership",
    "InfrastructureOwner":    "http://dbpedia.org/resource/Information_technology_management",
    "ProductOwner":           "http://dbpedia.org/resource/Product_management",
    "RequirementsProcess":    "http://dbpedia.org/resource/Requirements_management",
    "FirefightingTrigger":    "http://dbpedia.org/resource/Troubleshooting",
    "ReactiveWorkPercentage": "http://dbpedia.org/resource/Workload",
    "FixOneProblem":          "http://dbpedia.org/resource/Problem_solving",
    "AIImpact":              "http://dbpedia.org/resource/Artificial_intelligence",
}

# Wikidata cross-refs (additional)
WIKIDATA = {
    "LeadershipReality":      "http://www.wikidata.org/entity/Q6555377",
    "InfrastructureOwner":    "http://www.wikidata.org/entity/Q4116373",
    "ProductOwner":           "http://www.wikidata.org/entity/Q1644155",
    "RequirementsProcess":    "http://www.wikidata.org/entity/Q1195108",
    "FirefightingTrigger":    "http://www.wikidata.org/entity/Q1076425",
    "ReactiveWorkPercentage": "http://www.wikidata.org/entity/Q6597783",
    "FixOneProblem":          "http://www.wikidata.org/entity/Q648944",
    "AIImpact":              "http://www.wikidata.org/entity/Q11660",
}


# ── Helpers ───────────────────────────────────────────────────

def fetch_csv(url: str) -> str:
    """Fetch CSV from Google Sheets export URL."""
    req = urllib.request.Request(url, headers={"User-Agent": "SurveyKG/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def slugify(text: str) -> str:
    """Convert answer text to URL-safe slug for fragment IRI."""
    s = text.lower().strip()
    s = re.sub(r"[.,'\"()!?;:%]+", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"[–—]", "-", s)
    s = re.sub(r"-+", "-", s)
    s = s.strip("-")
    s = s[:90].rstrip("-")
    return s


def escape_ttl_string(s: str) -> str:
    """Escape a string for Turtle literal (with possible newlines)."""
    s = s.replace("\\", "\\\\")
    s = s.replace('"', '\\"')
    s = s.replace("\n", "\\n")
    s = s.replace("\r", "\\r")
    return s


def ttl_lines(text: str, indent: str = "\n    ") -> str:
    """Format a long literal for Turtle with line breaks and indentation."""
    return text


# ── CSV parsing ───────────────────────────────────────────────

def parse_csv(raw: str) -> tuple[list[str], list[list[str]]]:
    """Parse CSV, return (headers, rows)."""
    reader = csv.reader(io.StringIO(raw))
    all_rows = list(reader)
    if not all_rows:
        sys.exit("Error: empty CSV")
    headers = all_rows[0]
    data_rows = all_rows[1:]  # skip header row
    return headers, data_rows


# ── Turtle generation ─────────────────────────────────────────

def build(output_path: str) -> None:
    raw = fetch_csv(CSV_URL)
    headers, rows = parse_csv(raw)

    if not rows:
        sys.exit("Error: no data rows in CSV")

    # Extract unique answer options per question
    concept_sets = {}
    for col_idx, slug, class_name, prop_name, _ in QUESTIONS:
        options = set()
        for row in rows:
            if col_idx < len(row):
                val = row[col_idx].strip()
                if val:
                    options.add(val)
        concept_sets[slug] = sorted(options)

    # Question lookups
    qlabel_map = {slug: label for _, slug, _, _, label in QUESTIONS}
    qclass_map = {slug: cls for _, slug, cls, _, _ in QUESTIONS}
    qprop_map  = {slug: prop for _, slug, _, prop, _ in QUESTIONS}

    with open(output_path, "w", encoding="utf-8") as f:

        def w(s: str = "") -> None:
            f.write(s + "\n")

        # ── Prefix declarations ──
        w("@base <{}> .".format(BASE_IRI))
        w("@prefix : <{}#> .".format(BASE_IRI))
        w("@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .")
        w("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .")
        w("@prefix owl: <http://www.w3.org/2002/07/owl#> .")
        w("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .")
        w("@prefix schema: <http://schema.org/> .")
        w("@prefix skos: <http://www.w3.org/2004/02/skos/core#> .")
        w("@prefix dct: <http://purl.org/dc/terms/> .")
        w("@prefix dbr: <http://dbpedia.org/resource/> .")
        w("@prefix wd: <http://www.wikidata.org/entity/> .")
        w()

        # ── Document-level entity ──
        w("[] a schema:Survey ;")
        w('    schema:name "Data Team Organizational Dysfunction Survey"@en ;')
        w('    schema:description "Survey capturing organizational dysfunction in data teams — leadership direction, infrastructure ownership, product ownership, requirements processes, firefighting triggers, reactive work percentage, priority fixes, and AI impact."@en ;')
        w('    schema:dateCreated "2026-05-26"^^xsd:date .')
        w()

        # ── Ontology entity ──
        w(":ontology a owl:Ontology ;")
        w('    rdfs:label "Data Team Dysfunction Survey Ontology"@en ;')
        w('    rdfs:comment "Custom ontology for survey responses about data team organizational dysfunction. Covers leadership reality, infrastructure ownership, product ownership, requirements processes, firefighting triggers, reactive work, priority fixes, and AI impact."@en ;')
        w('    rdfs:isDefinedBy <{}> ;'.format(BASE_IRI))
        w("    owl:versionInfo \"1.0\" ;")
        w('    schema:name "Data Team Dysfunction Survey Ontology"@en ;')
        w('    dct:created "2026-05-26"^^xsd:date .')
        w()

        # ── Custom Classes ──

        # SurveyResponse
        w(":SurveyResponse a rdfs:Class ;")
        w('    rdfs:label "Survey Response"@en ;')
        w('    rdfs:comment "A single response to the Data Team Organizational Dysfunction Survey."@en ;')
        w("    rdfs:subClassOf schema:Review ;")
        w("    rdfs:isDefinedBy :ontology ;")
        w("    rdfs:seeAlso dbr:Survey_methodology ;")
        w("    rdfs:seeAlso wd:Q7312870 .")
        w()

        # Per-question answer range classes
        for _, slug, class_name, prop_name, _ in QUESTIONS:
            dbr_resource = DBPEDIA.get(class_name, "")
            wd_resource = WIKIDATA.get(class_name, "")

            # Human-readable label from class name
            label = re.sub(r"([a-z])([A-Z])", r"\1 \2", class_name)

            w(":{} a rdfs:Class ;".format(class_name))
            w('    rdfs:label "{}"@en ;'.format(label))
            w('    rdfs:comment "Answer options for the survey question: {}"@en ;'.format(
                re.sub(r'(["\\])', r'\\\1', qlabel_map[slug])))
            w("    rdfs:subClassOf schema:Thing ;")
            w("    rdfs:isDefinedBy :ontology ;")
            if dbr_resource:
                w("    rdfs:seeAlso <{}> ;".format(dbr_resource))
            if wd_resource:
                w("    rdfs:seeAlso <{}> ;".format(wd_resource))
            # Remove trailing semicolon
            f.seek(f.tell() - 2)  # back up over " ;\n"
            w(" .")
            w()

        # ── Custom Properties ──

        # Object properties (one per question)
        for _, slug, class_name, prop_name, _ in QUESTIONS:
            label = prop_name.replace("has", "").replace("would", "").replace("ai", "AI ")
            dbr_resource = DBPEDIA.get(class_name, "")

            w(":{} a owl:ObjectProperty, owl:FunctionalProperty, owl:AsymmetricProperty, owl:IrreflexiveProperty ;".format(prop_name))
            w('    rdfs:label "{}"@en ;'.format(
                re.sub(r"([a-z])([A-Z])", r"\1 \2", prop_name).lower()))
            w('    rdfs:comment "Links a SurveyResponse to its answer for the question about {}."@en ;'.format(
                re.sub(r'(["\\])', r'\\\1', qlabel_map[slug]).lower()))
            w("    rdfs:domain :SurveyResponse ;")
            w("    rdfs:range :{} ;".format(class_name))
            w("    rdfs:isDefinedBy :ontology ;")
            if dbr_resource:
                w("    rdfs:seeAlso <{}> ;".format(dbr_resource))
            w("    rdfs:seeAlso skos:Concept ;")
            # Remove trailing semicolon
            f.seek(f.tell() - 2)
            w(" .")
            w()

        # Datatype property for organizational change text
        w(":organizationalChange a rdf:Property, owl:DatatypeProperty ;")
        w('    rdfs:label "organizational change"@en ;')
        w('    rdfs:comment "Free-text description of an organizational change that meaningfully affected the data team."@en ;')
        w("    rdfs:domain :SurveyResponse ;")
        w("    rdfs:range xsd:string ;")
        w("    rdfs:isDefinedBy :ontology ;")
        w("    rdfs:seeAlso schema:text .")
        w()

        # ── SKOS Concept Schemes (one per question) ──

        for _, slug, class_name, prop_name, question_label in QUESTIONS:
            question_label_clean = re.sub(r'(["\\])', r'\\\1', question_label)
            w("<#question/{}> a skos:ConceptScheme, schema:Question ;".format(slug))
            w('    skos:prefLabel "{}"@en ;'.format(question_label_clean))
            w('    schema:text "{}"@en ;'.format(question_label_clean))
            w("    rdfs:isDefinedBy :ontology ;")
            w("    rdfs:seeAlso dbr:Question .")
            w()

        # ── SKOS Concepts (answer options) ──

        for _, slug, class_name, prop_name, _ in QUESTIONS:
            options = concept_sets[slug]
            for opt in options:
                concept_slug = slugify(opt)
                w("<#concept/{}/{}> a skos:Concept ;".format(slug, concept_slug))
                w('    skos:prefLabel "{}"@en ;'.format(escape_ttl_string(opt)))
                w("    skos:inScheme <#question/{}> ;".format(slug))
                w("    rdfs:isDefinedBy :ontology ;")
                w("    rdfs:seeAlso <#question/{}> .".format(slug))
                w()

        # ── Response entities ──

        data_rows = rows  # already defined via headers, data_rows = rows
        for i, row in enumerate(data_rows):
            row_num = i + 2  # row 2 = first data row in sheet (row 1 = header)
            w("# ── Response R-{} ──".format(row_num))
            w(":R-{} a :SurveyResponse ;".format(row_num))

            # Date
            if DATE_COL < len(row):
                date_val = row[DATE_COL].strip()
                if date_val:
                    w('    schema:dateCreated "{}"^^xsd:date ;'.format(date_val))

            # Concept answers
            for col_idx, slug, class_name, prop_name, _ in QUESTIONS:
                if col_idx < len(row):
                    val = row[col_idx].strip()
                    if val:
                        concept_slug = slugify(val)
                        w("    :{} <#concept/{}/{}> ;".format(prop_name, slug, concept_slug))

            # Free-text
            if FREE_TEXT_COL < len(row):
                free_val = row[FREE_TEXT_COL].strip()
                if free_val:
                    escaped = escape_ttl_string(free_val)
                    w('    :organizationalChange """{}"""@en ;'.format(escaped))

            # End the response triples
            w("    rdfs:isDefinedBy :ontology .")
            w()

    print("Wrote {} rows to {}".format(len(data_rows), output_path))
    print("Output: " + output_path)


if __name__ == "__main__":
    build(OUTPUT_PATH)
