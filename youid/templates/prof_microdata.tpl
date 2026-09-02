<div>
  <div itemtype="http://www.w3.org/2000/01/rdf-schema#Resource" itemid="%{prof_url}#identity" itemscope>
    <div itemprop="http://www.w3.org/ns/auth/cert#key" itemtype="http://www.w3.org/ns/auth/cert#RSAPublicKey" itemid="%{pubkey_url}#PublicKey" itemscope>
      <meta itemprop="exponent" content="%{exponent}" />
      <meta itemprop="modulus" content="%{modulus}" />
      <link itemprop="http://schema.org/sameAs" href="%{fingerprint_ni}" />
      <link itemprop="http://schema.org/sameAs" href="%{fingerprint_di}" />
    </div>
  </div>

  <div itemtype="http://www.w3.org/2000/01/rdf-schema#Resource" itemid="%{card_ident_url}" itemscope>
    <div itemprop="http://www.w3.org/ns/auth/cert#key" itemtype="http://www.w3.org/ns/auth/cert#RSAPublicKey" itemid="%{pubkey_url}#PublicKey" itemscope>
    </div>
  </div>

  <div itemtype="http://www.w3.org/2000/01/rdf-schema#Resource" itemid="%{prof_url}#identity" itemscope>
    <link itemprop="http://www.openlinksw.com/schemas/cert#hasCertificate" href="%{cert_url}#cert" />
  </div>

  <div itemtype="http://www.openlinksw.com/schemas/cert#Certificate" itemid="%{cert_url}#cert" itemscope>
    <meta itemprop="subject" content="%{subject}" />
    <meta itemprop="issuer" content="%{issuer}" />
    <meta itemprop="notBefore" content="%{date_before}" />
    <meta itemprop="notAfter" content="%{date_after}" />
    <meta itemprop="serial" content="%{serial}" />
    <link itemprop="SAN" href="%{prof_url}#identity" />
!{ca_cert_url}    <link itemprop="http://www.openlinksw.com/schemas/cert#IAN" href="%{ca_cert_url}" />
    <link itemprop="hasPublicKey" href="%{pubkey_url}#PublicKey" />
    <meta itemprop="fingerprint" content="%{fingerprint_hex}" />
    <meta itemprop="fingerprint-digest" content="%{fingerprint_hex}" />
    <meta itemprop="fingerprint-digest" content="%{fingerprint_256_hex}" />
  </div>

!!{ca_cert_url}
  <div itemtype="http://www.w3.org/2000/01/rdf-schema#Resource" itemid="%{cert_url}#cert" itemscope>
    <link itemprop="http://www.w3.org/1999/xhtml/vocab#alternate" href="%{ca_cert_url}" />
  </div>
!!.

!!{pdp_url}
  <div itemtype="http://schema.org/Person" itemid="%{pdp_url}" itemscope>
    <link itemprop="http://schema.org/sameAs" href="%{prof_url}" />
    <link itemprop="http://www.openlinksw.com/schemas/cert#owns" href="%{cert_url}#cert" />
  </div>
!!.

  <div itemtype="http://schema.org/CreativeWork" itemid="%{card_url}"  itemscope>
    <link itemprop="http://schema.org/additionalType" href="http://schema.org/CreativeWork" />
    <link itemprop="http://schema.org/additionalType" href="http://www.openlinksw.com/schemas/cert#Certificate" />
    <link itemprop="http://schema.org/additionalType" href="http://schema.org/WebPage" />
    <link itemprop="http://schema.org/url" href="#this" />
    <meta itemprop="http://schema.org/name" content="%{subj_name}" />
    <link itemprop="http://schema.org/author" href="%{prof_url}#identity" />
    <link itemprop="http://schema.org/mainEntity" href="%{prof_url}#identity" />
    <link itemprop="http://www.openlinksw.com/schemas/cert#SAN" href="%{prof_url}#identity" />
    <link itemprop="http://www.openlinksw.com/schemas/cert#hasPublicKey" href="%{pubkey_url}#PublicKey" />
    <link itemprop="http://www.w3.org/ns/auth/cert#key" href="%{pubkey_url}#PublicKey" />
  </div>

  <div itemtype="http://www.w3.org/2000/01/rdf-schema#Resource" itemid="%{card_url}" itemscope>
    <link itemprop="http://schema.org/isRelatedTo" href="%{card_ident_url}" />
    <link itemprop="http://schema.org/isRelatedTo" href="%{jsonld_prof_url}#identity" />
    <link itemprop="http://schema.org/isRelatedTo" href="%{rdfa_prof_url}#identity" />
    <link itemprop="http://schema.org/isRelatedTo" href="%{prof_url}#identity" />
  </div>

  <div itemtype="http://www.w3.org/2000/01/rdf-schema#Resource" itemid="%{card_ident_url}" itemscope>
    <link itemprop="http://www.w3.org/2002/07/owl#sameAs" href="%{jsonld_prof_url}#identity" />
    <link itemprop="http://www.w3.org/2002/07/owl#sameAs" href="%{rdfa_prof_url}#identity" />
    <link itemprop="http://www.w3.org/2002/07/owl#sameAs" href="%{prof_url}#identity" />
  </div>

  <div itemtype="http://www.w3.org/2000/01/rdf-schema#Resource" itemid="%{prof_url}#identity" itemscope>
    <link itemprop="http://schema.org/isRelatedTo" href="%{cert_url}#cert" />
  </div>

  <div itemtype="http://schema.org/WebPage" itemid="%{card_url}" itemscope>
    <link itemprop="http://schema.org/mainEntity" href="%{card_ident_url}" />
  </div>

  <div itemtype="http://schema.org/Person" itemid="%{card_ident_url}" itemscope>
