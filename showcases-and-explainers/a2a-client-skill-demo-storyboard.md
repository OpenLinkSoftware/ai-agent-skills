# Skill Discovery and Use over A2A — Demo Storyboard

Purpose: guide-demo and screencast outline for showing a practical user journey: the principal establishes session identity, the agent confirms operating preferences, then the A2A client skill discovers endpoint skills and supports selection of the skill of interest on the user's chosen endpoint.

## Core Message

Lead with the simple story:

> I, the principal, establish who I am and how the agent should behave. Then I invoke the A2A skill so the agent can discover the skills offered by my chosen endpoint and select the skill I want to use.

The transport stays in the background. The story is session context first, endpoint capability discovery second, skill selection third.

## Opening Promise

Open with trust and context before the demo mechanics:

1. Ask `whoami?`
2. Ask `what are my preferences?`

These are not decoration. They establish the principal-agent relationship and the behavioral context that guides the rest of the session before the A2A skill workflow begins.

## Cast

| Role | On-Screen Evidence |
|---|---|
| Principal user | `whoami?` response identifying Kingsley Idehen |
| Agent behavior contract | `what are my preferences?` response |
| Demo skill | `a2a-client` |
| Target endpoint | URIBurner, `https://linkeddata.uriburner.com` |
| Selected endpoint skill | OpenLink Data Twingler v2.0.4 |
| Chosen endpoint | URIBurner, `https://linkeddata.uriburner.com` |
| Selected skill of interest | OpenLink Data Twingler v2.0.4 |

## Scene List

| # | Scene | Visual Capture | Narration Beat | Proof Point |
|---:|---|---|---|---|
| 1 | Identity check | Chat/terminal: `whoami?` | "First, the agent establishes who it is operating for." | User and agent identity are explicit. |
| 2 | Preference check | Chat/terminal: `what are my preferences?` | "Then it checks the operating contract: local memory, Linked Data-first answers, compact presentation, and hyperlinking rules." | Output expectations are established before work starts. |
| 3 | Invoke A2A skill | Title card or command prompt | "With session context established, the user invokes the A2A client skill." | The A2A skill is the demo mechanism. |
| 4 | Recommended endpoints | Table of NetID QA, URIBurner, Demo | "The agent treats endpoints as choices, not hardcoded defaults." | NetID QA correction to `:8443` is visible. |
| 5 | Agent Card discovery | Terminal plus endpoint summary table | "Each endpoint publishes what it can do." | Card metadata is captured as a table. |
| 6 | Skills by endpoint | Full skills-by-endpoint table | "The crux: discovery exposes the available skills." | Data Twingler appears on URIBurner. |
| 7 | Select Data Twingler | Highlight `OpenLink Data Twingler v2.0.4` | "The user selects the skill of interest on the chosen endpoint." | Skill target is clear. |
| 8 | Optional continuation | OAuth / task execution evidence | "Authorization and task execution come after selection; they are supporting mechanics, not the headline." | Separates core story from QA details. |
| 9 | Close | Summary table | "The reusable pattern is identity, preferences, A2A discovery, and skill selection." | Clear guide-demo takeaway. |

## Screen Captures To Preserve

| Capture | Source Interaction | Use In Guide |
|---|---|---|
| Identity response | `whoami?` | Opening trust/context panel |
| Preferences response | `what are my preferences?` | Operating contract panel |
| Endpoint summary table | Card discovery results | Discovery proof |
| Skills-by-endpoint table | Agent Card `skills` arrays | Skill discovery proof |
| OAuth login page | URIBurner/GitHub/localhost callback | Auth flow proof |
| Token capture line | `.opal-a2a.env` written | Secure reuse proof |
| Data Twingler backend error | Authenticated A2A response | QA finding |
| Linked movie-title table | DBpedia result presentation | Final user value |

## Tables To Carry Forward

### Endpoint Discovery Summary

| Endpoint | Agent Card Result | A2A URL | Auth | Streaming | Skills | Notes |
|---|---:|---|---|---:|---:|---|
| `https://netid-qa.openlinksw.com` | 404 | N/A | N/A | N/A | N/A | No card at `/.well-known/agent.json` |
| `https://netid-qa.openlinksw.com:8443` | OK | `https://netid-qa.openlinksw.com:8443/chat/api/a2a` | OAuth2 | true | 9 | Working NetID QA A2A base |
| `https://linkeddata.uriburner.com` | OK | `https://linkeddata.uriburner.com/chat/api/a2a` | OAuth2 | true | 13 | URIBurner A2A endpoint |
| `https://demo.openlinksw.com` | OK | `https://demo.openlinksw.com/chat/api/a2a` | OAuth2 | true | 37 | Demo A2A endpoint |

