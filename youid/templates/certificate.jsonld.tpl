{
    "@context": {
        "owl": "http://www.w3.org/2002/07/owl#", 
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#", 
        "oplcert": "http://www.openlinksw.com/schemas/cert#", 
        "cert": "http://www.w3.org/ns/auth/cert#", 
        "foaf": "http://xmlns.com/foaf/0.1/", 
        "xhv": "http://www.w3.org/1999/xhtml/vocab#", 
        "xsd": "http://www.w3.org/2001/XMLSchema#", 
       "xsig": "http://www.w3.org/2000/09/xmldsig#",
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
      "@id": "%{jsonld_cert_url}", 
      "foaf:primaryTopic": "%{jsonld_cert_url}#cert"
    },
    {
      "@id": "%{jsonld_cert_url}#cert",
      "@type": "oplcert:Certificate",%{ian}
      "oplcert:SAN": "%{jsonld_prof_url}#identity",
!{ca_cert_url}      "oplcert:IAN": { "@id" : "%{ca_cert_url}"},
      "oplcert:issuer": "%{issuer}",
      "oplcert:notAfter": {
        "@value": "%{date_after}",
        "@type": "xsd:dateTime"
      },
      "oplcert:notBefore": {
        "@value": "%{date_before}",
        "@type": "xsd:dateTime"
      },
      "oplcert:serial": "%{serial}",
      "oplcert:subject": "%{subject}",
      "oplcert:hasPublicKey": "%{jsonld_pubkey_url}#PublicKey",
      "oplcert:fingerprint": "%{fingerprint_hex}",
      "oplcert:fingerprint-digest": [
        {
          "@type": "xsig:sha1",
          "@value": "%{fingerprint_hex}"
        },
        {
          "@type": "xsig:sha256",
          "@value": "%{fingerprint_256_hex}"
        }
      ]
    },
    {
      "@id": "%{jsonld_prof_url}#identity",
      "oplcert:hasCertificate": "%{jsonld_cert_url}#cert",
      "rdfs:label": "Digital Identity Card Subject: %{subj_name}"
    }
  ]
}