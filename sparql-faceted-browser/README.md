# sparql-faceted-browser

Ask questions of any SPARQL endpoint in plain language. The skill answers in chat with live SPARQL. When there is
more to see than a chat can hold, it brings in the **SPARQL Faceted Browser** app, opened on the exact view the
conversation reached.

## Quick start

```bash
cd sparql-faceted-browser

# Answer in chat: rows as a Markdown table, plus the link to the same view in the app
python3 scripts/fct_query.py --type dbo:Film --pv dbo:director=dbr:Christopher_Nolan

# Build a link only
python3 scripts/fct_state.py build --type dbo:Film --pv dbo:director=dbr:Christopher_Nolan --values-of dbo:starring

# Refine a link, or read one someone pasted
python3 scripts/fct_state.py edit "<link>" --pv dbo:starring=dbr:Michael_Caine
python3 scripts/fct_state.py decode "<link>"
```

The scripts need Python 3.8+ and `curl`. They have no other dependencies.

## Which app instance

By default, links open the app hosted on URIBurner:
`https://linkeddata.uriburner.com/DAV/demos/daas/sparql-faceted-browser-claude_opus_5_5.html`

To use another copy (for example, `assets/sparql-faceted-browser.html` served from your own site), name it in the
conversation ("use my browser at https://…"), pass `--app URL`, or set `FCT_APP_URL`. Check a new instance first:

```bash
python3 scripts/fct_state.py check-app https://your-host/path/sparql-faceted-browser.html
```

## Language

`--lang de` returns German labels in chat and adds `&cfg=` to the link, so the app opens that view in German without
changing the viewer's saved settings.

## Where to read more

- `SKILL.md`: when to stay in chat and when to bring in the app, how requests become trails, and the rules.
- `examples/interaction-modalities.md`: one worked example per interaction mode.
- `references/`: the link format, the query templates, the endpoints, and request-to-trail mappings.
