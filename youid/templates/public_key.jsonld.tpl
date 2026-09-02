{
    "@context": {
        "owl": "http://www.w3.org/2002/07/owl#", 
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#", 
        "oplcert": "http://www.openlinksw.com/schemas/cert#", 
        "cert": "http://www.w3.org/ns/auth/cert#", 
        "foaf": "http://xmlns.com/foaf/0.1/", 
        "xhv": "http://www.w3.org/1999/xhtml/vocab#", 
        "xsd": "http://www.w3.org/2001/XMLSchema#", 
        "oplcert:signature": {
            "@type": "@id"
        }, 
        "oplcert:hasCertificate": {
            "@type": "@id"
        }, 
        "owl:sameAs": {
            "@type": "@id"
        }, 
        "oplcert:owns": {
            "@type": "@id"
        }, 
        "foaf:page": {
            "@type": "@id"
        }, 
        "foaf:mbox": {
            "@type": "@id"
        }, 
        "foaf:primaryTopic": {
            "@type": "@id"
        }, 
        "xhv:alternate": {
            "@type": "@id"
        }, 
        "oplcert:SAN": {
            "@type": "@id"
        }, 
        "cert:key": {
            "@type": "@id"
        }, 
        "oplcert:hasPublicKey": {
            "@type": "@id"
        }
    }, 

  "@graph": [
    {
      "@id": "%{jsonld_pubkey_url}", 
      "foaf:primaryTopic": "%{jsonld_pubkey_url}#PublicKey"
    },
    {
      "@id": "%{jsonld_cert_url}#cert",
      "@type": "oplcert:Certificate",
      "oplcert:hasPublicKey": "%{jsonld_pubkey_url}#PublicKey"
    },
    {
      "@id": "%{jsonld_prof_url}#identity",
      "cert:key": "%{jsonld_pubkey_url}#PublicKey"
    },
    {
      "@id": "%{jsonld_pubkey_url}#PublicKey",
      "@type": "cert:RSAPublicKey",
      "cert:exponent": {
        "@value": "%{exponent}",
        "@type": "xsd:int"
      },
      "cert:modulus": {
        "@value": "%{modulus}",
        "@type": "xsd:hexBinary"
      },
      "owl:sameAs": [
        {
         "@id": "%{fingerprint_ni}"
        },
        {
         "@id": "%{fingerprint_di}"
        }
      ]
    }
  ]
}