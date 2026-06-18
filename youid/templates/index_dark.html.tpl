<!DOCTYPE html>
<html lang="en" prefix="
  foaf: http://xmlns.com/foaf/0.1/
  schema: http://schema.org/
  cert: http://www.w3.org/ns/auth/cert#
  oplcert: http://www.openlinksw.com/schemas/cert#
  xhv: http://www.w3.org/1999/xhtml/vocab#
  prov: http://www.w3.org/ns/prov#
  rdfs: http://www.w3.org/2000/01/rdf-schema#
  xsd: http://www.w3.org/2001/XMLSchema#
  owl: http://www.w3.org/2002/07/owl#
  pim: http://www.w3.org/ns/pim/space#
  dct: http://purl.org/dc/terms/
">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>%{subj_name} — Web‑Scale Digital Identity</title>

<!-- Semantic Link Relations -->
<link rel="describes" href="%{card_ident_url}" title="Describes" />
<link rev="describedby" href="%{card_ident_url}" title="Described By" />
<link rel="related" href="%{cert_url}" title="X.509 Certificate (Turtle)" type="text/turtle" />
<link rel="related" href="%{prof_url}" title="FOAF Profile (Turtle)" type="text/turtle" />
<link rel="related" href="%{jsonld_prof_url}" title="Profile (JSON-LD)" type="application/ld+json" />
<link rel="related" href="%{pubkey_url}" title="Public Key (Turtle)" type="text/turtle" />
<link rel="http://xmlns.com/foaf/0.1/primaryTopic" href="%{card_ident_url}" title="This Document's Primary Topic" />
<link rel="http://www.w3.org/ns/auth/cert#key" href="%{pubkey_url}#PublicKey" title="RSA Public Key" />
%{rel_header_html}
!!{em_indie_idp}
<link rel="indieauth-metadata" href="%{em_indie_idp}/indieauth/indieauth_metadata">
<link rel="authorization_endpoint" href="%{em_indie_idp}/indieauth/indieauth_authorize">
<link rel="token_endpoint" href="%{em_indie_idp}/indieauth/indieauth_token">
!!.
<link rel="alternate" href="%{prof_url}" title="FOAF Profile (Turtle)" type="text/turtle" />
<link rel="alternate" href="%{jsonld_prof_url}" title="Profile (JSON-LD)" type="application/ld+json" />
<link rel="alternate" href="%{pubkey_pem_url}" title="Certificate (PEM)" type="application/x-x509-ca-cert" />
<link rel="alternate" href="%{vcard_url}" title="vCard" type="text/vcard" />

<!-- Fonts -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">

<script src="./qrcode.js"></script>

