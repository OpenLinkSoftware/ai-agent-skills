# Business & Market Analysis Prompt — RDF-Turtle Output

Use this template for business strategy posts, X/social threads, market analyses, and industry deep-dives.
Substitute all `{placeholders}` before sending.

---

## Placeholders

| Placeholder | Description |
|---|---|
| `{url}` | URL of the original post or content being analysed |
| `{post-url}` | Used as the base namespace — all hash-URIs derive from this |
| `{current date}` | ISO 8601 date (e.g. `2026-03-13`) for `schema:dateCreated` |

> **Note**: `{post-url}` and `{url}` are often the same value. Use `{post-url}#` as the Turtle `@prefix :` base.

---

## Prompt Template

```
You are an expert in semantic web modeling, RDF/Turtle serialization, and schema.org + lightweight ontology design.
Given the post at {url} and its thread (which discusses AI-driven "autopilots" disrupting services markets by selling outcomes rather than tools, starting with outsourced intelligence-heavy tasks such as NDA drafting, insurance brokerage (~$140–200B labor TAM), and accounting (~$50–80B labor TAM), with structural shortages like the loss of ~340k U.S. accountants, data compounding enabling eventual judgment handling, debates around copilots vs. full autopilots, the innovator's dilemma, and founder collaboration opportunities),
produce a **comprehensive RDF/Turtle document** that represents the full business & strategy analysis.
Follow ALL of these final design requirements exactly:
1. Base URI: Use relative hash URIs grounded in {post-url} as the namespace prefix :
2. Use schema.org as the primary vocabulary, supplemented by:
   - skos: for glossary/concept definitions
   - org: for organizations
   - dbo: for selected DBpedia cross-references (via rdfs:seeAlso)
   - rdfs: for class/property definitions
3. Create a small custom lightweight ontology in the same namespace:
   - Define :Industry as rdfs:Class (base class for verticals)
   - Define two subclass rdfs:Class resources: :InsuranceBrokerageIndustry and :AccountingIndustry
   - Define two custom properties on :Industry:
     - :hasLaborTAM      (range xsd:string)
     - :hasAutomationReadiness (range xsd:string)
   - Create explicit instances of these classes (e.g. :insuranceBrokerageVertical a :InsuranceBrokerageIndustry ; ...) to hold concrete data (TAM values, readiness, NAICS, offers, DBpedia links). Do NOT put instance data directly on the class definitions.
4. Use low-redundancy schema.org identifier modeling (Option 3 style):
   - Use dedicated properties when they exist: schema:naics (on industry instances), schema:isbn (on the book), schema:identifier with plain literal for unambiguous codes (e.g. "US" for ISO 3166-1 alpha-2)
   - For NAICS codes, always use the Census Bureau canonical lookup URL as schema:identifier (see NAICS identifier pattern below)
   - Avoid unnecessary schema:PropertyValue wrappers unless genuinely required for disambiguation or extra metadata
5. Core entities that must be included:
   - The main analysis CreativeWork (:analysis)
   - Author (:grok), original post reference (:originalXPost), Julien Bek
   - :aiAutopilotDisruption (Product), :marketDisruptionAction, :servicesMarketDisruption
   - Example task :ndaExample
   - Concrete vertical instances :insuranceBrokerageVertical and :accountingVertical (with TAM, readiness, naics, offers WithCoverage/Rillet autopilots)
   - Organizations :withCoverage and :rillet + their autopilots
   - :shortageEvent (U.S. accountant shortage)
   - :unitedStates with ISO code
   - :threadReplies, :cursorExample, :scalingChallenges
   - :innovatorsDilemma (CreativeWork with isbn "9780060521998")
6. Mandatory structured sections (all must be present and complete):
   - schema:FAQPage (:faqSection) with **exactly 12** schema:Question items (:q1–:q12)
   - skos:ConceptScheme + schema:DefinedTermSet (:glossarySection) with **exactly 10** terms (:termAutopilot through :termVerticalMapping)
   - schema:HowTo (:howtoSection) with **exactly 7** schema:HowToStep items (:step1–:step7)
7. Include all original details:
   - Labor TAM ranges exactly as stated ($140-200B insurance, $50-80B accounting)
   - Automation readiness "High" for both
   - 340,000 accountant shortage statistic
   - Data compounding explanation
   - Outcome-as-a-Service model
   - Innovator's dilemma application
   - Copilot → autopilot transition challenges
   - Founder collaboration via tagging / datasets
8. Keep descriptions concise yet precise; avoid unnecessary verbosity in literals.
9. Output **only** the complete, valid Turtle document inside a single code block. Do not include explanations, comments outside Turtle, or any other text before/after the code block.
Current date for metadata: {current date}.
```

---

## NAICS Identifier Pattern

For all `schema:identifier` values on industry vertical instances, use the US Census Bureau canonical NAICS lookup URL:

```
https://www.census.gov/naics/?input={code}&year=2022&details={code}
```

**Examples:**

| NAICS Code | Description | `schema:identifier` value |
|---|---|---|
| `524210` | Insurance Agencies and Brokerages | `https://www.census.gov/naics/?input=524210&year=2022&details=524210` |
| `541211` | Offices of Certified Public Accountants | `https://www.census.gov/naics/?input=541211&year=2022&details=541211` |
| `541213` | Tax Preparation Services | `https://www.census.gov/naics/?input=541213&year=2022&details=541213` |
| `541110` | Offices of Lawyers | `https://www.census.gov/naics/?input=541110&year=2022&details=541110` |

Use `schema:naics` for the plain code string and `schema:identifier` for the canonical lookup URL. Both should appear together:

```turtle
:insuranceBrokerageVertical a :InsuranceBrokerageIndustry ;
    schema:naics "524210" ;
    schema:identifier "https://www.census.gov/naics/?input=524210&year=2022&details=524210" .
```

See [`references/naics-identifier-pattern.md`](../references/naics-identifier-pattern.md) for the full reference.

---

## Post-Generation Checklist

After generating output, verify:

- [ ] `@prefix :` is set to `{post-url}#`
- [ ] Lightweight ontology present: `:Industry`, `:InsuranceBrokerageIndustry`, `:AccountingIndustry`, `:hasLaborTAM`, `:hasAutomationReadiness`
- [ ] Instance data on instances (not on class definitions)
- [ ] Both `schema:naics` (plain code) and `schema:identifier` (Census URL) present on each vertical instance
- [ ] Exactly 12 FAQ questions (`:q1`–`:q12`)
- [ ] Exactly 10 glossary terms
- [ ] Exactly 7 HowTo steps (`:step1`–`:step7`)
- [ ] TAM values exact: `"$140-200B"` and `"$50-80B"`
- [ ] `schema:isbn "9780060521998"` on `:innovatorsDilemma`
- [ ] `schema:identifier "US"` on `:unitedStates`
- [ ] Output is only the Turtle code block — no surrounding explanatory text
- [ ] No `schema:PropertyValue` wrappers unless strictly necessary
