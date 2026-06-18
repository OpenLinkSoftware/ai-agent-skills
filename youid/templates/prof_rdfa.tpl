<div xmlns="http://www.w3.org/1999/xhtml"
  prefix="
    foaf: http://xmlns.com/foaf/0.1/
    owl: http://www.w3.org/2002/07/owl#
    rdfs: http://www.w3.org/2000/01/rdf-schema#
    cert: http://www.w3.org/ns/auth/cert#
    oplcert: http://www.openlinksw.com/schemas/cert#
    rdf: http://www.w3.org/1999/02/22-rdf-syntax-ns#
    xhv: http://www.w3.org/1999/xhtml/vocab#
    xsd: http://www.w3.org/2001/XMLSchema#
   xsig: http://www.w3.org/2000/09/xmldsig#
    schema: http://schema.org/
    pim: http://www.w3.org/ns/pim/space#"
  >

  <div typeof="rdfs:Resource" about="%{rdfa_prof_url}#identity">
    <div rel="cert:key">
      <div typeof="cert:RSAPublicKey" about="%{rdfa_pubkey_url}#PublicKey">
        <div property="cert:exponent" datatype="xsd:int" content="%{exponent}"></div>
        <div property="cert:modulus" datatype="xsd:hexBinary" content="%{modulus}"></div>

        <div rel="owl:sameAs" resource="%{fingerprint_ni}"></div>
        <div rel="owl:sameAs" resource="%{fingerprint_di}"></div>

      </div>
    </div>
  </div>

  <div typeof="rdfs:Resource" about="%{card_ident_url}">
    <div rel="cert:key">
      <div typeof="cert:RSAPublicKey" about="%{rdfa_pubkey_url}#PublicKey">
      </div>
    </div>
  </div>

  <div typeof="rdfs:Resource" about="%{rdfa_prof_url}#identity">
    <div rel="oplcert:hasCertificate" resource="%{rdfa_cert_url}#cert"></div>
  </div>

 <div typeof="oplcert:Certificate" about="%{rdfa_cert_url}#cert">
    <div property="oplcert:subject" content="%{subject}"></div>
    <div property="oplcert:issuer" content="%{issuer}"></div>
    <div property="oplcert:notBefore" datatype="xsd:dateTime" content="%{date_before}"></div>
    <div property="oplcert:notAfter" datatype="xsd:dateTime" content="%{date_after}"></div>
    <div property="oplcert:serial" content="%{serial}"></div>
    <div rel="oplcert:SAN" resource="%{rdfa_prof_url}#identity"></div>
!{ca_cert_url}    <div rel="oplcert:IAN" resource="%{ca_cert_url}"></div>
    <div rel="oplcert:hasPublicKey" resource="%{rdfa_pubkey_url}#PublicKey"></div>
    <div property="oplcert:fingerprint" content="%{fingerprint_hex}"></div>
    <div property="oplcert:fingerprint-digest" datatype="xsig:sha1" content="%{fingerprint_hex}"></div>
    <div property="oplcert:fingerprint-digest" datatype="xsig:sha256" content="%{fingerprint_256_hex}"></div>
  </div>

!!{ca_cert_url}
  <div typeof="rdfs:Resource" about="%{cert_url}#cert">
    <div rel="xhv:alternate" resource="%{ca_cert_url}"></div>
  </div>
!!.

!!{pdp_url}
  <div typeof="http://schema.org/Person" about="%{pdp_url}">
    <div rel="http://schema.org/sameAs" resource="%{rdfa_prof_url}"></div>
    <div rel="oplcert:owns" resource="%{rdfa_cert_url}#cert"></div>
  </div>
!!.

  <div typeof="http://schema.org/WebPage" about="%{card_url}">
    <div rel="rdf:type" resource="http://www.openlinksw.com/schemas/cert#Certificate"></div>
    <div rel="rdf:type" resource="http://schema.org/CreativeWork"></div>
    <div rel="http://schema.org/additionalType" resource="http://www.openlinksw.com/schemas/cert#Certificate"></div>
    <div rel="http://schema.org/additionalType" resource="http://schema.org/CreativeWork"></div>
    <div rel="http://schema.org/additionalType" resource="http://schema.org/WebPage"></div>
    <div rel="http://schema.org/url" resource="#this"></div>
    <div property="http://schema.org/name" content="%{subj_name}"></div>
    <div rel="http://schema.org/author" resource="%{rdfa_prof_url}#identity"></div>
    <div rel="http://schema.org/mainEntity" resource="%{rdfa_prof_url}#identity"></div>
    <div rel="oplcert:SAN" resource="%{rdfa_prof_url}#identity"></div>
    <div rel="oplcert:hasPublicKey" resource="%{rdfa_pubkey_url}#PublicKey"></div>
    <div rel="cert:key" resource="%{rdfa_pubkey_url}#PublicKey"></div>
  </div>

  <div typeof="rdfs:Resource" about="%{card_url}">
    <div rel="http://schema.org/isRelatedTo" resource="%{card_ident_url}"></div>
    <div rel="http://schema.org/isRelatedTo" resource="%{prof_url}#identity"></div>
    <div rel="http://schema.org/isRelatedTo" resource="%{jsonld_prof_url}#identity"></div>
    <div rel="http://schema.org/isRelatedTo" resource="%{rdfa_prof_url}#identity"></div>
  </div>

  <div typeof="rdfs:Resource" about="%{card_ident_url}">
    <div rel="owl:sameAs" resource="%{jsonld_prof_url}#identity"></div>
    <div rel="owl:sameAs" resource="%{rdfa_prof_url}#identity"></div>
    <div rel="owl:sameAs" resource="%{prof_url}#identity"></div>
  </div>

  <div typeof="rdfs:Resource" about="%{rdfa_prof_url}#identity">
    <div rel="http://schema.org/isRelatedTo" resource="%{rdfa_cert_url}#cert"></div>
  </div>

  <div typeof="http://schema.org/WebPage" about="%{card_url}">
    <div rel="http://schema.org/mainEntity" resource="%{card_ident_url}"></div>
  </div>

  <div typeof="http://schema.org/Person" about="%{card_ident_url}">
