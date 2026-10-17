# Interaction modes: worked examples

Each example shows what the user says, what the skill decides, the command it runs, and what the user gets back.
The commands run from the skill folder. All rows and counts below come from real runs against DBpedia on
2026-10-15; live data changes over time. Long app links are shown as `#s=…`. In a real answer, paste the full
link the script printed, never a shortened one.

| # | Mode | User says |
|---|---|---|
| 1 | Answer in chat | "How many films has Christopher Nolan directed?" |
| 2 | List + link | "List them." |
| 3 | Summon the app | "I want to explore settlements in Nigeria." |
| 4 | Refine | "Only the ones starring Michael Caine." |
| 5 | Facets / distribution | "How are those settlements spread across states?" |
| 6 | Pivot | "Which actors in Nolan's films were born in London?" |
| 7 | Describe | "Tell me about Benin City." |
| 8 | Read a pasted link back | "What is this view? <link>" |
| 9 | Language | "Same, but in German." |
| 10 | Another app instance | "Use my browser at <your-app-url>" |

---

## 1. Answer in chat

> **User:** How many films has Christopher Nolan directed?

**Skill decides:** this is a fact with a one-line answer, so it stays in chat. First it resolves the name to an IRI.

```bash
python3 scripts/fct_query.py --text "Christopher Nolan" --type dbo:Person --limit 3
```
```
| entity |
|---|
| [Christopher Nolan](http://dbpedia.org/resource/Christopher_Nolan) |
| [Christopher Nolan](http://dbpedia.org/resource/Christopher_Nolan_(author)) |
| [Ronnie Nolan](http://dbpedia.org/resource/Ronnie_Nolan) |
```

The first row is the filmmaker. When a name is ambiguous like this, ask, or pick by context.

```bash
python3 scripts/fct_query.py --type dbo:Film --pv dbo:director=dbr:Christopher_Nolan --what count
```
```
| count |
|---|
| 16 |
```

