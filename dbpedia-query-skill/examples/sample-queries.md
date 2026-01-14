# DBpedia Query Examples

## Example 1: Films by Director

**Natural Language**: "Show me all movies directed by Spike Lee with their budgets"

**SPARQL Query**:
```sparql
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dbp: <http://dbpedia.org/property/>

SELECT DISTINCT ?film ?title ?date ?budget
WHERE {
  ?film dbo:director dbr:Spike_Lee ;
        a dbo:Film ;
        rdfs:label ?title .
  OPTIONAL { ?film dbp:date ?date }
  OPTIONAL { ?film dbo:budget ?budget }
  FILTER(LANG(?title) = 'en')
}
ORDER BY DESC(?date)
```

## Example 2: Most Populous Cities

**Natural Language**: "What are the 20 largest cities in the world by population?"

**SPARQL Query**:
```sparql
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?city ?name ?population ?country
WHERE {
  ?city a dbo:City ;
        rdfs:label ?name ;
        dbo:populationTotal ?population ;
        dbo:country ?countryRes .
  ?countryRes rdfs:label ?country .
  FILTER(LANG(?name) = 'en' && LANG(?country) = 'en')
  FILTER(?population > 1000000)
}
ORDER BY DESC(?population)
LIMIT 20
```

## Example 3: Books by Author

**Natural Language**: "List all books by Agatha Christie"

**SPARQL Query**:
```sparql
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?book ?title ?publicationDate
WHERE {
  ?book dbo:author dbr:Agatha_Christie ;
        a dbo:Book ;
        rdfs:label ?title .
  OPTIONAL { ?book dbo:publicationDate ?publicationDate }
  FILTER(LANG(?title) = 'en')
}
ORDER BY ?publicationDate
```

## Example 4: University Information

**Natural Language**: "Show me universities in California with their founding dates"

**SPARQL Query**:
```sparql
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?university ?name ?foundingDate ?city
WHERE {
  ?university a dbo:University ;
              dbo:state dbr:California ;
              rdfs:label ?name .
  OPTIONAL { ?university dbo:foundingDate ?foundingDate }
  OPTIONAL { ?university dbo:city ?cityRes .
             ?cityRes rdfs:label ?city .
             FILTER(LANG(?city) = 'en') }
  FILTER(LANG(?name) = 'en')
}
ORDER BY ?foundingDate
```

## Example 5: Sports Teams

**Natural Language**: "What NBA teams are there and where are they located?"

**SPARQL Query**:
```sparql
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?team ?name ?city ?cityName
WHERE {
  ?team dbo:league dbr:National_Basketball_Association ;
        rdfs:label ?name ;
        dbo:city ?city .
  ?city rdfs:label ?cityName .
  FILTER(LANG(?name) = 'en' && LANG(?cityName) = 'en')
}
ORDER BY ?name
```

## Example 6: Nobel Prize Winners

**Natural Language**: "List Nobel Prize in Literature winners from the last 20 years"

**SPARQL Query**:
```sparql
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?person ?name ?year
WHERE {
  ?person dbo:award dbr:Nobel_Prize_in_Literature ;
          rdfs:label ?name ;
          dbo:birthDate ?birthDate .
  ?award dbo:year ?year .
  FILTER(LANG(?name) = 'en' && ?year > 2004)
}
ORDER BY DESC(?year)
```

## Example 7: Programming Languages

**Natural Language**: "Show me programming languages and who designed them"

**SPARQL Query**:
```sparql
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?language ?name ?designer ?designerName
WHERE {
  ?language a dbo:ProgrammingLanguage ;
            rdfs:label ?name .
  OPTIONAL { ?language dbo:designer ?designer .
             ?designer rdfs:label ?designerName .
             FILTER(LANG(?designerName) = 'en') }
  FILTER(LANG(?name) = 'en')
}
ORDER BY ?name
LIMIT 50
```

## Example 8: Mountain Heights

**Natural Language**: "What are the highest mountains in the world?"

**SPARQL Query**:
```sparql
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?mountain ?name ?elevation ?range
WHERE {
  ?mountain a dbo:Mountain ;
            rdfs:label ?name ;
            dbo:elevation ?elevation .
  OPTIONAL { ?mountain dbo:mountainRange ?rangeRes .
             ?rangeRes rdfs:label ?range .
             FILTER(LANG(?range) = 'en') }
  FILTER(LANG(?name) = 'en')
}
ORDER BY DESC(?elevation)
LIMIT 20
```

## Tips for Creating Queries

1. **Start with entity type**: Use `a dbo:Film`, `a dbo:Person`, etc.
2. **Add filters**: Always filter by language for labels
3. **Use OPTIONAL**: For properties that might not exist
4. **Sort results**: Make output meaningful with ORDER BY
5. **Limit results**: Don't overwhelm with too many results
6. **Check entity names**: DBpedia uses underscores (e.g., `Spike_Lee`)
