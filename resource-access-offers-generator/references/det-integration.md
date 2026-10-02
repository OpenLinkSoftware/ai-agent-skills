# ProtectedOffer DET Integration

The `ProtectedOffer` DAV DET (Virtuoso) applies this skill's **File Access** contract automatically, server-side, whenever a file is uploaded to a collection mounted with it. The DET doesn't call the skill. It re-implements the File Access template in Virtuoso/PL because the `prompts/*.md` templates are empty (see "Known gaps").

Source:

- `virtuoso-engine/binsrc/yacutia/sql/DET_ProtectedOffer.sql` (Conductor VAD)
- `ods-virtuoso/briefcase/sql/DET_ProtectedOffer.sql` (Briefcase VAD copy; identical apart from `wa_exec_no_error`)

## What happens on upload

1. The file is stored at its own DAV path, and world read/write/execute are stripped from its permissions.
2. A `DAV_QUEUE` job (`DB.DBA.ProtectedOffer__process_aq`) builds the Offer/License/PriceSpecification bundle, following `SKILL.md`:
   - IRIs per `offer-iri-patterns.md` (`/offer/…Offer{host_suffix}#this`, `/license/…License{host_suffix}#this`, `/offer-unitprice/…PriceSpecification#this`)
   - the File Access Product template
   - an `oplofr:{OfferIdentifier}Offer` type specific to the resource
   - `SubscriptionOffer`/`SubscriptionLicense`/`oplofr:interval` only for subscriptions
   - canonical Duration IRIs (`#perpetual`, `#ongoing-subscription`, `#annual`)
   - `@en` on prose literals
   - a validity window of 3 months
   - a `shop.openlinksw.com` cart URL
3. It adds a buyer-only `oplacl:ConditionalGroup` and `acl:Authorization`. These are adapted from the Graph Access authorization block, with `oplacl:hasScope oplacl:Dav` and `acl:accessTo` set to the file.
4. The Turtle is parsed into a temporary graph, and SPARQL ASK checks cover the constraints the shop and ACL depend on (`PO_CHECKS` lists any that fail).
5. The Turtle is saved as `{OfferIdentifier}{host_suffix}-FileAccessOffer.ttl` in the offers collection, which is publicly readable so shops can `LOAD` it.
6. The same group and rule are registered live through VAL (`acl_group_new` → `acl_group_addCondition` → `acl_rule_new`, scope `VAL.DBA.get_dav_scope ()`).
7. The notice goes to the `dav` account's e-mail. It includes one `SPARQL define get:soft "no-sponge" LOAD <offer.ttl> INTO <urn:opl:shop:offering:sponging:cache:official>` per configured shop, and the command for this skill's full SHACL gate.

Deleting the file removes the VAL rule, marks the offer `withdrawn`, and sends the admin the shop-side `DELETE` to run.

## host_short for any host

The fixed profiles win: `linkeddata.uriburner.com` → `URIBurner`, `ods-qa.openlinksw.com` → `ods-qa`, `localhost` → `localhost`. Otherwise the value is derived from the domain:

- a `*.openlinksw.com` sub-domain → PascalCase of its first label (`demo.openlinksw.com` → `Demo`);
- any other host → PascalCase of its registrable domain (`kingsley.idehen.net` → `IdehenNet`).

This reproduces every `host_short` used in the prior-art offer files. The `hostShort` setting overrides it.

## Settings

These are collection DET params (`virt:ProtectedOffer-<name>`). The same name set on a resource overrides the collection value, and changing one queues a regeneration.

| Name | Default |
|---|---|
| `price` | required |
| `pricingModel` | `one-time` (or `subscription`) |
| `interval` | `month` (or `year`) |
| `currency` | `USD` |
| `baseUrl` | `https://{URIQA DefaultHost}` |
| `hostShort` | derived (above) |
| `shops` | `shop.openlinksw.com,ods-qa.openlinksw.com` |
| `offersPath` | `{collection}-offers/` |
| `image` | `controlled-access-to-data-assets.jpg` |
| `title`, `description` | resource only |

Mount from iSQL:

```sql
DB.DBA.DAV_MAKE_DIR ('/DAV/paid/', http_dav_uid (), http_admin_gid (), '110100000NN');
DB.DBA.ProtectedOffer_CONFIGURE (DB.DBA.DAV_SEARCH_ID ('/DAV/paid/', 'C'), vector ('price', '2.99', 'pricingModel', 'one-time'));
```

Regenerate after fixing a setting:

```sql
DB.DBA.ProtectedOffer_REGENERATE ('/DAV/paid/report.html');
```

## Verification

```sql
SELECT PO_RES_PATH, PO_STATUS, PO_OFFER_IRI, PO_OFFER_URL, PO_ACL_GROUP, PO_CHECKS, PO_NOTIFIED FROM DB.DBA.PROTECTED_OFFER;
SELECT RES_FULL_PATH, RES_PERMS FROM WS.WS.SYS_DAV_RES WHERE RES_FULL_PATH LIKE '/DAV/paid/%';
```

```bash
curl -sk -o /dev/null -w '%{http_code}\n' https://{host}/DAV/paid/report.html
python3 scripts/validate-offers-shacl.py {OfferIdentifier}{host_suffix}-FileAccessOffer.ttl --type file
```

The anonymous GET should return 401, and the SHACL gate should pass with 0 violations.

## Known gaps

- **`prompts/*.md` are empty (0 bytes)** — `file-access-offer-prompt.md`, `graph-access-offer-prompt.md` and `api-access-offer-prompt.md`. The operative contract is `SKILL.md` + `shacl/`, and the DET follows those.
- **Blank nodes.** `FileAccessOfferShape` requires `skos:related` to be a blank node (`sh:nodeKind sh:BlankNode`), and the Product template uses blank nodes for `schema:provider` and `schema:hasPart`. This conflicts with the no-blank-nodes rule. It is kept for shop compatibility, and the shape needs fixing here.
- **File Access authorization.** This skill still says the authorization block is Graph Access only. The DET always emits it for files, with scope `oplacl:Dav`.
- **Purchase check not yet tested end to end.** The purchase-gated read (a buyer's WebID with a purchase-cache entry reaching the file through the VAL rule) still needs a test against a shop that replicates purchases.