> **Answer:** DBpedia lists **16** films directed by [Christopher Nolan](http://dbpedia.org/resource/Christopher_Nolan).
> [Open in SPARQL Faceted Browser](https://linkeddata.uriburner.com/DAV/demos/daas/sparql-faceted-browser-claude_opus_5_5.html#s=…)

## 2. List + link

> **User:** List them.

**Skill decides:** 16 rows fit in chat, so it shows a table and the link.

```bash
python3 scripts/fct_query.py --type dbo:Film --pv dbo:director=dbr:Christopher_Nolan --limit 20
```
```
| entity |
|---|
| [Inception](http://dbpedia.org/resource/Inception) |
| [The Dark Knight Rises](http://dbpedia.org/resource/The_Dark_Knight_Rises) |
| [Batman Begins](http://dbpedia.org/resource/Batman_Begins) |
| [Interstellar (film)](http://dbpedia.org/resource/Interstellar_(film)) |
| … 12 more …
```

The answer is the table plus one line: `[Open in SPARQL Faceted Browser](…the printed link…)`.

## 3. Summon the app

> **User:** I want to explore settlements in Nigeria.

**Skill decides:** "explore" plus a large set means the app. It sizes the set first.

```bash
python3 scripts/fct_query.py --type dbo:Settlement --pv dbo:country=dbr:Nigeria --what count
```
```
| count |
|---|
| 1,572 |
```

> **Answer:** There are **1,572** settlements in Nigeria in DBpedia, too many to read in chat. I've opened them in
> the faceted browser, where you can narrow them by type, state or any property. Tell me what to narrow by and
> I'll do it here too.
> [Open in SPARQL Faceted Browser](https://linkeddata.uriburner.com/DAV/demos/daas/sparql-faceted-browser-claude_opus_5_5.html#s=…)

In the Claude desktop app, open the link in the built-in browser pane so the view appears beside the conversation.
Elsewhere, give it as a link.

## 4. Refine

> **User:** (after example 2) Only the ones starring Michael Caine.

**Skill decides:** this adds one filter to the same trail, so it edits the previous link instead of starting over.

```bash
python3 scripts/fct_state.py edit "<link from example 2>" --pv dbo:starring=dbr:Michael_Caine
python3 scripts/fct_query.py --link "<the new link>"
```
```
| entity |
|---|
| [Inception](http://dbpedia.org/resource/Inception) |
| [The Dark Knight Rises](http://dbpedia.org/resource/The_Dark_Knight_Rises) |
| [Batman Begins](http://dbpedia.org/resource/Batman_Begins) |
| [Interstellar (film)](http://dbpedia.org/resource/Interstellar_(film)) |
| [Tenet (film)](http://dbpedia.org/resource/Tenet_(film)) |
| [The Dark Knight](http://dbpedia.org/resource/The_Dark_Knight) |
| [The Prestige](http://dbpedia.org/resource/The_Prestige_(film)) |
```

That's 7 films. `edit` keeps the app instance and language of the link it is given.

## 5. Facets / distribution

> **User:** (after example 3) How are those settlements spread across states?

**Skill decides:** this is a distribution. If the property isn't known yet, the property facet reveals it.

```bash
python3 scripts/fct_query.py --type dbo:Settlement --pv dbo:country=dbr:Nigeria --what props --limit 25
```

Among the results, "subdivision" (`dbo:subdivision`) covers 1,520 of the 1,572 members.

```bash
python3 scripts/fct_query.py --type dbo:Settlement --pv dbo:country=dbr:Nigeria --values-of dbo:subdivision --limit 6
```
```
| value | members |
|---|---|
| [Akwa Ibom](http://dbpedia.org/resource/Akwa_Ibom_State) | 200 |
| [Kaduna](http://dbpedia.org/resource/Kaduna_State) | 92 |
| [Delta](http://dbpedia.org/resource/Delta_State) | 71 |
| [Anambra](http://dbpedia.org/resource/Anambra_State) | 66 |
| [Imo](http://dbpedia.org/resource/Imo_State) | 59 |
| [Abia](http://dbpedia.org/resource/Abia_State) | 55 |
```

The link opens the app on the **Values · subdivision** tab, so the user can click a state to narrow to it.

## 6. Pivot

> **User:** Which actors in Nolan's films were born in London?

**Skill decides:** this moves from films to the actors in them (`--pivot`), then filters the actors.

```bash
python3 scripts/fct_query.py --type dbo:Film --pv dbo:director=dbr:Christopher_Nolan \
  --pivot dbo:starring --pv dbo:birthPlace=dbr:London --limit 6
```
```
| entity |
|---|
| [Tom Hardy](http://dbpedia.org/resource/Tom_Hardy) |
| [Rebecca Hall](http://dbpedia.org/resource/Rebecca_Hall) |
| [Fionn Whitehead](http://dbpedia.org/resource/Fionn_Whitehead) |
| [John Nolan](http://dbpedia.org/resource/John_Nolan_(British_actor)) |
```

Filters always attach to the most recent set, so `--pv dbo:birthPlace=…` applies to the actors, not the films. In
the app the trail reads *Films → starring → born in London*.

## 7. Describe

> **User:** Tell me about Benin City.

**Skill decides:** this is one entity. It fetches its description and summarizes the notable facts in prose rather
than pasting every row.

```bash
python3 scripts/fct_query.py --describe dbr:Benin_City --limit 200
```
```
| direction | property | value | values folded |
|---|---|---|---|
| out | [description](http://dbpedia.org/ontology/description) | capital city of Edo State, Nigeria @en |  |
| out | [thumbnail](http://dbpedia.org/ontology/thumbnail) | [http://commons.wikimedia.org/wiki/Special:FilePath/Areal_view_of_the_ancient_city_of_Benin.jpg?width=300](http://commons.wikimedia.org/wiki/Special:FilePath/Areal_view_of_the_ancient_city_of_Benin.jpg?width=300) |  |
| … |
```

On Virtuoso endpoints, annotation literals (labels, comments, names) are folded to one value per property, and
"values folded" counts the rest. The link opens the app on the **Description** tab.

## 8. Read a pasted link back

> **User:** What is this view? https://…/sparql-faceted-browser-claude_opus_5_5.html#s=eyJlcCI6…

```bash
python3 scripts/fct_state.py decode "<the pasted link>"
```
```
App:       http://127.0.0.1:8765/app.html  (not the default instance)
Endpoint:  https://dbpedia.org/sparql
Set 1  ← focus: a dbo:Film; dbo:director = dbr:Christopher_Nolan; dbo:starring = dbr:Michael_Caine
View:      entities
```

> **Answer:** It's Christopher Nolan's films that star Michael Caine, from DBpedia. There are 7 of them (Inception,
> The Dark Knight Rises, …).

`fct_query.py --link "<the pasted link>"` supplies the rows. Follow-ups use `fct_state.py edit "<the pasted link>" …`.

## 9. Language

> **User:** Same, but in German.

```bash
python3 scripts/fct_query.py --describe dbr:Benin_City --lang de --limit 8 --format table
```
```
out  Beschreibung  Großstadt in Nigeria @de
out  dbo:thumbnail  http://commons.wikimedia.org/wiki/Special:FilePath/Areal_view_of_the_ancient_city_of_Benin.jpg?width=300
out  dbo:wikiPageExternalLink  http://www.edoworld.net/Tourism.html
…
```

`--lang de` changes both the labels in chat and the link: the link gains `&cfg=…`, so the app opens in German
for that view only, whatever the viewer's own settings are. The app's About panel then shows "Literal language:
de (from this link)".

## 10. Another app instance

> **User:** Use my faceted browser at `<your-app-url>` (whatever URL the user gives)

**Skill decides:** the user named an instance, so it checks that instance once and then uses it for the rest of
the session.

```bash
APP_URL='<your-app-url>'   # the exact URL the user gave
python3 scripts/fct_state.py check-app "$APP_URL"
```

- **A valid instance** prints: `… is a SPARQL Faceted Browser instance with #s= state and &cfg= language support.`
- **Not the app** (for example, someone pastes an endpoint URL) prints: `https://dbpedia.org/sparql is not a SPARQL Faceted Browser instance (missing: title, state (#s=), language (&cfg=)).`

From then on, every call carries `--app`:

```bash
python3 scripts/fct_query.py --app "$APP_URL" --type dbo:Film --pv dbo:director=dbr:Christopher_Nolan
```

Alternatively, set `export FCT_APP_URL=https://…` once for the whole session. Without `--app` or `FCT_APP_URL`,
links go to the default URIBurner instance.