### Selected Skill Evidence

| Endpoint | Skill ID | Skill Name |
|---|---|---|
| URIBurner | `system-data-twingler-config` | OpenLink Data Twingler v2.0.4 |

The full skills-by-endpoint table should be included in the guide as an expandable or scrollable table, with the Data Twingler row visually highlighted.

### Query Result Table

Use this compact form. The title is the hyperlink; there is no separate DBpedia IRI column.

| Movie |
|---|
| [25th Hour](http://dbpedia.org/resource/25th_Hour) |
| [4 Little Girls](http://dbpedia.org/resource/4_Little_Girls) |
| [A Huey P. Newton Story](http://dbpedia.org/resource/A_Huey_P._Newton_Story) |
| [American Utopia (film)](http://dbpedia.org/resource/American_Utopia_(film)) |
| [Bad 25 (film)](http://dbpedia.org/resource/Bad_25_(film)) |
| [Bamboozled](http://dbpedia.org/resource/Bamboozled) |
| [BlacKkKlansman](http://dbpedia.org/resource/BlacKkKlansman) |
| [Chi-Raq](http://dbpedia.org/resource/Chi-Raq) |
| [Clockers (film)](http://dbpedia.org/resource/Clockers_(film)) |
| [Crooklyn](http://dbpedia.org/resource/Crooklyn) |
| [Da 5 Bloods](http://dbpedia.org/resource/Da_5_Bloods) |
| [Da Sweet Blood of Jesus](http://dbpedia.org/resource/Da_Sweet_Blood_of_Jesus) |
| [Do the Right Thing](http://dbpedia.org/resource/Do_the_Right_Thing) |
| [Get on the Bus](http://dbpedia.org/resource/Get_on_the_Bus) |
| [Girl 6](http://dbpedia.org/resource/Girl_6) |
| [He Got Game](http://dbpedia.org/resource/He_Got_Game) |
| [Inside Man](http://dbpedia.org/resource/Inside_Man) |
| [Jungle Fever](http://dbpedia.org/resource/Jungle_Fever) |
| [Malcolm X (1992 film)](http://dbpedia.org/resource/Malcolm_X_(1992_film)) |
| [Miracle at St. Anna](http://dbpedia.org/resource/Miracle_at_St._Anna) |
| [Mo' Better Blues](http://dbpedia.org/resource/Mo'_Better_Blues) |
| [Oldboy (2013 film)](http://dbpedia.org/resource/Oldboy_(2013_film)) |
| [Red Hook Summer](http://dbpedia.org/resource/Red_Hook_Summer) |
| [School Daze](http://dbpedia.org/resource/School_Daze) |
| [She's Gotta Have It](http://dbpedia.org/resource/She's_Gotta_Have_It) |
| [Summer of Sam](http://dbpedia.org/resource/Summer_of_Sam) |
| [The Original Kings of Comedy](http://dbpedia.org/resource/The_Original_Kings_of_Comedy) |
| [When the Levees Broke](http://dbpedia.org/resource/When_the_Levees_Broke) |

## Script Beats

### Beat 1 — Establish Identity and Preferences

Prompts:

```text
whoami?
what are my preferences?
```

Narration:

> Before the agent touches a remote endpoint, it establishes who it is acting for and how the work should be shaped. That matters because the user expects Linked Data-first answers, explicit provenance, endpoint-aware behavior, and compact presentation of resolvable IRIs.

Capture guidance:

- Show the responses as screen captures, not retyped summaries.
- Blur or avoid any sensitive local paths if they appear.
- Keep the emphasis on identity, delegation, and output preferences.

### Beat 2 — Discover What The Endpoints Offer

Commands:

```bash
python3 a2a-client/scripts/a2a_client.py card \
  --agent-base https://netid-qa.openlinksw.com:8443

python3 a2a-client/scripts/a2a_client.py card \
  --agent-base https://linkeddata.uriburner.com

python3 a2a-client/scripts/a2a_client.py card \
  --agent-base https://demo.openlinksw.com
```

Guide output: show the endpoint summary table, then the skills-by-endpoint table.

Narration:

> The discovery step is the product moment. The endpoint tells us which skills exist. The user does not need to know a private endpoint contract in advance.

### Beat 3 — Select and Invoke a Skill

Prompt:

```text
OpenLink Data Twingler v2.0.4: Using DBpedia, list movies by Spike Lee.
```

Narration:

> The selected skill is Data Twingler on URIBurner. The question is intentionally plain English. The job of the workflow is to bridge from that intent to an endpoint-hosted skill and, ultimately, a linked-data answer.

### Beat 4 — Authenticate Without Exposing Secrets

Command:

```bash
python3 a2a-client/scripts/a2a_client.py send \
  --agent-base https://linkeddata.uriburner.com \
  --oauth-auth-code \
  --oauth-timeout 900 \
  --save-token-env OPAL_A2A_TOKEN \
  --save-token-env-file .opal-a2a.env \
  --message "OpenLink Data Twingler v2.0.4: Using DBpedia, list movies by Spike Lee." \
  --text-only
```

Capture guidance:

- Show the login page and callback.
- Show only that `.opal-a2a.env` was written.
- Do not show the token value.

Narration:

> Authentication is part of the workflow, but credentials are not part of the story. The user completes login in the browser. The client captures a reusable bearer token without exposing it.

### Beat 5 — Separate Client Success From Backend Failure

Observed outcomes:

1. OAuth succeeded.
2. Token capture succeeded.
3. Authenticated retry reached the endpoint.
4. Data Twingler returned a backend missing-parameter error.

Narration:

> This is useful QA. The client workflow worked. The selected backend skill needs a fix. The guide should make that distinction clear.

### Beat 6 — Preserve the User Outcome

Fallback SPARQL:

```sparql
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?movie ?title WHERE {
  ?movie dbo:director dbr:Spike_Lee ;
         rdfs:label ?title .
  FILTER (lang(?title) = "en")
}
ORDER BY ?title
```

Narration:

> When the selected backend route fails, the agent preserves the user intent and uses DBpedia directly. The final answer follows the user's presentation preference: the movie title is the link.

## Voiceover Draft

> This demo starts with context. The agent first establishes who it is working for and checks the user's preferences. That is the operating contract: use Linked Data where it matters, preserve provenance, and present results in a form people can read.
>
> The main product moment is skill discovery. Three endpoints are checked. Each Agent Card tells us the available skills, the authentication scheme, streaming support, and the task endpoint. From that discovery table, we select OpenLink Data Twingler on URIBurner.
>
> The user asks a simple question: using DBpedia, list movies by Spike Lee. The endpoint requires OAuth, so the browser handles login and the client captures a reusable bearer token without exposing it. The authenticated request reaches the endpoint, but the Data Twingler backend returns a missing-parameter error. That is not hidden; it is a useful QA finding.
>
> The guide still delivers the user outcome. It runs the equivalent DBpedia SPARQL query and presents movie titles as hyperlinks. No noisy duplicate IRI column. The result is a clearer demo: discover skills, select one, authenticate, interact, report what happened, and present linked-data answers cleanly.

## Screencast Capture Plan

| Segment | Capture Surface | Duration | Notes |
|---|---|---:|---|
| Identity and preferences | Chat/terminal screenshots | 20s | Must include `whoami?` and `what are my preferences?`. |
| Value proposition | Static guide page | 10s | Do not over-explain A2A; say "discover skills, select, interact." |
| Endpoint discovery | Static guide table plus terminal snippets | 25s | Show endpoint summary table. |
| Skills discovery | Scrollable skills table | 30s | Highlight Data Twingler on UB. |
| Auth flow | Browser + terminal | 45s | Show login/callback/token-file, never token value. |
| Skill interaction | Terminal | 20s | Show authenticated reach plus backend error. |
| Query result | Static guide table | 25s | Use linked movie-title table. |
| Close | Static guide page | 10s | Summarize client success vs backend QA issue. |

## Open QA Items

| Item | Owner | Notes |
|---|---|---|
| Data Twingler A2A missing-parameter error | OPAL/Data Twingler backend | Reproduced after OAuth success on URIBurner. |
| First authenticated call returned VAL 401/deadlock | OPAL auth/backend | Retry with saved token reached OPAL skill. |
| NetID QA no-port Agent Card returns 404 | Endpoint config/docs | Recommended endpoint corrected to include `:8443`. |
| Capture real `whoami?` and preferences screenshots | Guide author | Required opening proof. |
| Build static guide page | Guide author | Needed for clean screencast capture. |

## Assets To Produce Next

1. `a2a-client-skill-demo-guide.html` — static guide page for clean recording.
2. Screen captures for `whoami?` and `what are my preferences?`.
3. Full skills-by-endpoint table rendered as an expandable section.
4. `a2a-client-skill-demo-storyboard.yml` — `shot-scraper` scene file.
5. Optional captions: `a2a-client-skill-demo.srt` / `.vtt`.
6. Optional voiceover MP3 after script approval.
