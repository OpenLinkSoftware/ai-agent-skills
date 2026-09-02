BEGIN:VCARD
VERSION:3.0
N: %{subj_name};;;;
FN: %{subj_name}
ORG:%{subj_org}
ADR;TYPE=work:;;;;%{subj_state};;%{subj_country}
EMAIL;type=INTERNET;type=WORK;type=pref:%{subj_email}
URL:%{pdp_url}
item1.URL;type=pref:data:text/plain:%{fingerprint_colon}
item1.X-ABLabel:Fingerprint
item2.URL;type=pref:%{vcard_digest_uri} 
item2.X-ABLabel:Digest URI
item3.URL:%{pubkey_pem_url}
item3.X-ABLabel:Certificate URL
item4.URL:%{webid}
item4.X-ABLabel:NetID
PHOTO;ENCODING=b;TYPE=JPEG:%{photo_base64}
END:VCARD
