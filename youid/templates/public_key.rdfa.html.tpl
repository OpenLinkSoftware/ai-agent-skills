<!doctype html>
<html>
<head>
<meta charset="UTF-8">
<title>Public Key RDFa for %{subj_name}</title>

</head>
<body>

<div xmlns="http://www.w3.org/1999/xhtml"
  prefix="
    owl: http://www.w3.org/2002/07/owl#
    cert: http://www.w3.org/ns/auth/cert#
    rdf: http://www.w3.org/1999/02/22-rdf-syntax-ns#
    oplcert: http://www.openlinksw.com/schemas/cert#
    xsd: http://www.w3.org/2001/XMLSchema#
    rdfs: http://www.w3.org/2000/01/rdf-schema#"
  >
  <div typeof="oplcert:Certificate" about="%{rdfa_cert_url}#cert">
    <div rel="oplcert:hasPublicKey">
      <div typeof="cert:RSAPublicKey" about="%{rdfa_pubkey_url}#PublicKey">
        <div property="cert:modulus" datatype="xsd:hexBinary" content="%{modulus}"></div>
        <div property="cert:exponent" datatype="xsd:int" content="%{exponent}"></div>
        <div rel="owl:sameAs" resource="%{fingerprint_ni}"></div>
        <div rel="owl:sameAs" resource="%{fingerprint_di}"></div>
      </div>
    </div>
  </div>
  <div typeof="rdfs:Resource" about="%{rdfa_prof_url}#identity">
    <div rel="cert:key" resource="%{rdfa_pubkey_url}#PublicKey"></div>
  </div>
</div>

</body>
</html>