!{subj_email}    <div property="http://schema.org/email" content="%{subj_email}"></div>
!{subj_email}    <div rel="foaf:mbox" resource="mailto:%{subj_email}"></div>
    <div rel="http://schema.org/worksFor">
      <div typeof="http://schema.org/Organization">
        <div property="http://schema.org/name" content="%{subj_org}"></div>
      </div>
    </div>
    <div rel="http://schema.org/address">
      <div typeof="http://schema.org/Place">
!{subj_state}        <div property="http://schema.org/addressRegion" content="%{subj_state}"></div>
!{subj_country}        <div property="http://schema.org/addressCountry" content="%{subj_country}"></div>
      </div>
    </div>
    <div property="http://schema.org/name" content="%{subj_name}"></div>
!{pdp_url}    <div rel="http://schema.org/sameAs" resource="%{pdp_url}"></div>
!{pdp_url}    <div rel="owl:sameAs" resource="%{pdp_url}#this"></div>
!{pim_storage}    <div rel="pim:storage" resource="%{pim_storage}"></div>
  </div>

  <div typeof="http://schema.org/Person" about="%{prof_url}#identity">
    <div rel="http://schema.org/sameAs" resource="%{card_url}"></div>
    <div rel="http://schema.org/sameAs" resource="%{rdfa_prof_url}"></div>
    <div rel="http://schema.org/sameAs" resource="%{jsonld_prof_url}"></div>
  </div>


!!{pdp_mail}
  <div typeof="foaf:Agent" about="%{rdfa_prof_url}#identity">
    <div property="foaf:mbox_sha1sum" content="%{pdp_mail_sha1}"></div>
    <div rel="foaf:mbox" resource="mailto:%{pdp_mail}"></div>
    <div rel="oplcert:owns" resource="%{rdfa_cert_url}#cert"></div>
  </div>
!!.

  <div typeof="foaf:profileDocument" about="%{card_url}">
    <div rel="rdf:type" resource="http://www.openlinksw.com/schemas/cert#Certificate"></div>
    <div property="rdfs:label" content="Profile Document Subject: %{subj_name}"></div>
    <div rel="foaf:primaryTopic" resource="%{rdfa_prof_url}#identity"></div>
    <div rel="oplcert:SAN" resource="%{rdfa_prof_url}#identity"></div>
    <div rel="oplcert:hasPublicKey" resource="%{rdfa_pubkey_url}#PublicKey"></div>
    <div rel="cert:key" resource="%{rdfa_pubkey_url}#PublicKey"></div>
  </div>

  <div typeof="rdfs:Resource" about="%{card_url}">
    <div rel="xhv:alternate" resource="%{card_ident_url}"></div>
    <div rel="xhv:alternate" resource="%{rdfa_prof_url}#identity"></div>
    <div rel="xhv:alternate" resource="%{jsonld_prof_url}#identity"></div>
    <div rel="xhv:alternate" resource="%{prof_url}#identity"></div>
  </div>

  <div typeof="rdfs:Resource" about="%{card_ident_url}">
!{relList_rdfa} %{relList_rdfa}
    <div rel="owl:sameAs" resource="%{jsonld_prof_url}#identity"></div>
    <div rel="owl:sameAs" resource="%{prof_url}#identity"></div>
    <div rel="owl:sameAs" resource="%{rdfa_prof_url}#identity"></div>
  </div>

  <div typeof="rdfs:Resource" about="%{card_ident_url}">
!{relList_rdfa_schema} %{relList_rdfa_schema}
    <div rel="schema:sameAs" resource="%{jsonld_prof_url}"></div>
    <div rel="schema:sameAs" resource="%{prof_url}"></div>
    <div rel="schema:sameAs" resource="%{rdfa_prof_url}"></div>
  </div>

  <div typeof="rdfs:Resource" about="%{rdfa_prof_url}#identity">
    <div rel="xhv:alt" resource="%{rdfa_cert_url}#cert"></div>
  </div>

</div>
