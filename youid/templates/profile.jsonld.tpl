{
  "@context": {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "schema": "http://schema.org/",
    "foaf": "http://xmlns.com/foaf/0.1/",
    "cert": "http://www.w3.org/ns/auth/cert#",
    "oplcert": "http://www.openlinksw.com/schemas/cert#",
    "xhv": "http://www.w3.org/1999/xhtml/vocab#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "xsig": "http://www.w3.org/2000/09/xmldsig#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "pim": "http://www.w3.org/ns/pim/space#"
  },
  "@graph": [
    {
      "@id": "%{card_ident_url}",
      "cert:key": {
        "@id": "%{jsonld_pubkey_url}#PublicKey"
      }
    },
    {
      "@id": "%{jsonld_prof_url}#identity",
      "cert:key": {
        "@id": "%{jsonld_pubkey_url}#PublicKey"
      }
    },
    {
      "@id": "%{jsonld_pubkey_url}#PublicKey",
      "@type": "cert:RSAPublicKey",
      "cert:exponent": {
        "@type": "xsd:int",
        "@value": "%{exponent}"
      },
      "cert:modulus": {
        "@type": "xsd:hexBinary",
        "@value": "%{modulus}"
      },
      "owl:sameAs": [
        {
         "@id": "%{fingerprint_ni}"
        },
        {
         "@id": "%{fingerprint_di}"
        }
      ]
    },

    {
      "@id": "%{jsonld_prof_url}#identity",
      "oplcert:hasCertificate": {
        "@id": "%{jsonld_cert_url}#cert"
      }
    },

    {
      "@id": "%{jsonld_cert_url}#cert",
      "@type": "oplcert:Certificate",
      "oplcert:subject": "%{subject}",
      "oplcert:issuer": "%{issuer}",
      "oplcert:notBefore": {
        "@type": "xsd:dateTime",
        "@value": "%{date_before}"
      },
      "oplcert:notAfter": {
        "@type": "xsd:dateTime",
        "@value": "%{date_after}"
      },
      "oplcert:serial": "%{serial}",
!{ca_cert_url}      "oplcert:IAN": { "@id" : "%{ca_cert_url}"},
      "oplcert:SAN": {
        "@id": "%{jsonld_prof_url}#identity"
      },
      "oplcert:hasPublicKey": {
        "@id": "%{jsonld_pubkey_url}#PublicKey"
      },
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
!!{ca_cert_url}
    {
      "@id": "%{cert_url}#cert",
      "xhv:alternate": {
        "@id": "%{ca_cert_url}"
      }
    },
!!.
!!{pdp_url}
    {
      "@id": "%{pdp_url}",
      "@type": "schema:Person",
      "oplcert:owns": {
        "@id": "%{jsonld_cert_url}#cert"
      },
      "schema:sameAs": {
        "@id": "%{jsonld_prof_url}"
      }
    },
!!.
    {
      "@id": "%{card_url}",
      "@type": [
        "schema:CreativeWork",
        "oplcert:Certificate",
        "schema:WebPage"
      ],
      "schema:additionalType": [
        {
          "@id": "oplcert:Certificate"
        },
        {
          "@id": "schema:CreativeWork"
        },
        {
          "@id": "schema:WebPage"
        }
      ],
      "schema:url": {
        "@id": "#this"
      },
      "schema:name": "%{subj_name}",
      "schema:author": {
        "@id": "%{jsonld_prof_url}#identity"
      },
      "schema:mainEntity": {
        "@id": "%{jsonld_prof_url}#identity"
      },
      "oplcert:SAN": {
        "@id": "%{jsonld_prof_url}#identity"
      },
      "oplcert:hasPublicKey": {
        "@id": "%{jsonld_pubkey_url}#PublicKey"
      },
      "cert:key": {
        "@id": "%{jsonld_pubkey_url}#PublicKey"
      }
    },

    {
      "@id": "%{card_url}",
      "schema:isRelatedTo": [
        {
          "@id": "%{card_ident_url}"
        },
        {
          "@id": "%{jsonld_prof_url}#identity"
        },
        {
          "@id": "%{rdfa_prof_url}#identity"
        },
        {
          "@id": "%{prof_url}#identity"
        }
      ]
    },

    {
      "@id": "%{card_ident_url}",
      "owl:sameAs": [
        {
          "@id": "%{jsonld_prof_url}#identity"
        },
        {
          "@id": "%{rdfa_prof_url}#identity"
        },
        {
          "@id": "%{prof_url}#identity"
        }
      ]
    },

    {
      "@id": "%{jsonld_prof_url}#identity",
      "schema:isRelatedTo": {
        "@id": "%{jsonld_cert_url}#cert"
      }
    },

    {
      "@id": "%{card_url}",
      "@type": "schema:WebPage",
      "schema:mainEntity": {
        "@id": "%{card_ident_url}"
      }
    },

    {
      "@id": "%{card_ident_url}",
      "@type": "schema:Person",
!{subj_email}      "schema:email": "%{subj_email}",
!{subj_email}      "foaf:mbox": {  "@id": "mailto:%{subj_email}"  },
!{subj_org}      "schema:worksFor": { "@type": "schema:Organization", "schema:name": "%{subj_org}" },
      "schema:address": {
        "@type": "schema:Place"
!{subj_country}      , "schema:addressCountry": "%{subj_country}"
!{subj_state}        , "schema:addressRegion": "%{subj_state}"
      },
!{pdp_url}      "owl:sameAs": { "@id": "%{pdp_url}#this" },
!{pdp_url}      "schema:sameAs": { "@id": "%{pdp_url}" },
!{pim_storage}      "pim:storage": { "@id": "%{pim_storage}" },
      "schema:name": "%{subj_name}"
    },

    {
      "@id": "%{prof_url}",
      "@type": "schema:Person",
      "schema:sameAs": [
        {
          "@id": "%{rdfa_prof_url}"
        },
        {
          "@id": "%{card_url}"
        },
        {
          "@id": "%{jsonld_prof_url}"
        }
      ]
    },


!!{pdp_mail}
    {
      "@id": "%{jsonld_prof_url}#identity",
      "@type": "foaf:Agent",
      "foaf:mbox": {
        "@id": "mailto:%{pdp_mail}"
      },
      "foaf:mbox_sha1sum": "%{pdp_mail_sha1}",
      "oplcert:owns": {
        "@id": "%{jsonld_cert_url}#cert"
      }
    },
!!.

    {
      "@id": "%{card_url}",
      "@type": [
        "foaf:profileDocument",
        "oplcert:Certificate"
      ],
      "rdfs:label": "Profile Document Subject:  %{subj_name}",
      "schema:about": {
        "@id": "%{jsonld_prof_url}#identity"
      },
      "foaf:primaryTopic": {
        "@id": "%{jsonld_prof_url}#identity"
      },
      "oplcert:SAN": {
        "@id": "%{jsonld_prof_url}#identity"
      },
      "oplcert:hasPublicKey": {
        "@id": "%{jsonld_pubkey_url}#PublicKey"
      },
      "cert:key": {
        "@id": "%{jsonld_pubkey_url}#PublicKey"
      }
    },

    {
      "@id": "%{card_url}",
      "xhv:alternate": [
        {
          "@id": "%{card_ident_url}"
        },
        {
          "@id": "%{prof_url}#identity"
        },
        {
          "@id": "%{rdfa_prof_url}#identity"
        },
        {
          "@id": "%{jsonld_prof_url}#identity"
        }
      ]
    },

    {
      "@id": "%{card_ident_url}",
      "owl:sameAs": [
!{relList_json} %{relList_json}
        {
          "@id": "%{jsonld_prof_url}#identity"
        },
        {
          "@id": "%{rdfa_prof_url}#identity"
        },
        {
          "@id": "%{prof_url}#identity"
        }
      ]
    },

    {
      "@id": "%{card_ident_url}",
      "schema:sameAs": [
!{relList_json} %{relList_json}
        {
          "@id": "%{jsonld_prof_url}"
        },
        {
          "@id": "%{rdfa_prof_url}"
        },
        {
          "@id": "%{prof_url}"
        }
      ]
    },

    {
      "@id": "%{jsonld_prof_url}#identity",
      "xhv:alt": {
        "@id": "%{jsonld_cert_url}#cert"
      }
    }
  ]
}
