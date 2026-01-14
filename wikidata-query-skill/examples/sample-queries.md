# Wikidata Query Examples

## Example 1: Films by Director (Spike Lee)

**Natural Language**: "Show me all movies directed by Spike Lee with release dates and budgets"

**Entity ID**: `wd:Q51566` (Spike Lee)

**SPARQL Query**:
```sparql
SELECT DISTINCT ?film ?filmLabel ?publicationDate ?budget
WHERE {
  ?film wdt:P57 wd:Q51566 ;        # director: Spike Lee
        wdt:P31 wd:Q11424 .         # instance of: film
  OPTIONAL { ?film wdt:P577 ?publicationDate . }
  OPTIONAL { ?film wdt:P2130 ?budget . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY DESC(?publicationDate)
```

## Example 2: Books by Author

**Natural Language**: "List all Harry Potter books by J.K. Rowling"

**Entity ID**: `wd:Q34660` (J.K. Rowling)

**SPARQL Query**:
```sparql
SELECT DISTINCT ?book ?bookLabel ?publicationDate ?pages
WHERE {
  ?book wdt:P50 wd:Q34660 ;        # author: J.K. Rowling
        wdt:P179 wd:Q8337 .        # part of series: Harry Potter
  OPTIONAL { ?book wdt:P577 ?publicationDate . }
  OPTIONAL { ?book wdt:P1104 ?pages . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY ?publicationDate
```

## Example 3: Nobel Prize Winners

**Natural Language**: "List Nobel Prize in Physics winners from the 21st century"

**SPARQL Query**:
```sparql
SELECT ?person ?personLabel ?awardYear ?countryLabel
WHERE {
  ?person wdt:P166 wd:Q38104 .     # award: Nobel Prize in Physics
  ?person wdt:P166 ?award .
  ?award wdt:P585 ?awardTime .
  BIND(YEAR(?awardTime) AS ?awardYear)
  OPTIONAL { ?person wdt:P27 ?country . }
  FILTER(?awardYear >= 2000)
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY DESC(?awardYear)
```

## Example 4: Geographic Queries

**Natural Language**: "What are the 20 most populous cities in the world?"

**SPARQL Query**:
```sparql
SELECT ?city ?cityLabel ?population ?countryLabel
WHERE {
  ?city wdt:P31 wd:Q515 ;          # instance of: city
        wdt:P1082 ?population ;    # population
        wdt:P17 ?country .         # country
  FILTER(?population > 1000000)
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY DESC(?population)
LIMIT 20
```

## Example 5: Software and Creators

**Natural Language**: "Show me popular programming languages and who created them"

**SPARQL Query**:
```sparql
SELECT ?language ?languageLabel ?creator ?creatorLabel ?inception
WHERE {
  ?language wdt:P31 wd:Q9143 .     # instance of: programming language
  OPTIONAL { ?language wdt:P170 ?creator . }
  OPTIONAL { ?language wdt:P571 ?inception . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY ?inception
LIMIT 30
```

## Example 6: Universities

**Natural Language**: "List top universities in the United States founded before 1900"

**SPARQL Query**:
```sparql
SELECT ?university ?universityLabel ?foundingDate ?cityLabel
WHERE {
  ?university wdt:P31 wd:Q3918 ;   # instance of: university
              wdt:P17 wd:Q30 ;     # country: United States
              wdt:P571 ?foundingDate .
  OPTIONAL { ?university wdt:P131 ?city . }
  FILTER(YEAR(?foundingDate) < 1900)
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY ?foundingDate
LIMIT 20
```

## Example 7: Musicians and Bands

**Natural Language**: "Who are members of The Beatles?"

**Entity ID**: `wd:Q1299` (The Beatles)

**SPARQL Query**:
```sparql
SELECT ?member ?memberLabel ?birthDate ?instrument ?instrumentLabel
WHERE {
  ?member wdt:P463 wd:Q1299 .      # member of: The Beatles
  OPTIONAL { ?member wdt:P569 ?birthDate . }
  OPTIONAL { ?member wdt:P1303 ?instrument . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY ?birthDate
```

## Example 8: Scientific Discoveries

**Natural Language**: "List major chemical elements and who discovered them"

**SPARQL Query**:
```sparql
SELECT ?element ?elementLabel ?symbol ?discoverer ?discovererLabel ?discoveryDate
WHERE {
  ?element wdt:P31 wd:Q11344 .     # instance of: chemical element
  OPTIONAL { ?element wdt:P246 ?symbol . }
  OPTIONAL { ?element wdt:P61 ?discoverer . }
  OPTIONAL { ?element wdt:P575 ?discoveryDate . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY ?discoveryDate
LIMIT 50
```

## Example 9: Sports Teams

**Natural Language**: "List NBA teams and their home cities"

**SPARQL Query**:
```sparql
SELECT ?team ?teamLabel ?city ?cityLabel ?founded
WHERE {
  ?team wdt:P118 wd:Q155223 ;      # league: NBA
        wdt:P159 ?city .           # headquarters location
  OPTIONAL { ?team wdt:P571 ?founded . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY ?teamLabel
```

## Example 10: Painters and Artworks

**Natural Language**: "Show me famous paintings by Vincent van Gogh"

**Entity ID**: `wd:Q5582` (Vincent van Gogh)

**SPARQL Query**:
```sparql
SELECT ?painting ?paintingLabel ?inception ?locationLabel
WHERE {
  ?painting wdt:P170 wd:Q5582 ;    # creator: Vincent van Gogh
            wdt:P31 wd:Q3305213 .  # instance of: painting
  OPTIONAL { ?painting wdt:P571 ?inception . }
  OPTIONAL { ?painting wdt:P276 ?location . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY ?inception
LIMIT 30
```

## Finding Entity Q-Numbers

### Method 1: Search Query
```sparql
SELECT ?item ?itemLabel ?itemDescription
WHERE {
  ?item rdfs:label "Albert Einstein"@en .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 5
```

### Method 2: With Type Filter
```sparql
SELECT ?item ?itemLabel ?itemDescription
WHERE {
  ?item rdfs:label "Microsoft"@en .
  ?item wdt:P31 wd:Q4830453 .      # instance of: business
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 5
```

## Common Property Reference

| Property | P-Number | Example |
|----------|----------|---------|
| director | P57 | Films |
| author | P50 | Books |
| publication date | P577 | Works |
| birth date | P569 | People |
| occupation | P106 | People |
| country | P17 | Locations |
| population | P1082 | Cities |
| capital | P36 | Countries |
| creator | P170 | Art, Software |
| instance of | P31 | Everything |

## Tips for Wikidata Queries

1. **Always use Label Service**: Makes results readable
2. **Find Q-numbers first**: Use Wikidata.org search
3. **Use OPTIONAL**: Many properties may not exist
4. **Filter wisely**: Add constraints to reduce results
5. **Order results**: Sort by dates, names, or values
6. **Limit output**: Start with LIMIT 100
7. **Test incrementally**: Build complex queries step by step
