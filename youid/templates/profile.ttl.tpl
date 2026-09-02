@prefix rsa: <http://www.w3.org/ns/auth/rsa#> .
@prefix cert: <http://www.w3.org/ns/auth/cert#> .
@prefix oplcert: <http://www.openlinksw.com/schemas/cert#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix xhv: <http://www.w3.org/1999/xhtml/vocab#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
@prefix schema: <http://schema.org/> .
@prefix xsig: <http://www.w3.org/2000/09/xmldsig#>  . 
@prefix pim: <http://www.w3.org/ns/pim/space#> .

<%{card_ident_url}>    cert:key <%{pubkey_url}#PublicKey> . 
<%{prof_url}#identity>    cert:key <%{pubkey_url}#PublicKey> . 
<%{pubkey_url}#PublicKey>    a cert:RSAPublicKey ; 
         cert:modulus "%{modulus}"^^xsd:hexBinary ; 
         cert:exponent "%{exponent}"^^xsd:int ;
         owl:sameAs <%{fingerprint_ni}>, <%{fingerprint_di}> . 

<%{prof_url}#identity> oplcert:hasCertificate <%{cert_url}#cert> . 
<%{cert_url}#cert>     a oplcert:Certificate ; 
         oplcert:subject "%{subject}" ; 
         oplcert:issuer "%{issuer}" ; 
         oplcert:notBefore "%{date_before}"^^xsd:dateTime ; 
         oplcert:notAfter "%{date_after}"^^xsd:dateTime ; 
         oplcert:serial "%{serial}" ; 
         oplcert:SAN <%{prof_url}#identity> ;
!{ca_cert_url}         oplcert:IAN <%{ca_cert_url}> ;
         oplcert:hasPublicKey <%{pubkey_url}#PublicKey> ;
         oplcert:fingerprint "%{fingerprint_hex}" ; 
         oplcert:fingerprint-digest "%{fingerprint_hex}"^^xsig:sha1, "%{fingerprint_256_hex}"^^xsig:sha256 .

!!{ca_cert_url}
<%{cert_url}#cert> xhv:alternate <%{ca_cert_url}> .
!!.

!!{pdp_url}
<%{pdp_url}> a <http://schema.org/Person> ; 
    <http://schema.org/sameAs> <%{prof_url}> ;
    oplcert:owns <%{cert_url}#cert> .
!!.

<> 
    a     <http://schema.org/CreativeWork>, 
          <http://schema.org/WebPage> , 
          oplcert:Certificate ;
    <http://schema.org/additionalType> <http://schema.org/CreativeWork>, 
                                      <http://schema.org/WebPage> , 
                                      oplcert:Certificate ;
    <http://schema.org/url>            <#this>  ;
    <http://schema.org/name>          "%{subj_name}" ;
    <http://schema.org/author>         <%{prof_url}#identity> ;
    <http://schema.org/mainEntity>     <%{prof_url}#identity> ;
    oplcert:SAN           <%{prof_url}#identity> ;
    oplcert:hasPublicKey  <%{pubkey_url}#PublicKey> ;
    cert:key  <%{pubkey_url}#PublicKey> .


<> <http://schema.org/isRelatedTo> <%{card_ident_url}>;
   <http://schema.org/isRelatedTo> <%{jsonld_prof_url}#identity> ;
   <http://schema.org/isRelatedTo> <%{rdfa_prof_url}#identity> ;
   <http://schema.org/isRelatedTo> <%{prof_url}#identity> .


<%{card_ident_url}> owl:sameAs <%{jsonld_prof_url}#identity> ,
	                          <%{rdfa_prof_url}#identity> ,
	                          <%{prof_url}#identity> .


<%{prof_url}#identity> <http://schema.org/isRelatedTo> <%{cert_url}#cert> .


<%{card_url}> a   <http://schema.org/WebPage> ;
              <http://schema.org/mainEntity> <%{card_ident_url}> .
  

<%{card_ident_url}> a <http://schema.org/Person> ;
!{subj_email}       <http://schema.org/email> "%{subj_email}" ;
!{subj_email}       foaf:mbox <mailto:%{subj_email}> ;
!{subj_org}         <http://schema.org/worksFor> [ a <http://schema.org/Organization> ; <http://schema.org/name> "%{subj_org}" ] ;
     <http://schema.org/address> 
        [a <http://schema.org/Place>  
!{subj_state}      ; <http://schema.org/addressRegion> "%{subj_state}" 
!{subj_country}      ; <http://schema.org/addressCountry> "%{subj_country}"
        ] ;
!{pdp_url}     owl:sameAs    <%{pdp_url}#this> ;
!{pdp_url}     <http://schema.org/sameAs> <%{pdp_url}> ;
!{pim_storage}     pim:storage  <%{pim_storage}> ;
     <http://schema.org/name>   "%{subj_name}" .

<%{prof_url}> 
  a <http://schema.org/Person> ;
    <http://schema.org/sameAs> <%{card_url}>, 
                  <%{rdfa_prof_url}>, 
                  <%{jsonld_prof_url}> .


!!{pdp_mail}

<%{prof_url}#identity> a foaf:Agent ; 
    foaf:mbox <mailto:%{pdp_mail}> ;
    foaf:mbox_sha1sum "%{pdp_mail_sha1}" ;
    oplcert:owns <%{cert_url}#cert> .
!!.

<> 
a foaf:profileDocument , oplcert:Certificate ;
  rdfs:label           "Profile Document Subject: %{subj_name}" ;
  foaf:primaryTopic     <%{prof_url}#identity> ;
  oplcert:SAN           <%{prof_url}#identity> ;
  oplcert:hasPublicKey  <%{pubkey_url}#PublicKey> ;
  cert:key  <%{pubkey_url}#PublicKey> .

<> xhv:alternate <%{card_ident_url}>;
   xhv:alternate <%{jsonld_prof_url}#identity> ;
   xhv:alternate <%{rdfa_prof_url}#identity> ;
   xhv:alternate <%{prof_url}#identity> .


<%{card_ident_url}> owl:sameAs <%{jsonld_prof_url}#identity> ,
!{relList} %{relList}
	<%{rdfa_prof_url}#identity> ,
	<%{prof_url}#identity> .

<%{card_ident_url}> schema:sameAs <%{jsonld_prof_url}> ,
!{relList} %{relList}
	<%{rdfa_prof_url}> ,
	<%{prof_url}> .

<%{prof_url}#identity> xhv:alt <%{cert_url}#cert> .


