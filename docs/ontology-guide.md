> Snapshot of the live Claude Doc (https://claude.ai/artifact/QZzDB9Lp8k94cXoU7smD7S), kept for safe keeping. Network addresses are redacted. The Claude Doc is the current copy.

# How to Use the Lakehouse Ontology (Jena Fuseki)

Updated Nov 2, 2026 · @wrolfgar

## What it is

The ontology is a knowledge graph in Apache Jena Fuseki: a few named graphs that say what every lake column means, how the business terms relate, which columns are sensitive, which business rules hold, and which business inputs each data product waits on. You ask it questions in SPARQL. It holds no records, only meaning: 27 glossary terms, 580 columns across 73 lake tables, 23 columns tagged Restricted, 21 tagged Personal and 17 deduced Pseudonymous, 5 data products, 12 business rules and 5 business inputs (as of 2026-11-02, with the expanded world's tables and products and the tagger's two ops tables in).

Nobody edits it directly. It is a published copy of what OpenMetadata knows:

1. The glossary (`lakehouse/glossary/glossary.yml`) and dbt's `meta.sensitivity` tags go into OpenMetadata through `om_sync.py`. Stewards can add more tags there in the UI.
2. `om_to_rdf.py` reads OpenMetadata and replaces the whole graph in Fuseki, so it never drifts or piles up stale facts.
3. The 05:00 `daily_lake` run does both steps after gold is built (assets `openmetadata/lake` and `fuseki/glossary`), and `bootstrap.sh` does them on every run.

&#91;embedded content: how meaning reaches the graph · 2 sources, 2 scripts, daily\]

Everything you query in Fuseki started in the repo or in OpenMetadata; change it there, and the next load carries it over.

The graph is written in two standard vocabularies: **SKOS** (the W3C standard for glossaries and taxonomies) for the terms, and a small lakehouse vocabulary (`lh:`) for columns, tables, sensitivity and the relations SKOS doesn't have, such as *part of* and *identifies*.

## What it helps you do better

It answers questions that cross meaning, relationships and sensitivity in one query; elsewhere each needs several screens or tools stitched by hand. Each of these is a recipe below, with today's real answer.

| Question | Without the ontology | With it |
| --- | --- | --- |
| Which restricted columns hold part of an offender record? | Read the glossary, then each term's tags in OpenMetadata, then match column names yourself | One query: `stg_group`, `stg_status` |
| Where does sensitive data live, layer by layer? | Open every table in OpenMetadata and scan its tags | One query: bronze, silver, gold and ref, 20 Restricted columns |
| If the meaning of Offender Number changes, what is affected? | Search the code and dbt for the column name | One query: 7 columns in 7 tables, raw to the custody mart |
| What does "PC" mean? | Know that it's a synonym, then search | One query matches synonyms too: Protective Custody, with its definition |
| Where is our glossary thin? | No easy way | One query: 17 of the fact table's columns have no term, including all four race and religion columns, the most sensitive ones |

What it is not for:

- **Numbers.** Counts, totals and pass rates come from Cube (Superset, SQL, the MCP server's `query_metric`), which also enforces the masks.
- **Editing meaning.** That happens in OpenMetadata or `glossary.yml`; the graph follows.
- **One term's definition in a chat.** The MCP server's `define_term` is quicker; the ontology is for questions that join several facts.
- **The automatic tags.** Since 2026-11-02 the daily run tags every table and column: Governance (CJIS, PII), PIIType, Source, Layer and Refresh. Those tags live in OpenMetadata, not the graph; `om_to_rdf.py` carries only the hand-set Sensitivity tags and the glossary terms. To find data by any tag, use OpenMetadata's search or the MCP server's `find_by_tags`, which reads both kinds.

## Getting started

The graph answers SPARQL at `<tailnet-host>` from any device on your tailnet, with no login for reading. Pick whichever of these three suits the moment.

**In the browser.** Open <tailnet-host> choose the `lakehouse` dataset, then the **Query** tab. Paste a recipe from below, keeping its `PREFIX` lines, and run it. The Stats page and the create, delete and backup buttons answer with an error on purpose: those admin actions only work from inside the Fuseki container.

**From your Mac, with curl.** `Accept: text/csv` gives you a plain table:

```bash
curl -s <tailnet-host> -H 'Accept: text/csv' --data-urlencode 'query=
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?term ?definition WHERE { ?t a skos:Concept ; skos:prefLabel ?term ; skos:definition ?definition } ORDER BY ?term'
```

**From a Jupyter notebook on the lakehouse.** Inside the stack, Fuseki is at `http://fuseki:3030`. This helper returns a pandas DataFrame and adds the three prefixes for you:

```python
import pandas as pd, requests

def sparql(query):
    """Run a SPARQL query on the lakehouse ontology; returns a DataFrame."""
    prefixes = """PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX lh:   <https://lakehouse.invalid/ontology#>
PREFIX term: <https://lakehouse.invalid/glossary/>
"""
    r = requests.post("http://fuseki:3030/fuseki/lakehouse/sparql", data={"query": prefixes + query},
                      headers={"Accept": "application/sparql-results+json"}, timeout=30)
    r.raise_for_status()
    rows = r.json()["results"]["bindings"]
    return pd.DataFrame([{k: v["value"] for k, v in row.items()} for row in rows])

sparql('SELECT ?label WHERE { ?t a skos:Concept ; skos:prefLabel ?label } ORDER BY ?label')
```

With the helper defined, every recipe below runs as `sparql('''...''')` without its `PREFIX` lines.

## The vocabulary

A query names things through three prefixes, which every recipe starts with:

```sparql
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX lh:   <https://lakehouse.invalid/ontology#>
PREFIX term: <https://lakehouse.invalid/glossary/>
```

| Name | What it is | Example |
| --- | --- | --- |
| `term:<slug>` | A glossary term; the slug is its name in lower case with hyphens | `term:offender-number`, `term:stg-affiliation` |
| `skos:Concept` | The type every glossary term has | `term:unit a skos:Concept` |
| `skos:prefLabel` | The term's name | "Offender Number" |
| `skos:definition` | Its definition, as written in the glossary | "The record's ID: 8 digits with leading zeros as people write it (02381457)..." |
| `skos:altLabel` | A synonym, one per value | "PC" for Protective Custody |
| `skos:broader`, `skos:narrower` | The more general or more specific term | Offense Code is narrower than Offense-Against Category |
| `skos:related` | A loose "see also" | Violence Code is related to Offense Code |
| `lh:partOf`, `lh:hasPart` | One concept is a part of another | Escape Risk is part of Offender Record (11 parts) |
| `lh:identifies`, `lh:identifiedBy` | One concept picks out instances of another | Offender Number identifies Offender Record |
| `lh:Column` | The type every lake column has | 213 of them, in 27 tables |
| `lh:table` | The column's table, as `schema.table` | "gold.fct\_offender\_record" |
| `lh:name` | The column's name | "stg\_group" |
| `lh:sensitivity` | `lh:Restricted` or `lh:Personal` (tagged in OpenMetadata), or Pseudonymous (deduced by a rule, recipe 10) | `stg_group` is `lh:Restricted` |
| `lh:means` | The glossary term the column carries | `offender_number` means `term:offender-number` |

&#91;embedded content: one column in the graph · 3 links\]

A query is a pattern of these links: recipe 8 asks for columns that are Restricted, mean a term, and whose term is part of Offender Record.

Every relation is stored in both directions (*part of* and *has part*, *broader* and *narrower*), so you can walk from either end. The facts sit in named graphs, each from one source: `<https://lakehouse.invalid/graph/openmetadata>` (terms, columns, tags, products), `.../graph/rulebook` (business rules), `.../graph/readiness` (business inputs and who depends on them), and one `.../graph/inferred/<rule>` per deduction rule. Fuseki serves them all together as the default graph, so most queries never need a `GRAPH` clause. Use one when you want to know where a fact came from (recipe 10).

**Data products and people.** Each data product (`lakehouse/products/`) is in the graph as a `dcat:Dataset`, from DCAT, the W3C vocabulary for data catalogs, under `prod:<name>` (`PREFIX prod: <https://lakehouse.invalid/product/>`, plus `dcat:` and `dct:` for DCAT and Dublin Core):

| Name | What it is | Example |
| --- | --- | --- |
| `dct:title`, `lh:question` | The product's name and the question it answers | "Custody Population" |
| `lh:domain` | Its domain | "Custody Operations" |
| `lh:usesTable` | A table it delivers, as `schema.table` | "mart\_custody.custody\_snapshot\_monthly" |
| `lh:usesTerm` | A glossary term it speaks in | `term:person` |
| `dcat:accessService` | A Cube view that serves it (a `dcat:DataService` with a `dct:title`) | `custody_population` |
| `lh:isAbout`, `lh:subjectOf` | A record describes one person | Offender Record is about Person; SID Number identifies Person |

## Recipes

Each recipe was run against the live graph on 2026-10-26, and its answer is shown under it. Add the three `PREFIX` lines in the browser or curl; the notebook helper adds them for you. Recipes 9 and 12 were run again on 2026-11-02, after the expanded world gained its data products. The others still show their first answers, from before the world's tables and terms arrived, so today's counts are larger; the queries themselves are unchanged.

### 1. Look up a word, synonyms included

What does "PC" mean?

```sparql
SELECT ?label ?definition WHERE {
  ?t skos:prefLabel ?label ; skos:definition ?definition .
  { ?t skos:altLabel ?a } UNION { ?t skos:prefLabel ?a }
  FILTER(LCASE(STR(?a)) = "pc")
}
```

Answer: **Protective Custody**, "Yes or no: the person is housed apart for their own safety..."

### 2. The parts of an offender record, with their columns

```sparql
SELECT ?part (GROUP_CONCAT(DISTINCT ?col; separator=", ") AS ?cols) WHERE {
  ?t lh:partOf term:offender-record ; skos:prefLabel ?part .
  OPTIONAL { ?c lh:means ?t ; lh:table "gold.fct_offender_record" ; lh:name ?col }
} GROUP BY ?part ORDER BY ?part
```

Answer: 11 parts, from Custody Level (`custody_level`) to STG Affiliation (`stg_group, stg_status`). Conduct Note comes back with no column, because the glossary links it to none.

### 3. Where restricted data lives, layer by layer

```sparql
SELECT ?table (GROUP_CONCAT(?name; separator=", ") AS ?cols) WHERE {
  ?c lh:sensitivity lh:Restricted ; lh:table ?table ; lh:name ?name
} GROUP BY ?table ORDER BY ?table
```

| Table | Restricted columns |
| --- | --- |
| bronze.hero\_offenders\_raw | race, religion, stg\_affiliation |
| silver.hero\_offenders | race, race\_code, race\_omb, religion, religion\_family, religion\_group, stg\_affiliation, stg\_group, stg\_status |
| gold.fct\_offender\_record | race\_code, race\_omb, religion\_family, religion\_group, stg\_group, stg\_status |
| gold.dim\_stg\_group | stg\_group |
| ref.stg\_groups | stg\_group |

Swap `lh:Restricted` for `lh:Personal` for the personal-data inventory: names, aliases, birth dates and conduct notes, in bronze (5 columns) and silver (8), never in gold.

### 4. Every place one concept lives

```sparql
SELECT ?table ?name ?sensitivity WHERE {
  ?c lh:means term:stg-affiliation ; lh:table ?table ; lh:name ?name .
  OPTIONAL { ?c lh:sensitivity ?sensitivity }
} ORDER BY ?table ?name
```

Answer: 6 columns in 4 tables (ref, silver, two gold), every one Restricted.

### 5. Walk the relations around a term

```sparql
SELECT ?relation ?other WHERE {
  term:offense-code ?relation ?o .
  ?o a skos:Concept ; skos:prefLabel ?other
} ORDER BY ?relation
```

Answer: Offense Code is `broader` → Offense-Against Category, `related` → Violence Code, `partOf` → Offender Record.

### 6. What a change to a term would touch

```sparql
SELECT ?table ?name WHERE {
  ?c lh:means term:offender-number ; lh:table ?table ; lh:name ?name
} ORDER BY ?table
```

Answer: 7 columns in 7 tables (as of 2026-10-27), from `bronze.hero_offenders_raw` through gold to `mart_custody.custody_snapshot_monthly`, including both copies of the conduct-notes answer key.

### 7. Where the glossary is thin

```sparql
SELECT ?name WHERE {
  ?c lh:table "gold.fct_offender_record" ; lh:name ?name .
  FILTER NOT EXISTS { ?c lh:means ?t }
} ORDER BY ?name
```

Answer: 17 of the fact table's columns have no term, among them `gender`, `sentence_date` and all four race and religion columns. Those four are the most sensitive in gold and have no written meaning, which makes them the first candidates for new glossary terms.

### 8. One question no single tool answers

Which restricted columns hold part of an offender record?

```sparql
SELECT ?column WHERE {
  ?c lh:table "gold.fct_offender_record" ; lh:name ?column ;
     lh:sensitivity lh:Restricted ; lh:means ?t .
  ?t lh:partOf term:offender-record
}
```

Answer: `stg_group` and `stg_status`. It joins a term relation (STG Affiliation is part of Offender Record), the column-to-term link and the sensitivity tag.

### 9. Which products would a change touch?

Add `PREFIX dcat: <http://www.w3.org/ns/dcat#>` and `PREFIX dct: <http://purl.org/dc/terms/>` to the usual three.

```sparql
SELECT ?product (GROUP_CONCAT(DISTINCT ?view; separator=", ") AS ?views) WHERE {
  ?p a dcat:Dataset ; dct:title ?product ; lh:usesTerm term:person ;
     dcat:accessService ?v . ?v dct:title ?view
} GROUP BY ?product ORDER BY ?product
```

Answer: **Custody Offenses** (views `custody_admissions, custody_offenses`) and **Custody Population** (`custody_population`). The expanded world's three products speak in Person Key, not Person, so they don't appear. Swap `term:person` for any term, or match `lh:usesTable` against a table, to see who a change would reach before you make it. A property path reaches products one link further: `lh:usesTerm/lh:isAbout? term:incident` (the term itself, or a term that is about it) finds **Court Outcomes**, **Field Incidents** and **Incident Damage**. Court Outcomes is there only through the path: it speaks in Charge, and a Charge is about an Incident.

Recipes 10 to 16 go further: where a fact came from, chains of links, readiness, yes/no checks, taking the graph into Python, and using it with Cube. Each was run against the live graph on 2026-10-31.

### 10. Stated or deduced: where did a fact come from?

A rule can add facts nobody typed in. Asking for the graph a fact sits in (`GRAPH ?g`) tells you whether OpenMetadata stated it or a rule deduced it, and which rule.

```sparql
SELECT ?table ?sensitivity ?source WHERE {
  ?c lh:name "sid_number" ; lh:table ?table .
  OPTIONAL {
    GRAPH ?g { ?c lh:sensitivity ?s }
    BIND(STRAFTER(STR(?s), "#") AS ?sensitivity)
    BIND(IF(STRSTARTS(STR(?g), "https://lakehouse.invalid/graph/inferred/"),
            CONCAT("deduced: ", STRAFTER(STR(?g), "inferred/")), "stated: OpenMetadata") AS ?source)
  }
} ORDER BY ?table
```

Answer: all 6 `sid_number` columns, from `bronze.hero_offenders_raw` to `mart_custody.custody_snapshot_monthly`, are Pseudonymous, and every one says `deduced: identifier-of-a-person-is-pseudonymous`. Nobody tagged them; the rule found them. Swap the first line for `?c a lh:Column ; lh:table ?table .` to see every column's sensitivity with its source.

### 11. Follow a chain of links

One link at a time, a query only sees neighbours. A *property path* follows links any number of steps: `+` means one or more, `*` zero or more, `|` either link, and `/` one link then the next. Which terms lead to Person, by any chain of part-of, identifies, is-about and narrower links?

```sparql
SELECT ?term (COUNT(DISTINCT ?c) AS ?columns) WHERE {
  ?t skos:prefLabel ?term ;
     (lh:partOf|lh:identifies|lh:isAbout|skos:narrower)+ term:person .
  OPTIONAL { ?c lh:means ?t }
} GROUP BY ?term ORDER BY DESC(?columns) ?term
```

Answer: all 14 other terms do, from Unit (8 columns) to Conduct Note (0). Offense-Against Category takes three steps: it is broader than Offense Code, which is part of Offender Record, which is about Person. No one-step query would find it.

The same idea counts the columns that say something about a person:

```sparql
SELECT (COUNT(DISTINCT ?direct) AS ?one_step) (COUNT(DISTINCT ?any) AS ?any_number_of_steps) WHERE {
  { ?direct lh:means/(lh:identifies|lh:isAbout) term:person } UNION
  { ?any lh:means/(lh:partOf|lh:identifies|lh:isAbout|skos:narrower)* term:person }
}
```

Answer: 13 columns one step from Person, 57 by any chain. That 57 is the real footprint of personal information by meaning, which is far wider than the 13 columns tagged Personal.

### 12. Readiness: who does each product wait on?

The readiness graph holds each business input (`lh:BusinessInput`: `dct:title`, `lh:unit`, `lh:system`, `lh:closesWithinDays`) and each product's `lh:dependsOn`. Add the `dcat:` and `dct:` prefixes from recipe 9.

```sparql
SELECT ?product ?input ?unit ?system ?days WHERE {
  ?p a dcat:Dataset ; dct:title ?product ; lh:dependsOn ?i .
  ?i dct:title ?input ; lh:unit ?unit ; lh:system ?system ; lh:closesWithinDays ?days .
} ORDER BY ?product ?input
```

Answer:

| Product | Input | Unit | System | Closes within (days) |
| --- | --- | --- | --- | --- |
| Court Outcomes | Sentencing orders and charge decisions | Courts liaison | Court case feed | 7 |
| Custody Offenses | Admissions, releases and transfers | Records | Offender management | 5 |
| Custody Offenses | Sentencing orders and charge decisions | Courts liaison | Court case feed | 7 |
| Custody Population | Admissions, releases and transfers | Records | Offender management | 5 |
| Custody Population | Custody-level and threat reviews | Classification | Case management | 10 |
| Field Incidents | Incident reports | Field Operations | Incident reporting | 3 |
| Incident Damage | Damage claims | Insurance | Claims system | 20 |
| Incident Damage | Incident reports | Field Operations | Incident reporting | 3 |

To ask the other way round, which products wait on one unit, a path does it in one line: `?p a dcat:Dataset ; dct:title ?product ; lh:dependsOn/lh:unit "Classification"`. Answer: Custody Population only. That is who to warn when Classification runs late. With `"Courts liaison"` the answer is Court Outcomes and Custody Offenses: one unit's close finalizes products in two domains.

### 13. Yes-or-no checks and summaries

`ASK` answers true or false, which suits a quick check or an `assert` in a notebook. Is any Restricted column without a glossary term?

```sparql
ASK { ?c lh:sensitivity lh:Restricted . FILTER NOT EXISTS { ?c lh:means ?t } }
```

Answer: true, the race and religion columns from recipe 7. And `ASK { ?c lh:sensitivity lh:Personal ; lh:table ?t . FILTER STRSTARTS(?t, "gold.") }` answers false: no personal data has reached gold.

`GROUP BY` with `SUM` or `COUNT` gives a summary in one table, here sensitivity by layer:

```sparql
SELECT ?layer (SUM(IF(?s = lh:Restricted, 1, 0)) AS ?restricted)
       (SUM(IF(?s = lh:Personal, 1, 0)) AS ?personal)
       (SUM(IF(?s = lh:Pseudonymous, 1, 0)) AS ?pseudonymous) WHERE {
  ?c lh:table ?table ; lh:sensitivity ?s .
  BIND(STRBEFORE(?table, ".") AS ?layer)
} GROUP BY ?layer ORDER BY ?layer
```

Answer:

| Layer | Restricted | Personal | Pseudonymous |
| --- | --- | --- | --- |
| bronze | 3 | 5 | 1 |
| gold | 7 | 0 | 2 |
| mart\_custody | 0 | 0 | 1 |
| ref | 1 | 0 | 0 |
| silver | 9 | 8 | 2 |

### 14. Everything about one thing

`DESCRIBE` returns every fact about a subject, without writing a pattern. Ask for Turtle (`Accept: text/turtle` with curl; the notebook helper expects tables, so use `requests` directly).

```sparql
DESCRIBE term:person
```

Answer: Person's name, definition and scheme, its synonyms (person, offender, inmate, individual), `lh:identifiedBy term:sid-number` and `lh:subjectOf term:offender-record`. It's a quick way to learn a term's shape before writing a query about it.

### 15. Take the graph into Python

The `get` endpoint downloads a graph as a file, with no login. From your Mac:

```bash
curl -s '<tailnet-host> \
  -H 'Accept: text/turtle' -o openmetadata.ttl
curl -s <tailnet-host> -H 'Accept: application/trig' -o lakehouse.trig
```

The first is one graph as Turtle; the second is every graph at once as TriG, each fact still labelled with its graph. In a Jupyter notebook on the lakehouse, `rdflib` loads it and `networkx` draws the glossary:

```python
import requests, rdflib, networkx as nx, matplotlib.pyplot as plt

ttl = requests.get("http://fuseki:3030/fuseki/lakehouse/get",
                   params={"graph": "https://lakehouse.invalid/graph/openmetadata"},
                   headers={"Accept": "text/turtle"}, timeout=60).text
g = rdflib.Graph().parse(data=ttl, format="turtle")

SKOS = rdflib.Namespace("http://www.w3.org/2004/02/skos/core#")
LH = rdflib.Namespace("https://lakehouse.invalid/ontology#")
label = {s: str(o) for s, o in g.subject_objects(SKOS.prefLabel)}
G = nx.DiGraph()
for p in (LH.partOf, LH.identifies, LH.isAbout, SKOS.broader, SKOS.related):
    for s, o in g.subject_objects(p):
        if s in label and o in label:
            G.add_edge(label[s], label[o], rel=p.split("#")[-1])

plt.figure(figsize=(12, 8))
pos = nx.spring_layout(G, seed=1)
nx.draw_networkx(G, pos, node_color="#dbe7f5", node_size=1800, font_size=8)
nx.draw_networkx_edge_labels(G, pos, edge_labels=nx.get_edge_attributes(G, "rel"), font_size=7)
plt.axis("off")
```

Answer: 892 facts in the graph; the picture has 15 terms and 17 links, with Offender Record at the centre and its 11 parts around it. Once the graph is in `rdflib` you can query it offline with `g.query("SELECT ...")`, or hand it to `networkx` for things SPARQL can't do, such as shortest paths.

### 16. The graph and the numbers together

The graph knows which columns are restricted; Cube holds the numbers and the masks. Together they can prove the masks are doing their job. In a Jupyter notebook on the lakehouse (the MCP token is already in its environment):

```python
import os, requests

def mcp(tool, **arguments):
    """Call one of the MCP server's tools; returns its structured result."""
    r = requests.post("http://mcp:8000/mcp", timeout=60,
                      headers={"Accept": "application/json, text/event-stream",
                               "Authorization": "Bearer " + os.environ["MCP_TOKEN"]},
                      json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                            "params": {"name": tool, "arguments": arguments}})
    return r.json()["result"]["structuredContent"]

restricted = sparql('''SELECT ?name WHERE {
  ?c lh:table "gold.fct_offender_record" ; lh:name ?name ; lh:sensitivity lh:Restricted }''')["name"]
dims = next(m["dimensions"] for m in mcp("list_metrics")["metrics"]
            if m["view"] == "offender_records" and m["name"] == "record_count")
for col in sorted(restricted):
    if col in dims:
        rows = mcp("query_metric", metric="offender_records.record_count", group_by=[col])["rows"]
        print(col, sorted({str(r[col]) for r in rows}))
```

Answer: all six restricted columns of the fact table (`race_code`, `race_omb`, `religion_family`, `religion_group`, `stg_group`, `stg_status`) come back from Cube as `***` only. If one ever showed real values, a tag in OpenMetadata and Cube's masks would have drifted apart. The daily `cube_masks_match_openmetadata` check watches for the same thing; this recipe shows it end to end.

## Changing the ontology

Change the source, never Fuseki: the next load replaces the whole graph, so anything written straight into Fuseki is gone by morning.

| To change | Edit it in | Reaches the graph |
| --- | --- | --- |
| A term's definition, synonyms or relations | `lakehouse/glossary/glossary.yml` (commit it). Not OpenMetadata's glossary screen: the next sync puts the file's words back | The 05:00 `daily_lake` run, or now with the commands below |
| A new glossary term, or a term's columns | `glossary.yml`: the term's `columns` list links it to every lake column with that name | Same |
| A column's sensitivity | dbt's `meta.sensitivity` in the model's `schema.yml`, or a `Sensitivity.Restricted` tag added in OpenMetadata's UI | Same; a new Restricted tag also flags Cube's masks as behind (see below) |
| Column descriptions | dbt's `schema.yml` | Same |

To publish a change now instead of at 05:00, on the VM:

```bash
cd ~/lunch-and-learn-data-cleansing/lakehouse
docker compose --profile core exec -T jupyter python lakehouse/openmetadata/om_sync.py
docker compose --profile core exec -T jupyter python lakehouse/openmetadata/om_to_rdf.py
```

Add `--check` to either to see what differs without writing. `scripts/bootstrap.sh` runs both too.

Tagging a column Restricted also changes what Cube masks: `bootstrap.sh` rewrites the Cube model and restarts Cube; review `git diff lakehouse/cube/model/` and commit it. Until then, the daily run's `cube_masks_match_openmetadata` check warns.

## Business rules

The ontology can hold rules as well as facts: what must be true, and what follows from what is stated. First decide which kind of rule you have, because only some belong here:

| The rule | Example | Where it belongs |
| --- | --- | --- |
| Computes a number | "In custody on a date = sentenced on or before it, release after it"; "people = distinct SIDs" | dbt or Cube. The ontology describes it and points to it. |
| A threshold | "Over 10% of records flagged is a problem" | Prometheus alert rules |
| About meaning or governance | "A column holding a person's identifier is never shown to a consumer"; "every term has a real definition" | The ontology |

Rules are **files in the repo**, never typed into Fuseki: the graphs are rebuilt on every run, so anything added there by hand is gone the next morning. There are three kinds, each with its own graph or check.

### 1. The rulebook: rules written down as data

The `rules:` section at the end of `glossary/glossary.yml`. Each rule has a name, a statement in plain English, the terms it is about, and what enforces it:

```yaml
- name: People are counted by SID
  statement: >
    A person is counted once however many records they hold, by distinct SID at query time; people counts are
    never stored or added up, and records with no SID belong to no known person.
  about: [Person, SID Number]
  enforced_by:
    - cube:custody_population.people_in_custody
    - dbt:dim_person_counts_every_record
    - test:test_custody_cube.py::test_people_by_unit_are_distinct_not_summed
```

`enforced_by` entries are `kind:name`: `cube:` (a measure or dimension), `dbt:` (a test in `dbt/tests`), `prometheus:` (an alert), `shacl:` (a shape), `sparql:` (a deduction rule) or `test:` (an acceptance test). A test checks that every one exists, so the rulebook can't point at nothing. `om_to_rdf.py` publishes each rule as an `lh:BusinessRule` in `<https://lakehouse.invalid/graph/rulebook>`. There are six today.

Which rules involve Person, and where is each enforced (add `PREFIX dct: <http://purl.org/dc/terms/>`):

```sparql
SELECT ?rule ?enforcedBy WHERE {
  ?r a lh:BusinessRule ; dct:title ?rule ; lh:about term:person ; lh:enforcedBy ?enforcedBy }
```

### 2. Deductions: new facts from stated ones

One SPARQL `CONSTRUCT` per file in `ontology/rules/`. `om_to_rdf.py` runs them over the published graphs, and over each other's results, until nothing new appears. It writes each rule's facts to `<https://lakehouse.invalid/graph/inferred/<file name>>`, so a deduced fact is never mistaken for a stated one, and the graph's name says which rule made it. Delete the file and its graph goes too.

Today's rule, `identifier-of-a-person-is-pseudonymous.rq`:

```sparql
CONSTRUCT { ?column lh:sensitivity lh:Pseudonymous }
WHERE { ?column a lh:Column ; lh:means ?identifier . ?identifier lh:identifies term:person . }
```

The glossary says SID Number identifies Person, so every `sid_number` column (six tables today) is deduced to be a **pseudonymous key**. Such a column is fine in tables, for joining and counting people, but is never shown to a consumer, and a test holds Cube to that. Nobody tagged those columns: the rule found them, and a new identifier term with the same relation would be covered without touching the rule.

```sparql
SELECT ?table WHERE {
  GRAPH <https://lakehouse.invalid/graph/inferred/identifier-of-a-person-is-pseudonymous> { ?c lh:sensitivity lh:Pseudonymous }
  ?c lh:table ?table }
```

### 3. Constraints: what must be true (SHACL)

`ontology/shapes.ttl` holds **SHACL** shapes, the W3C language for "this graph must look like this". Fuseki checks them itself, at `/fuseki/lakehouse/shacl`, against every graph at once. Two today:

- **TermShape**: every glossary term has exactly one name and a definition of at least 40 characters (the shortest real one is 92), so a placeholder like "TBD" is caught.
- **RuleShape**: every rule has a statement, names what enforces it, and is only about glossary terms.

Run the check yourself:

```bash
docker compose --profile core exec -T jupyter python lakehouse/ontology/check_rules.py
```

It prints each violation (rule, the thing breaking it, the message), then `Business rules: all 2 shapes hold` or a count, and exits 1 if anything is broken.

The check runs in three places:

- **Every morning:** Dagster's `fuseki/glossary` asset runs the check `business_rules_hold` and pushes `lakehouse_business_rule_violations` per rule to Prometheus. `BusinessRuleViolated` then alerts through ntfy.
- **`bootstrap.sh`:** a broken rule fails the run, in both modes.
- **When you run it by hand,** as above.

### Adding a rule

Test first, as everything here:

1. Write it in `rules:` in `glossary.yml`, with what enforces it.
2. **For a deduction:** add `ontology/rules/<name>.rq` with a comment stating the rule in English.
3. **For a constraint:** add a shape to `shapes.ttl`, and name each of its property shapes `lh:<Shape>-<what>`. A violation names the property shape that failed, and the name lets the check find its rule.
4. Run `scripts/bootstrap.sh`, or wait for 05:00.

`acceptance/test_business_rules.py` shows how to prove a shape really catches a violation: it puts a "TBD" definition in a scratch graph, checks that `TermShape` reports it, then deletes the graph.

## Data readiness: is this number final yet?

The business rules above check the catalog: that definitions are complete and consistent. A different kind of rule is about **time and context**. A number is only correct for a period once **every business process that feeds it has finished**, each in its own system, run by its own business unit, on its own schedule. Query before then and you get a believable wrong answer: rows exist, the pipeline succeeded, the data is fresh, and the number is still wrong. Finance calls the moment everything is in **period close**; data teams call it **readiness** or **completeness**.

### An example

"Cost per person in custody, September" depends on four inputs:

| Input | Owned by | System | Done when |
| --- | --- | --- | --- |
| Who was held each day | Records | Offender management | September admissions, releases and transfers are posted |
| Food and medical invoices | Finance | Accounts payable | September invoices are entered and approved |
| Staff hours | HR | Timekeeping | September timesheets are approved |
| Custody-level reviews | Classification | Case management | September reviews are signed off |

Each finishes on a different day. Asked on October 3rd, the lakehouse would give a confident number built from a complete headcount, half the invoices and no staff hours.

### Three things that sound alike

|  | Means | Who checks it here |
| --- | --- | --- |
| **Fresh** | Loaded recently | Each product's freshness promise, `DataProductStale` |
| **Complete** | Every input for *this period* has arrived and been signed off | Readiness, below |
| **Correct** | The values are valid | dbt tests, the quality scorecard |

A number can be fresh and correct, and still not complete.

### The model

1. **Dependencies are business facts, so they go in the ontology.** Each business value (a metric, a data product) names the inputs it depends on. Each input names the unit that owns it, its system, and how many days after a period ends it should close. Dagster knows the pipeline's steps; it doesn't know that HR hasn't approved timesheets.
2. **Each input reports a watermark: "complete through" a date.** It might be a unit's sign-off, a source system's close flag, or a rule like "no new rows for that month in 5 days". Every report is kept, so a unit can reopen a month and the history shows it.
3. **Readiness is computed per period.** A value for September is **final** only when every input it depends on is complete through September 30. Until then it is **provisional**, with the reason ("waiting on Classification").
4. **Readiness travels with the number**, wherever people query: next to the measure in Cube, in the MCP server's answer, and on the Superset dashboard.
5. **A late input is an alert**, about the business process, not the pipeline: "September should have closed by the 10th; Classification hasn't".
6. **Late changes are visible.** When a late input changes a number already called final, you want to know what you reported before. DuckLake keeps every snapshot, so a published number can record the snapshot it came from.

### How it works here

The custody products are built this way. Three fictional business units feed them:

| Input (`products/inputs/`) | Unit | Closes within | Custody Population | Custody Offenses |
| --- | --- | --- | --- | --- |
| `records`: admissions, releases, transfers | Records | 5 days | needs it | needs it |
| `classification`: custody-level and threat reviews | Classification | 10 days | needs it |  |
| `courts`: sentencing orders and charge decisions | Courts liaison | 7 days |  | needs it |

The units are fictional, so the daily run plays them: each closes a month a few days after it ends (Records on day 3, Courts on day 5, Classification on day 8). Every month therefore starts **provisional** on the 1st and turns **final** by the 8th.

Where readiness shows:

- **Cube:** `period_status` and `waiting_on` sit next to the numbers in `custody_population` and `custody_offenses`. The `period_readiness` view lists every product's months.
- **The MCP server:** `query_metric` on a product's metric returns `readiness` (the latest month-end, plus any month still provisional, with who it waits on).
- **Superset:** *Period status by month-end* sits at the top of the Custody dashboard.
- **Alerts:** `BusinessInputLate` goes to your phone when a unit misses its own deadline.
- **The ontology:** each input is an `lh:BusinessInput`, and each product `lh:dependsOn` its inputs (`graph/readiness`). SHACL shapes check that no product forgets its inputs and every input has an owner and a deadline.

### The recipe: adding a readiness rule

Everything a person adds is a file; there is no Python, SQL or Cube to touch. This is the part to teach.

**1. Name the business input.** Copy `products/inputs/records.yml` to a new file and fill it in. The comments in that file explain each field.

```yaml
name: medical                     # the file's name; depends_on: and closes.py use it
title: Medical and pharmacy costs
unit: Health services             # who owns it: what "waiting on" will say
system: Pharmacy billing          # where the unit records it
description: >
  The month's medical visits and pharmacy invoices, entered and approved by Health services.
closes_within_days: 12            # the unit's promise: complete this many days after a month ends
simulate:                         # only because the unit is fictional: the lakehouse closes for it
  closes_after_days: 9
```

To name an input well, ask: *who* has to finish *what*, in *which* system, before this number means anything? A real unit and a real deadline make a good input; "the pipeline ran" doesn't.

**2. Say who depends on it.** Add its name to the product's `depends_on:` in `products/<product>.yml`:

```yaml
depends_on: [records, classification, medical]
```

**3. Publish.** Run `scripts/bootstrap.sh`, or wait for the 05:00 daily run. `closes.py sync` copies the files into the lake, and `om_to_rdf.py` puts the input and the dependency in the ontology.

**4. Report closes.** In real life the unit's system (or a person in it) does this; here it's one command. `report` needs a month-end; an earlier date reopens a month, and the history keeps both:

```bash
docker compose --profile core exec -T jupyter python lakehouse/readiness/closes.py report medical 2026-09-30 --by "Health services"
```

**5. See it.** `closes.py status` lists each input, what it's complete through, and how late it is. Then query Cube, ask the MCP server, or open the dashboard.

**6. Prove it.** The tests pick up the new input with no edits:

- **`test_readiness.py`:** every product names declared inputs, every input has an owner and a deadline, and readiness matches the closes for every month.
- **SHACL:** the shapes check the ontology.
- **`bootstrap.sh --check`:** fails if the lake is behind the files.

### Exercise (about 30 minutes)

1. **Look.** Run `closes.py status`, then in Superset's SQL Lab:

   ```sql
   SELECT month_end, period_status, waiting_on, MEASURE(people_in_custody)
   FROM custody_population GROUP BY 1, 2, 3 ORDER BY 1 DESC LIMIT 3
   ```
2. **Reopen a month.** Report Classification complete through only August (`report classification 2026-08-31 --by "you" --note "exercise"`). Run the query again: September is **provisional, waiting on Classification**, and the number didn't change. Only its status did. Custody Offenses stays final, because it doesn't need Classification. Ask the MCP server for `people_in_custody` and read its `readiness`.
3. **Close it.** Report Classification through `2026-09-30`. September is final again, at once, with no rebuild.
4. **Add a dependency, and meet the trap.** Add the `medical` input from step 1 of the recipe and list it in Custody Population's `depends_on:`, then run `bootstrap.sh`. **Every month** is now provisional, waiting on Health services, because nobody ever closed medical for any month. A new dependency needs its history closed: report `medical` through the last month-end it really covers.
5. **Put it back.** Delete the file and the `depends_on:` entry, then run `bootstrap.sh`.

### Common mistakes

- **Treating fresh as complete.** The pipeline running says nothing about whether the units are done.
- **Adding a dependency without closing its history.** Every past month turns provisional (step 4 above).
- **Reporting a date that isn't a month-end.** `closes.py` refuses it, because readiness is per month here.
- **Expecting a reopen to need a delete.** It doesn't: the latest report wins, and the earlier one stays as history.
- **Wanting readiness for one unit or one record.** This model is per product per month. Finer readiness (Unit 4's numbers are final but Unit 7's aren't) means dependencies by dimension, which is the natural next step.

### Where each piece lives

| File | Its job |
| --- | --- |
| `products/inputs/<input>.yml` | The business input: owner, system, deadline |
| `depends_on:` in `products/<product>.yml` | Which inputs a product needs |
| `readiness/closes.py` | sync, report, simulate, status |
| `ops.input_closes` | Every close ever reported (append-only) |
| `dbt/models/marts/readiness/period_readiness.sql` | The rule itself: final when every input has closed the month (a view, so it's live) |
| `cube/model/custody.yml` | `period_status`, `waiting_on`, the `period_readiness` view |
| `ontology/shapes.ttl` | `ProductInputsShape`, `InputShape` |
| `monitoring/prometheus/rules/lakehouse.yml` | `BusinessInputLate` |

## Good to know

- **No records, by design.** The graph holds meaning and tags, never a row of data, which is why reading it needs no login on the tailnet. For data, use Cube; for raw rows, the lake.
- **As fresh as the last load.** It reflects OpenMetadata as of the last `daily_lake` run or `bootstrap.sh`. `om_to_rdf.py --check` tells you whether it's behind.
- **Writes are locked.** Only the `writer` user can change the graph, and only `om_to_rdf.py` should. The admin endpoints (create, delete, back up) answer only inside the Fuseki container.
- **The addresses don't resolve.** IRIs such as `https://lakehouse.invalid/glossary/offender-number` are names, not links: `.invalid` is reserved never to resolve, so nothing points at a real host.
- **Exact names matter.** `lh:table` and `lh:name` are plain strings: `"gold.fct_offender_record"`, not `gold.fct_offender_record`. A query that returns nothing usually has a misspelled name or a missing `PREFIX` line.
- **Version.** Apache Jena Fuseki 6.2.0, built from Apache's verified release; more in the lakehouse README (Fuseki: SPARQL over the meaning).
- **What it doesn't do.** There is no OWL reasoner: nothing is inferred unless a rule file in ontology/rules/ says so, and recipe 10 shows which facts those are. There are no people or records in it either, so it can't answer "which offenders..." questions; ask Cube for those. It describes the data, and Cube counts it.