<style>
  /* ── Reset & Variables ── */
  *, *::before, *::after { box-sizing:border-box; margin:0; padding:0 }
  :root {
    --bg: #0f0f1a;
    --surface: #1a1a2e;
    --surface-soft: #22223a;
    --text: #e8e8f0;
    --text-secondary: #a8a8c0;
    --text-muted: #6868a0;
    --border: #2a2a3e;
    --accent: #5b7fff;
    --accent-light: #7a94ff;
    --accent-glow: rgba(91,127,255,0.15);
    --success: #34d399;
    --warning: #fbbf24;
    --radius: 14px;
    --radius-sm: 10px;
    --shadow: 0 4px 20px rgba(0,0,0,0.3);
    --shadow-md: 0 8px 30px rgba(0,0,0,0.4);
    --font: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    --font-mono: 'JetBrains Mono', 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
    --max-width: 780px;
  }

  body {
    font-family: var(--font);
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    min-height: 100vh;
    padding: 0;
  }

  .container {
    max-width: var(--max-width);
    margin: 0 auto;
    padding: 20px 16px 40px;
  }
  @media (min-width:640px) { .container { padding: 32px 24px 48px; } }

  /* ── Dark Hero ── */
  .hero {
    text-align: center;
    padding: 48px 24px 36px;
    margin-bottom: 20px;
    position: relative;
  }
  .hero-photo {
    width: 140px; height: 140px;
    border-radius: 50%;
    object-fit: cover;
    border: 3px solid var(--accent);
    box-shadow: 0 0 30px var(--accent-glow);
    margin-bottom: 20px;
  }
  .hero-name {
    font-size: 1.9rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #fff;
    line-height: 1.2;
    margin-bottom: 4px;
  }
  .hero-name a {
    color: inherit;
    text-decoration: none;
  }
  .hero-name a:hover {
    text-decoration: underline;
  }
  .hero-title {
    font-size: 1rem;
    color: var(--text-secondary);
    font-weight: 400;
    margin-bottom: 8px;
  }
  .hero-meta {
    display: flex;
    justify-content: center;
    gap: 10px;
    flex-wrap: wrap;
    font-size: 0.82rem;
    color: var(--text-muted);
    margin-bottom: 16px;
  }
  .hero-meta-item {
    display: inline-flex;
    align-items: center;
    gap: 5px;
  }

  /* ── Dark Badges ── */
  .badge-row {
    display: flex;
    justify-content: center;
    gap: 10px;
    flex-wrap: wrap;
  }
  .badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 0.82rem;
    font-weight: 500;
  }
  .badge-metric {
    background: var(--surface-soft);
    color: var(--accent);
    border: 1px solid rgba(91,127,255,0.3);
  }
  .badge-webid {
    background: rgba(91,127,255,0.15);
    color: var(--accent-light);
    border: 1px solid rgba(91,127,255,0.2);
  }

  /* ── Bio Section ── */
  .bio-section {
    background: var(--surface);
    border-radius: var(--radius);
    padding: 24px 28px;
    margin-bottom: 16px;
    border: 1px solid var(--border);
  }
  .bio-text {
    font-size: 0.92rem;
    color: var(--text);
    line-height: 1.7;
  }

  /* ── Question Chips ── */
  .chips-section {
    margin-bottom: 16px;
  }
  .chips-label {
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-muted);
    margin-bottom: 10px;
  }
  .chips-scroll {
    display: flex;
    gap: 8px;
    overflow-x: auto;
    padding-bottom: 6px;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: thin;
    scrollbar-color: var(--border) transparent;
  }
  .chips-scroll::-webkit-scrollbar { height: 4px; }
  .chips-scroll::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
  .chip {
    flex-shrink: 0;
    padding: 8px 16px;
    border-radius: 20px;
    font-size: 0.82rem;
    color: var(--accent-light);
    background: var(--surface);
    border: 1px solid var(--border);
    cursor: default;
    white-space: nowrap;
    transition: all 0.15s;
  }
  .chip:hover {
    border-color: var(--accent);
    background: var(--accent-glow);
  }

  /* ── Card ── */
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    margin-bottom: 16px;
    overflow: hidden;
  }
  .card-header {
    padding: 16px 24px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 600;
    font-size: 0.92rem;
    color: var(--text);
  }
  .card-header svg {
    width: 18px; height: 18px;
    flex-shrink: 0;
    opacity: 0.7;
    color: var(--accent);
  }
  .card-body {
    padding: 20px 24px;
  }
  .card-body:last-child { padding-bottom: 20px; }

  /* ── Detail Grid ── */
  .detail-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 12px;
  }
  @media (min-width:560px) {
    .detail-grid { grid-template-columns: 1fr 1fr; }
    .detail-grid .span-2 { grid-column: 1 / -1; }
  }
  .detail-item {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .detail-label {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
  }
  .detail-value {
    font-size: 0.9rem;
    color: var(--text);
    word-break: break-all;
  }
  .detail-value.mono {
    font-family: var(--font-mono);
    font-size: 0.78rem;
    letter-spacing: -0.01em;
  }
  .detail-value a {
    color: var(--accent);
    text-decoration: none;
  }
  .detail-value a:hover { text-decoration: underline; }

  .tag {
    display: inline-block;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 4px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  .tag-valid { background:rgba(5,150,105,0.2); color:#34d399; }
  .tag-warning { background:rgba(217,119,6,0.2); color:#fbbf24; }

  .fingerprint-box {
    background: var(--surface-soft);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 12px 16px;
    font-family: var(--font-mono);
    font-size: 0.75rem;
    line-height: 1.7;
    word-break: break-all;
    color: var(--text-secondary);
    position: relative;
  }
  .fingerprint-box .fp-label {
    font-family: var(--font);
    font-size: 0.68rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--text-muted);
    display: block;
    margin-bottom: 4px;
  }

  /* ── Accordion ── */
  details.card-body {
    padding: 0;
    border: none;
  }
  details.card-body > summary {
    padding: 16px 24px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    list-style: none;
    user-select: none;
    font-size: 0.88rem;
    color: var(--text-secondary);
  }
  details.card-body > summary::-webkit-details-marker { display: none; }
  details.card-body > summary::after {
    content: '';
    width: 10px; height: 10px;
    border-right: 2px solid var(--text-muted);
    border-bottom: 2px solid var(--text-muted);
    transform: rotate(45deg);
    transition: transform 0.2s;
    flex-shrink: 0;
    margin-left: auto;
  }
  details.card-body[open] > summary::after {
    transform: rotate(-135deg);
  }
  details.card-body > summary:hover {
    background: var(--surface-soft);
  }
  details.card-body > .accordion-content {
    padding: 0 24px 20px;
  }
  details.card-body > summary .summary-preview {
    font-size: 0.82rem;
    color: var(--text-muted);
    font-weight: 400;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex: 1;
    min-width: 0;
    text-align: right;
  }
  @media (max-width:480px) {
    details.card-body > summary { padding: 12px 16px; }
    details.card-body > .accordion-content { padding: 0 16px 16px; }
  }

  /* ── Nested Accordion ── */
  .nested-details {
    margin-top: 16px;
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    background: var(--surface-soft);
    overflow: hidden;
  }
  .nested-details > summary {
    padding: 10px 14px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    list-style: none;
    user-select: none;
    font-size: 0.85rem;
    color: var(--text-secondary);
  }
  .nested-details > summary::-webkit-details-marker { display: none; }
  .nested-details > summary::after {
    content: '';
    width: 8px; height: 8px;
    border-right: 2px solid var(--text-muted);
    border-bottom: 2px solid var(--text-muted);
    transform: rotate(45deg);
    transition: transform 0.2s;
    flex-shrink: 0;
  }
  .nested-details[open] > summary::after {
    transform: rotate(-135deg);
  }
  .nested-details > summary:hover {
    background: var(--border);
  }
  .nested-details > .nested-content {
    padding: 0 14px 14px;
  }
  .nested-details > summary .summary-preview {
    font-size: 0.78rem;
    color: var(--text-muted);
    font-weight: 400;
  }

  /* ── Social Row ── */
  .social-section {
    background: var(--surface);
    border-radius: var(--radius);
    padding: 24px 24px 28px;
    margin-bottom: 16px;
    border: 1px solid var(--border);
    text-align: center;
  }
  .social-heading {
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-muted);
    margin-bottom: 14px;
  }
  .social-row {
    display: flex;
    justify-content: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  /* ── Dual CTA ── */
  .dual-cta {
    display: flex;
    gap: 12px;
    justify-content: center;
    flex-wrap: wrap;
    margin-bottom: 20px;
  }
  .cta-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 12px 28px;
    border-radius: var(--radius-sm);
    font-size: 0.92rem;
    font-weight: 600;
    text-decoration: none;
    cursor: pointer;
    border: none;
    transition: all 0.15s;
  }
  .cta-btn svg { width: 18px; height: 18px; }
  .cta-chat {
    background: var(--accent);
    color: #fff;
  }
  .cta-chat:hover {
    background: var(--accent-light);
    box-shadow: 0 0 20px var(--accent-glow);
  }
  .cta-verify {
    background: transparent;
    color: var(--accent);
    border: 1px solid var(--accent);
  }
  .cta-verify:hover {
    background: var(--accent-glow);
  }

  /* ── Footer ── */
  .footer {
    text-align: center;
    padding: 16px 0 8px;
    border-top: 1px solid var(--border);
    margin-top: 8px;
  }
  .footer p {
    font-size: 0.75rem;
    color: var(--text-muted);
    line-height: 1.7;
  }
  .footer a { color: var(--accent); text-decoration: none; }
  .footer a:hover { text-decoration: underline; }

  /* ── QR ── */
  .qr-container img { width: 80px; height: 80px; }

  /* ── Responsive ── */
  @media (max-width:480px) {
    .hero { padding: 32px 16px 24px; }
    .hero-photo { width: 100px; height: 100px; }
    .hero-name { font-size: 1.4rem; }
    .bio-section { padding: 18px 16px; }
    .card-header { padding: 12px 16px; }
    .card-body { padding: 14px 16px; }
    .social-section { padding: 16px; }
    .cta-btn { padding: 10px 20px; font-size: 0.85rem; }
  }
</style>
</head>
<body>

<div class="container">

  <!-- ═══ HERO ═══ -->
  <header class="hero" typeof="foaf:Person" resource="%{card_ident_url}">
    <link property="cert:key" href="%{pubkey_url}#PublicKey" />
    <img src="%{photo_url}" alt="%{subj_name}" class="hero-photo" property="foaf:img" />
    <h1 class="hero-name"><a href="%{webid}" property="foaf:name schema:name">%{subj_name}</a></h1>
    <p class="hero-title" property="foaf:title">%{subj_title}</p>
    <div class="hero-meta">
      <span class="hero-meta-item" property="foaf:mbox" resource="mailto:%{subj_email}">%{subj_email}</span>
      <span class="hero-meta-item" property="foaf:org" resource="%{subj_org}">%{subj_org}</span>
      <span class="hero-meta-item">%{subj_country}%{subj_state}</span>
    </div>
    <div class="badge-row">
      <span class="badge badge-metric">&#9679; Verified WebID</span>
      <span class="badge badge-webid">&#10003; &#109; Active</span>
    </div>
  </header>

  <!-- ═══ QR (hidden container for script) ═══ -->
  <div class="qr-container" style="display:none"></div>

  <!-- ═══ BIO ═══ -->
  !!{subj_summary}
  <div class="bio-section">
    <p class="bio-text">%{subj_summary}</p>
  </div>
  !!.

  <!-- ═══ SUGGESTED QUESTIONS ═══ -->
  <div class="chips-section">
    <div class="chips-label">Ask about this identity</div>
    <div class="chips-scroll">
      <span class="chip">How do I verify this identity?</span>
      <span class="chip">What are the certificate details?</span>
      <span class="chip">Check my public key fingerprint</span>
      <span class="chip">Query this WebID on the Knowledge Graph</span>
    </div>
  </div>

  <!-- ═══ CERTIFICATE ═══ -->
  <section class="card" typeof="oplcert:Certificate" resource="%{card_url}#cert">
    <div class="card-header">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
      X.509 Certificate
      <span style="margin-left:auto;display:flex;gap:6px;flex-wrap:wrap">
        <span class="tag tag-valid">&#10003; Active</span>
        <span class="tag tag-valid">RSA 2048</span>
      </span>
    </div>
    <details class="card-body">
      <summary>
        <span>Subject: <strong>%{subj_name}</strong></span>
        <span class="summary-preview">%{date_before}–%{date_after} &#183; Self&#8209;Signed</span>
      </summary>
      <div class="accordion-content">
        <div class="detail-grid">
          <div class="detail-item span-2">
            <span class="detail-label">Subject</span>
            <span class="detail-value mono" property="oplcert:subject">%{subject}</span>
          </div>
          <div class="detail-item span-2">
            <span class="detail-label">Issuer</span>
            <span class="detail-value mono" property="oplcert:issuer">%{issuer}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Serial</span>
            <span class="detail-value mono" property="oplcert:serial">%{serial}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Signature Algorithm</span>
            <span class="detail-value mono">sha256WithRSAEncryption</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Issued</span>
            <span class="detail-value" property="oplcert:notBefore" datatype="xsd:dateTime">%{date_before}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Expires</span>
            <span class="detail-value" property="oplcert:notAfter" datatype="xsd:dateTime">%{date_after}</span>
          </div>
          <div class="detail-item span-2">
            <span class="detail-label">WebID (Subject Alternative Name)</span>
            <span class="detail-value mono"><a href="%{webid}" property="oplcert:SAN">%{webid}</a></span>
          </div>
        </div>

        <!-- ═══ NESTED: PUBLIC KEY ACCORDION ═══ -->
        <details class="nested-details" typeof="cert:RSAPublicKey" resource="%{pubkey_url}#PublicKey">
          <summary>
            <span style="display:flex;align-items:center;gap:8px">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px;flex-shrink:0" stroke-linecap="round" stroke-linejoin="round"><path d="M15 7a4 4 0 11-8 0 4 4 0 018 0z"/><path d="M21 17a2 2 0 01-2 2H5a2 2 0 01-2-2v-2a2 2 0 012-2h14a2 2 0 012 2v2z"/></svg>
              RSA Public Key &#8212; <strong>%{exponent}</strong> &#183; 2048 bit
            </span>
            <span class="summary-preview">modulus + fingerprints</span>
          </summary>
          <div class="nested-content">
            <div class="detail-grid" style="margin-top:12px">
              <div class="detail-item">
                <span class="detail-label">Exponent</span>
                <span class="detail-value mono" property="cert:exponent" datatype="xsd:int">%{exponent}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Key Size</span>
                <span class="detail-value mono">2048 bits</span>
              </div>
              <div class="detail-item span-2">
                <span class="detail-label">Modulus</span>
                <span class="detail-value mono" property="cert:modulus" datatype="xsd:hexBinary" style="font-size:0.65rem;line-height:1.6">%{modulus}</span>
              </div>
            </div>

            <div style="margin-top:16px">
              <div style="font-size:0.72rem;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:var(--text-muted);margin-bottom:8px">Fingerprints</div>
              <div class="fingerprint-box">
                <span class="fp-label">SHA-1</span>
                %{fingerprint_hex}
              </div>
              <div class="fingerprint-box" style="margin-top:6px">
                <span class="fp-label">SHA-256</span>
                %{fingerprint_256_hex}
              </div>
              <div class="fingerprint-box" style="margin-top:6px">
                <span class="fp-label">Nice IRI</span>
                %{fingerprint_ni}
              </div>
              <div class="fingerprint-box" style="margin-top:6px">
                <span class="fp-label">Digest IRI</span>
                %{fingerprint_di}
              </div>
            </div>
          </div>
        </details>

      </div>
    </details>
  </section>

  <!-- ═══ SOCIAL PROFILES ═══ -->
  <div class="social-section">
    <div class="social-heading">Follow for more</div>
    <div class="social-row">
!{relList_html}%{relList_html}
    </div>
  </div>

  <style>
    .social-row a {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 38px; height: 38px;
      border-radius: 50%;
      text-decoration: none;
      border: 1px solid var(--border);
      transition: all 0.15s;
      position: relative;
      background: var(--pbg, var(--surface-soft));
      border-color: var(--pcolor, var(--border));
    }
    .social-row a:hover {
      transform: translateY(-2px);
      box-shadow: 0 0 14px var(--pcolor, var(--accent));
      border-color: var(--pcolor, var(--accent));
    }
    .social-row a::after {
      content: attr(title);
      position: absolute;
      bottom: -24px;
      left: 50%;
      transform: translateX(-50%);
      font-size: 0.68rem;
      color: var(--text-muted);
      white-space: nowrap;
      opacity: 0;
      transition: opacity 0.15s;
      pointer-events: none;
      font-weight: 500;
    }
    .social-row a:hover::after { opacity: 1; }
    .social-row img {
      width: 22px; height: 22px;
      border-radius: 3px;
    }
    .social-row a[title*="LinkedIn"] { --pcolor: #0a66c2; --pbg: rgba(10,102,194,0.15); }
    .social-row a[title*="Mastodon"] { --pcolor: #6364ff; --pbg: rgba(99,100,255,0.15); }
    .social-row a[title*="Bluesky"] { --pcolor: #0085ff; --pbg: rgba(0,133,255,0.15); }
    .social-row a[title*="GitHub"] { --pcolor: #8b949e; --pbg: rgba(139,148,158,0.12); }
    .social-row a[title*="Facebook"] { --pcolor: #1877f2; --pbg: rgba(24,119,242,0.15); }
    .social-row a[title*="Instagram"] { --pcolor: #e4405f; --pbg: rgba(228,64,95,0.15); }
    .social-row a[title*="Linktree"] { --pcolor: #39e09b; --pbg: rgba(57,224,155,0.15); }
    .social-row a[title*="RSS"] { --pcolor: #f26522; --pbg: rgba(242,101,34,0.15); }
  </style>

  <!-- ═══ DUAL CTA ═══ -->
  <div class="dual-cta">
    <button class="cta-btn cta-chat open-button" onclick="window.location.href='#opal-section'">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
      OPAL AI Chat
    </button>
    <a href="%{prof_url}" class="cta-btn cta-verify" download>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
      Verify Identity
    </a>
  </div>

  <!-- ═══ DOWNLOADS ═══ -->
  <div class="dual-cta" style="margin-bottom:16px;gap:8px">
    <a href="%{vcard_url}" class="btn" download style="display:inline-flex;align-items:center;gap:6px;padding:8px 18px;border-radius:var(--radius-sm);font-size:0.85rem;font-weight:500;text-decoration:none;background:var(--surface);color:var(--text);border:1px solid var(--border);transition:all 0.15s">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
      vCard (.vcf)
    </a>
    <a href="%{pubkey_pem_url}" class="btn" download style="display:inline-flex;align-items:center;gap:6px;padding:8px 18px;border-radius:var(--radius-sm);font-size:0.85rem;font-weight:500;text-decoration:none;background:var(--surface);color:var(--text);border:1px solid var(--border);transition:all 0.15s">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
      Cert (.pem)
    </a>
    <a href="%{pubkey_der_url}" class="btn" download style="display:inline-flex;align-items:center;gap:6px;padding:8px 18px;border-radius:var(--radius-sm);font-size:0.85rem;font-weight:500;text-decoration:none;background:var(--surface);color:var(--text);border:1px solid var(--border);transition:all 0.15s">
      Cert (.crt)
    </a>
    <a href="%{jsonld_prof_url}" class="btn" download style="display:inline-flex;align-items:center;gap:6px;padding:8px 18px;border-radius:var(--radius-sm);font-size:0.85rem;font-weight:500;text-decoration:none;background:var(--surface);color:var(--text);border:1px solid var(--border);transition:all 0.15s">
      Profile (JSON-LD)
    </a>
  </div>

  <!-- ═══ OPAL AI AGENT ═══ -->
  !!{use_opal_widget}
  <section class="card" id="opal-section">
    <div class="card-header">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
      AI Agent &#8212; OPAL
    </div>
    <div class="card-body">
      <p style="font-size:0.88rem;color:var(--text-secondary);margin-bottom:12px">
        Ask questions about this identity, the certificate, or explore the knowledge graph.
      </p>
      <div class="btn-group">
        <button class="btn btn-primary open-button" onclick="document.getElementById('opal-form').style.display='block'" style="background:var(--accent);border-color:var(--accent);color:#fff;display:inline-flex;align-items:center;gap:6px;padding:8px 18px;border-radius:var(--radius-sm);font-size:0.85rem;font-weight:500;cursor:pointer;border:none;transition:all 0.15s">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
          Open Chat
        </button>
      </div>
    </div>
  </section>
  !!.

  <!-- ═══ FOOTER ═══ -->
  <footer class="footer">
    <p>
      Web&#8209;Scale Verifiable Digital Identity for <a href="%{webid}">%{subj_name}</a><br />
      Generated using <a href="https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/youid">youid</a>.
      <a href="%{prof_url}">Turtle</a> &#183;
      <a href="%{jsonld_prof_url}">JSON-LD</a> &#183;
      <a href="%{vcard_url}">vCard</a>
    </p>
    <p style="margin-top:4px">
      Linked Data resolved via <a href="https://linkeddata.uriburner.com/">URIBurner</a>
      (<a href="https://virtuoso.openlinksw.com/">Virtuoso</a>-backed).
    </p>
  </footer>

</div>

<!-- ═══ Embedded JSON-LD ═══ -->
!!{em_jsonld}
<script type="application/ld+json">
%{json_ld}
</script>
!!.

<!-- ═══ Embedded Turtle (for RDF-aware browsers) ═══ -->
!!{em_ttl}
<script type="text/turtle">
%{profile_ttl}
</script>
!!.

<!-- ═══ QR Code Generator ═══ -->
<script>
document.addEventListener('DOMContentLoaded', function() {
  var el = document.querySelector('.qr-container');
  if (el && typeof qrcode !== 'undefined') {
    var errorCorrectionLevel = 'M';
    var typeNumber = 10;
    qrcode.stringToBytes = qrcode.stringToBytesFuncs['default'];
    var qr = qrcode(typeNumber, errorCorrectionLevel);
    qr.addData(location.href, 'Byte');
    qr.make();
    el.innerHTML = qr.createImgTag(2, 2, 'QR code');
    el.style.display = '';
  }
});
</script>

<!-- ═══ Semantic Web Helper Scripts ═══ -->
!!{use_opal}
<script src="./opal.js"></script>
<script src="./opalx.js"></script>
!!.
<script>
function toggleOpal() {
  var form = document.getElementById('opal-form');
  if (form) form.style.display = form.style.display === 'none' ? 'block' : 'none';
}
</script>

<!-- ═══ Hidden RDFa annotations ═══ -->
!!{em_rdfa}
%{rdfa}
!!.
</body>
</html>
