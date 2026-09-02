@prefix rsa: <http://www.w3.org/ns/auth/rsa#> .
@prefix cert: <http://www.w3.org/ns/auth/cert#> .
@prefix oplcert: <http://www.openlinksw.com/schemas/cert#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix owl:  <http://www.w3.org/2002/07/owl#> .

 <%{prof_url}#identity>    cert:key <%{pubkey_url}#PublicKey> . 
 <%{pubkey_url}#PublicKey>    a cert:RSAPublicKey ; 
         cert:modulus "%{modulus}"^^xsd:hexBinary ; 
         cert:exponent "%{exponent}"^^xsd:int ; 
         owl:sameAs <%{fingerprint_ni}>, <%{fingerprint_di}> . 

 <%{cert_url}#cert>    a oplcert:Certificate ; 
          oplcert:hasPublicKey <%{pubkey_url}#PublicKey> .

