# SHACL Shape Templates for Infographic Entities

## ImageObject Shape (PNG files)

```turtle
@prefix sh:    <http://www.w3.org/ns/shacl#> .
@prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix schema: <http://schema.org/> .
@prefix wdrs:  <http://www.w3.org/2007/05/powder-s#> .
@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .

<#InfographicImageShape>
    a sh:NodeShape ;
    sh:targetClass schema:ImageObject ;
    sh:property [
        sh:path rdf:type ;
        sh:hasValue schema:ImageObject ;
        sh:minCount 1 ; sh:maxCount 1 ;
    ] ;
    sh:property [
        sh:path schema:name ;
        sh:datatype xsd:string ;
        sh:minCount 1 ; sh:maxCount 1 ; sh:minLength 1 ;
    ] ;
    sh:property [
        sh:path schema:description ;
        sh:datatype xsd:string ;
        sh:minCount 1 ; sh:maxCount 1 ; sh:minLength 1 ;
    ] ;
    sh:property [
        sh:path schema:encodingFormat ;
        sh:datatype xsd:string ;
        sh:hasValue "image/png" ;
        sh:minCount 1 ; sh:maxCount 1 ;
    ] ;
    sh:property [
        sh:path schema:contentUrl ;
        sh:class rdf:Resource ;
        sh:minCount 1 ; sh:maxCount 1 ;
    ] ;
    sh:property [
        sh:path schema:thumbnailUrl ;
        sh:class rdf:Resource ;
        sh:minCount 0 ; sh:maxCount 1 ;
    ] ;
    sh:property [
        sh:path schema:category ;
        sh:minCount 1 ;
    ] ;
    sh:property [
        sh:path schema:dateCreated ;
        sh:datatype xsd:dateTime ;
        sh:minCount 0 ; sh:maxCount 1 ;
    ] ;
    sh:property [
        sh:path schema:dateModified ;
        sh:datatype xsd:dateTime ;
        sh:minCount 0 ; sh:maxCount 1 ;
    ] ;
    sh:property [
        sh:path wdrs:describedby ;
        sh:minCount 1 ;
    ] .
```

## VideoObject Shape (MP4 files)

Same structure but with:
- `sh:targetClass schema:VideoObject`
- `sh:hasValue schema:VideoObject` for rdf:type
- `sh:hasValue "video/mp4"` for encodingFormat

## WebPage Shape (HTML files)

Same structure but with:
- `sh:targetClass schema:WebPage`
- `sh:hasValue schema:WebPage` for rdf:type
- `sh:hasValue "text/html"` for encodingFormat

## Notes

- `thumbnailUrl`, `dateCreated`, `dateModified` use `sh:minCount 0` because most files lack these
- `category` uses `sh:minCount 1` — at minimum the directory-based default category applies
- `wdrs:describedby` uses `sh:minCount 1` — the describe endpoint URL is always constructible
