# NAICS Identifier Pattern Reference

## Canonical URL Structure

The US Census Bureau provides canonical NAICS code lookup pages. Always use this URL pattern for `schema:identifier` on industry vertical instances:

```
https://www.census.gov/naics/?input={code}&year=2022&details={code}
```

Both `input` and `details` query parameters receive the same NAICS code value.
The `year=2022` parameter references the most recent NAICS revision year.

---

## Usage in Turtle

Use `schema:naics` for the plain code string and `schema:identifier` for the canonical Census Bureau URL. Both appear together on the same instance:

```turtle
:insuranceBrokerageVertical a :InsuranceBrokerageIndustry ;
    schema:naics "524210" ;
    schema:identifier "https://www.census.gov/naics/?input=524210&year=2022&details=524210" .
```

**Never** use `schema:identifier` alone without `schema:naics`, and **never** use the obsolete `?code={code}` pattern.

---

## Common NAICS Codes for AI Autopilot Disruption Verticals

| Code | Description | Canonical `schema:identifier` |
|---|---|---|
| `524210` | Insurance Agencies and Brokerages | `https://www.census.gov/naics/?input=524210&year=2022&details=524210` |
| `524291` | Title Insurance | `https://www.census.gov/naics/?input=524291&year=2022&details=524291` |
| `524298` | All Other Insurance-Related Activities | `https://www.census.gov/naics/?input=524298&year=2022&details=524298` |
| `541211` | Offices of Certified Public Accountants | `https://www.census.gov/naics/?input=541211&year=2022&details=541211` |
| `541213` | Tax Preparation Services | `https://www.census.gov/naics/?input=541213&year=2022&details=541213` |
| `541214` | Payroll Services | `https://www.census.gov/naics/?input=541214&year=2022&details=541214` |
| `541219` | Other Accounting Services | `https://www.census.gov/naics/?input=541219&year=2022&details=541219` |
| `541110` | Offices of Lawyers | `https://www.census.gov/naics/?input=541110&year=2022&details=541110` |
| `541191` | Title Abstract and Settlement Offices | `https://www.census.gov/naics/?input=541191&year=2022&details=541191` |
| `541611` | Administrative Management and General Management Consulting Services | `https://www.census.gov/naics/?input=541611&year=2022&details=541611` |
| `561110` | Office Administrative Services | `https://www.census.gov/naics/?input=561110&year=2022&details=561110` |
| `561310` | Employment Placement Agencies | `https://www.census.gov/naics/?input=561310&year=2022&details=561310` |

---

## Deprecated Pattern — Never Use

```turtle
# WRONG — deprecated URL pattern
schema:identifier "https://www.census.gov/naics/?code=524210" .
```

---

## Related Reference

See [`identifier-patterns.md`](identifier-patterns.md) for `schema:identifier` conventions across all entity types.
