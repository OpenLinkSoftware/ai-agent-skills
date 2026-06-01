# Product Catalog — Offer IRI Mappings with Prices

Resolved from the following TTL sources:

- `/Users/kidehen/Documents/Management/Marketing/Virtuoso/Virtuoso Data Web/Virtuoso-Enterprise-Offers-Licenses-Prices.ttl`
- `/Users/kidehen/Documents/Management/Marketing/Virtuoso/Virtuoso Data Web/OPALOffers-Licenses-Prices-Knowledge-Graph-Access.ttl`
- `/Users/kidehen/Documents/Management/Marketing/UDA/UDA Data Web/Lite Edition/UDALiteOffers-Licenses-Prices-Oct-2024.ttl`

## How to Use

When the user says "I want to purchase the JDBC to ODBC bridge driver", match
the friendly name against the **Match Names** below. Use the corresponding
**Offer IRI** as `ACP_ITEM_ID`.

**Price columns:**
- **Special Price** — Current promotional price (if available)
- **Retail Price** — Standard retail price

All prices in **USD**.

---

## Virtuoso Enterprise

| Match Names | Offer IRI | Special Price | Retail Price |
|---|---|---|---|
| Virtuoso Enterprise, Virtuoso 8 Enterprise, Enterprise License | `http://data.openlinksw.com/oplweb/offer/Offer-virtuoso-8-Enterprise-WKSSVR-ANY#this` | Negotiable | Negotiable |

---

## OPAL Knowledge Graph Access

| Match Names | Offer IRI | Special Price | Retail Price |
|---|---|---|---|
| OPAL demo graph access, demo knowledge graph, ods-qa graph access | `http://data.openlinksw.com/oplweb/offer/DemoGraphAccessOfferOds-qa#this` | Subscription | Subscription |

---

## UDA Lite Edition — ODBC Drivers

### SQL Server / Sybase

| Match Names | Offer IRI | Special Price | Retail Price |
|---|---|---|---|
| SQL Server ODBC personal, SQL Server Lite personal, SQL Server driver personal | `http://data.openlinksw.com/oplweb/offer/Offer-UDALT-WKS-anyos-odbc-sql-personal-2024-02#this` | **$49.99** | $99.99 |
| SQL Server ODBC workgroup, SQL Server Lite workgroup | `http://data.openlinksw.com/oplweb/offer/Offer-UDALT-WKSSVR-anyos-odbc-sql-workgroup-2024-02#this` | **$99.99** | $524.99 |
| SQL Server ODBC department, SQL Server Lite department | `http://data.openlinksw.com/oplweb/offer/Offer-UDALT-WKSSVR-anyos-odbc-sql-department-2024-02#this` | **$1,312.99** | $3,937.24 |

### JDBC Data Sources

| Match Names | Offer IRI | Special Price | Retail Price |
|---|---|---|---|
| JDBC ODBC personal, JDBC driver personal, JDBC Lite personal | `http://data.openlinksw.com/oplweb/offer/Offer-UDALT-WKS-anyos-odbc-jdbc-personal-2024-02#this` | **$49.99** | $99.99 |
| JDBC ODBC workgroup, JDBC driver workgroup | `http://data.openlinksw.com/oplweb/offer/Offer-UDALT-WKSSVR-anyos-odbc-jdbc-workgroup-2024-02#this` | **$99.99** | $524.99 |
| JDBC ODBC department, JDBC driver department | `http://data.openlinksw.com/oplweb/offer/Offer-UDALT-WKSSVR-anyos-odbc-jdbc-department-2024-02#this` | **$1,312.99** | $3,937.24 |

### Informix 11.x

| Match Names | Offer IRI | Special Price | Retail Price |
|---|---|---|---|
| Informix 11 ODBC personal, Informix driver personal | `http://data.openlinksw.com/oplweb/offer/Offer-UDALT-WKS-anyos-odbc-inf11-personal-2024-02#this` | **$49.99** | $99.99 |
| Informix 11 ODBC workgroup, Informix driver workgroup | `http://data.openlinksw.com/oplweb/offer/Offer-UDALT-WKSSVR-anyos-odbc-inf11-workgroup-2024-02#this` | **$99.99** | $524.99 |
| Informix 11 ODBC department, Informix driver department | `http://data.openlinksw.com/oplweb/offer/Offer-UDALT-WKSSVR-anyos-odbc-inf11-department-2024-02#this` | **$1,312.99** | $3,937.24 |

---

## UDA Lite Edition — JDBC Drivers

### JDBC to ODBC Bridge

| Match Names | Offer IRI | Special Price | Retail Price |
|---|---|---|---|
| **JDBC to ODBC bridge driver**, JDBC-ODBC bridge, JDBC ODBC bridge personal | `http://data.openlinksw.com/oplweb/offer/Offer-UDALT-WKS-anyos-jdbc-odbc-personal-2024-01#this` | **$49.99** | $99.99 |
| JDBC to ODBC bridge workgroup, JDBC-ODBC bridge workgroup | `http://data.openlinksw.com/oplweb/offer/Offer-UDALT-WKSSVR-anyos-jdbc-odbc-workgroup-2024-01#this` | **$99.99** | $524.99 |
| JDBC to ODBC bridge department, JDBC-ODBC bridge department | `http://data.openlinksw.com/oplweb/offer/Offer-UDALT-WKSSVR-anyos-jdbc-odbc-department-2024-01#this` | **$1,312.99** | $3,937.24 |

---

## Additional UDA Lite Drivers (Partial Catalog)

### Oracle 12c

| Match Names | Offer IRI | Special Price | Retail Price |
|---|---|---|---|
| Oracle 12c ODBC personal | `http://data.openlinksw.com/oplweb/offer/Offer-UDALT-WKS-anyos-odbc-ora12-personal-2024-02#this` | **$49.99** | $99.99 |

---

## Fallback Resolution

If the user's product name does not match any entry above:

1. Ask the user for the **full offer IRI** (e.g., `http://data.openlinksw.com/oplweb/offer/...`)
2. Or ask the user for the **product page URL** and attempt to extract the offer IRI from any `<link rel="alternate">` or embedded JSON-LD
3. If neither is available, prompt: "Please provide the offer IRI or navigate to the product page and paste the URL."

## Price Validation Note

When a checkout returns a **total of $0.00**, verify the offer IRI version:
- The `2024-02` versions of some offers may return $0 pricing (unconfigured)
- The `2024-01` versions have validated working prices
- If checkout total is $0, retry with the alternate year version or contact the ACP administrator