!{subj_email}    <meta itemprop="http://schema.org/email" content="%{subj_email}" />
!{subj_email}    <link itemprop="http://xmlns.com/foaf/0.1/mbox" href="mailto:%{subj_email}" />
    <div itemprop="http://schema.org/worksFor" itemtype="http://schema.org/Organization" itemscope>
      <meta itemprop="http://schema.org/name" content="%{subj_org}" />
    </div>
    <div itemprop="http://schema.org/address" itemtype="http://schema.org/Place" itemscope>
!{subj_country}      <meta itemprop="http://schema.org/addressCountry" content="%{subj_country}" />
!{subj_state}      <meta itemprop="http://schema.org/addressRegion" content="%{subj_state}" />
    </div>
    <meta itemprop="http://schema.org/name" content="%{subj_name}" />
!{pdp_url}    <link itemprop="http://www.w3.org/2002/07/owl#sameAs" href="%{pdp_url}#this" />
!{pdp_url}    <link itemprop="http://schema.org/sameAs" href="%{pdp_url}" />
!{pim_storage}    <link itemprop="http://www.w3.org/ns/pim/space#storage" href="%{pim_storage}" />
  </div>

  <div itemtype="http://schema.org/Person" itemid="%{prof_url}" itemscope>
    <link itemprop="http://schema.org/sameAs" href="%{card_url}" />
    <link itemprop="http://schema.org/sameAs" href="%{rdfa_prof_url}" />
    <link itemprop="http://schema.org/sameAs" href="%{jsonld_prof_url}" />
  </div>


!!{pdp_mail}
  <div itemtype="http://xmlns.com/foaf/0.1/Agent" itemid="%{prof_url}#identity" itemscope>
    <link itemprop="http://www.openlinksw.com/schemas/cert#owns" href="%{cert_url}#cert" />
    <meta itemprop="mbox_sha1sum" content="%{pdp_mail_sha1}" />
    <link itemprop="mbox" href="mailto:%{pdp_mail}" />
  </div>
!!.

  <div itemtype="http://xmlns.com/foaf/0.1/profileDocument" itemid="%{card_url}" itemscope>
    <link itemprop="http://schema.org/additionalType" href="http://www.openlinksw.com/schemas/cert#Certificate" />
    <meta itemprop="http://www.w3.org/2000/01/rdf-schema#label" content="Profile Document Subject:  %{subj_name}" />
    <link itemprop="primaryTopic" href="%{prof_url}#identity" />
    <link itemprop="http://www.openlinksw.com/schemas/cert#SAN" href="%{prof_url}#identity" />
    <link itemprop="http://www.openlinksw.com/schemas/cert#hasPublicKey" href="%{pubkey_url}#PublicKey" />
    <link itemprop="http://www.w3.org/ns/auth/cert#key" href="%{pubkey_url}#PublicKey" />
  </div>

  <div itemtype="http://www.w3.org/2000/01/rdf-schema#Resource" itemid="%{card_url}" itemscope>
    <link itemprop="http://www.w3.org/1999/xhtml/vocab#alternate" href="%{card_ident_url}" />
    <link itemprop="http://www.w3.org/1999/xhtml/vocab#alternate" href="%{rdfa_prof_url}#identity" />
    <link itemprop="http://www.w3.org/1999/xhtml/vocab#alternate" href="%{prof_url}#identity" />
    <link itemprop="http://www.w3.org/1999/xhtml/vocab#alternate" href="%{jsonld_prof_url}#identity" />
  </div>

  <div itemtype="http://www.w3.org/2000/01/rdf-schema#Resource" itemid="%{card_ident_url}" itemscope>
!{relList_micro} %{relList_micro}
    <link itemprop="http://www.w3.org/2002/07/owl#sameAs" href="%{jsonld_prof_url}#identity" />
    <link itemprop="http://www.w3.org/2002/07/owl#sameAs" href="%{rdfa_prof_url}#identity" />
    <link itemprop="http://www.w3.org/2002/07/owl#sameAs" href="%{prof_url}#identity" />
  </div>

  <div itemtype="http://www.w3.org/2000/01/rdf-schema#Resource" itemid="%{card_ident_url}" itemscope>
!{relList_micro_schema} %{relList_micro_schema}
    <link itemprop="http://schema.org/sameAs" href="%{jsonld_prof_url}" />
    <link itemprop="http://schema.org/sameAs" href="%{rdfa_prof_url}" />
    <link itemprop="http://schema.org/sameAs" href="%{prof_url}" />
  </div>

  <div itemtype="http://www.w3.org/2000/01/rdf-schema#Resource" itemid="%{prof_url}#identity" itemscope>
    <link itemprop="http://www.w3.org/1999/xhtml/vocab#alt" href="%{cert_url}#cert" />
  </div>

</div>
