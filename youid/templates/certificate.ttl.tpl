@prefix rsa: <http://www.w3.org/ns/auth/rsa#> .
@prefix cert: <http://www.w3.org/ns/auth/cert#> .
@prefix oplcert: <http://www.openlinksw.com/schemas/cert#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix xsig: <http://www.w3.org/2000/09/xmldsig#>  . 

<%{prof_url}#identity>    oplcert:hasCertificate <%{cert_url}#cert> ; 
                  rdfs:label  "Digital Identity Card Subject: %{subj_name}" . 
<%{cert_url}#cert>    a oplcert:Certificate ; 
         oplcert:subject "%{subject}" ; 
         oplcert:issuer "%{issuer}" ; 
         oplcert:notBefore "%{date_before}"^^xsd:dateTime ; 
         oplcert:notAfter "%{date_after}"^^xsd:dateTime ; 
         oplcert:serial "%{serial}" ; 
         oplcert:SAN <%{prof_url}#identity> ; %{ian}
!{ca_cert_url}         oplcert:IAN <%{ca_cert_url}> ;
         oplcert:hasPublicKey <%{pubkey_url}#PublicKey> ;  
         oplcert:fingerprint "%{fingerprint_hex}" ; 
         oplcert:fingerprint-digest "%{fingerprint_hex}"^^xsig:sha1, "%{fingerprint_256_hex}"^^xsig:sha256 .

