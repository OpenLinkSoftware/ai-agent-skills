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
    --bg: #f4f6f9;
    --surface: #ffffff;
    --surface-soft: #f8f9fb;
    --text: #1a1d23;
    --text-secondary: #5e6674;
    --text-muted: #8b95a6;
    --border: #e2e6ed;
    --accent: #1e3a5f;
    --accent-light: #2a4a7a;
    --gold: #c8a45c;
    --gold-light: #d4b87a;
    --success: #059669;
    --warning: #d97706;
    --radius: 12px;
    --radius-sm: 8px;
    --shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
    --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -1px rgba(0,0,0,0.04);
    --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -2px rgba(0,0,0,0.04);
    --font: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    --font-mono: 'JetBrains Mono', 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
    --max-width: 820px;
  }
  @media (prefers-color-scheme:dark) {
    :root {
      --bg: #0f1117;
      --surface: #1a1d27;
      --surface-soft: #222531;
      --text: #e8eaed;
      --text-secondary: #9aa0b0;
      --text-muted: #6b7280;
      --border: #2d3140;
      --shadow: 0 1px 3px rgba(0,0,0,0.3), 0 1px 2px rgba(0,0,0,0.2);
      --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.4), 0 2px 4px -1px rgba(0,0,0,0.3);
      --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.5), 0 4px 6px -2px rgba(0,0,0,0.3);
    }
  }

  body {
    font-family: var(--font);
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    min-height: 100vh;
    padding: 24px 16px;
  }
  @media (min-width:640px) { body { padding: 40px 24px; } }

  .container {
    max-width: var(--max-width);
    margin: 0 auto;
  }

  /* ── Premium Hero ── */
  .hero {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 36px 32px;
    margin-bottom: 24px;
    display: flex;
    align-items: flex-start;
    gap: 28px;
    flex-wrap: wrap;
    color: var(--text);
    box-shadow: var(--shadow);
  }
  .hero-photo {
    width: 120px; height: 120px;
    border-radius: 50%;
    object-fit: cover;
    border: 3px solid var(--gold);
    flex-shrink: 0;
  }
  .hero-body { flex:1; min-width:240px; }
  .hero-name {
    font-size: 1.8rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--accent);
    line-height: 1.2;
    margin-bottom: 2px;
    display: inline-block;
    border-bottom: 3px solid var(--gold);
    padding-bottom: 4px;
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
    margin-top: 10px;
  }
  .hero-meta {
    display: flex;
    gap: 10px;
    margin-top: 8px;
    flex-wrap: wrap;
    font-size: 0.82rem;
  }
  .hero-meta-item {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    color: var(--text-muted);
  }

  /* ── Credential Badge Bar ── */
  .badge-bar {
    display: flex;
    gap: 10px;
    margin-top: 12px;
    flex-wrap: wrap;
  }
  .badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 0.82rem;
    font-weight: 500;
  }
  .badge-active {
    background: linear-gradient(135deg, #c8a45c, #d4b87a);
    color: #1a1d23;
  }
  .badge-webid {
    background: var(--accent);
    color: #fff;
  }
  .badge-webid-dark {
    background: #2a4a7a;
    color: #fff;
  }

  /* ── Cards ── */
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
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
    color: var(--accent);
    border-left: 4px solid var(--gold);
    margin-left: 0;
  }
  .card-header svg {
    width: 18px; height: 18px;
    flex-shrink: 0;
    opacity: 0.8;
    color: var(--gold);
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
    color: var(--accent-light);
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
  .tag-valid { background:#d1fae5; color:#065f46; }
  .tag-warning { background:#fef3c7; color:#92400e; }
  @media (prefers-color-scheme:dark) {
    .tag-valid { background:rgba(5,150,105,0.2); color:#34d399; }
    .tag-warning { background:rgba(217,119,6,0.2); color:#fbbf24; }
  }

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

  /* ── Social Grid ── */
  .social-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
  .social-grid a {
    display: inline-block;
    line-height: 0;
    border-radius: 8px;
    transition: box-shadow 0.15s;
  }
  .social-grid a:hover {
    box-shadow: 0 0 0 2px var(--accent);
  }
  .social-grid img {
    width: 32px;
    height: 32px;
    border-radius: 6px;
    display: block;
  }

  /* ── Attribution Row ── */
  .attribution-row {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    flex-wrap: wrap;
    padding: 12px 0;
    margin-top: 8px;
    color: var(--text-muted);
    font-size: 0.78rem;
  }
  .attribution-row a {
    color: var(--accent-light);
    text-decoration: none;
  }
  .attribution-row a:hover { text-decoration: underline; }
  .attr-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 10px;
    border: 1px solid var(--border);
    border-radius: 20px;
    font-size: 0.75rem;
    background: var(--surface-soft);
  }

  /* ── Buttons ── */
  .btn-group {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
  .btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 18px;
    border-radius: var(--radius-sm);
    font-size: 0.85rem;
    font-weight: 500;
    text-decoration: none;
    cursor: pointer;
    border: 1px solid var(--border);
    background: var(--surface);
    color: var(--text);
    transition: all 0.15s;
  }
  .btn:hover {
    border-color: var(--accent-light);
    background: var(--surface-soft);
  }
  .btn-primary {
    background: var(--accent);
    border-color: var(--accent);
    color: white;
  }
  .btn-primary:hover {
    background: var(--accent-light);
    border-color: var(--accent-light);
  }
  .btn svg { width: 16px; height: 16px; opacity: 0.8; }

  /* ── Footer ── */
  .footer {
    text-align: center;
    padding: 20px 0 8px;
    border-top: 1px solid var(--border);
    margin-top: 24px;
  }
  .footer-links {
    display: flex;
    justify-content: center;
    gap: 16px;
    flex-wrap: wrap;
    font-size: 0.78rem;
  }
  .footer-links a {
    color: var(--text-muted);
    text-decoration: none;
  }
  .footer-links a:hover {
    color: var(--accent-light);
    text-decoration: underline;
  }
  .footer-copy {
    font-size: 0.72rem;
    color: var(--text-muted);
    margin-top: 8px;
  }
  .footer-copy a { color: var(--accent-light); text-decoration: none; }
  .footer-copy a:hover { text-decoration: underline; }

  /* ── QR fallback ── */
  .cardQr img { width: 80px; height: 80px; }

  /* ── Responsive ── */
  @media (max-width:480px) {
    .hero { padding: 24px 20px; gap: 16px; }
    .hero-photo { width: 80px; height: 80px; }
    .hero-name { font-size: 1.35rem; }
    .social-grid { grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); }
    .card-header { padding: 12px 16px; }
    .card-body { padding: 16px; }
  }
</style>
</head>
<body>

<div class="container">

  <!-- ═══ HERO ═══ -->
  <header class="hero" typeof="foaf:Person" resource="%{card_ident_url}">
    <link property="cert:key" href="%{pubkey_url}#PublicKey" />
    <img src="%{photo_url}" alt="%{subj_name}" class="hero-photo" property="foaf:img" />
    <div class="hero-body">
      <h1 class="hero-name"><a href="%{webid}" property="foaf:name schema:name">%{subj_name}</a></h1>
      <p class="hero-title" property="foaf:title">%{subj_title}</p>
      <div class="hero-meta">
        <span class="hero-meta-item" property="foaf:mbox" resource="mailto:%{subj_email}">%{subj_email}</span>
        <span class="hero-meta-item" property="foaf:org" resource="%{subj_org}">%{subj_org}</span>
        <span class="hero-meta-item">%{subj_country}%{subj_state}</span>
      </div>
      <div class="badge-bar">
        <span class="badge badge-active">&#10003; Active</span>
        <span class="badge badge-webid">&#10003; Verified WebID</span>
      </div>
    </div>
    <div class="qr-container cardQr">
      <canvas></canvas>
    </div>
  </header>

  <style>
    .qr-container {
      width: 88px; height: 88px;
      background: var(--surface-soft);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .qr-container canvas, .qr-container img {
      width: 80px; height: 80px;
      border-radius: 4px;
    }
  </style>

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
  <section class="card">
    <div class="card-header">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 2h-3a5 5 0 00-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 011-1h3z"/></svg>
      Connected Profiles
    </div>
    <div class="card-body">
      <div class="social-grid">
!{relList_html}%{relList_html}
      </div>
    </div>
  </section>

  <!-- ═══ ATTRIBUTION ROW ═══ -->
  <div class="attribution-row">
    <span class="attr-badge">Linked Data via <a href="https://linkeddata.uriburner.com/" target="_blank" rel="noopener noreferrer">URIBurner</a></span>
    <span class="attr-badge"><a href="https://virtuoso.openlinksw.com/" target="_blank" rel="noopener noreferrer">Virtuoso</a>-backed</span>
  </div>

  <!-- ═══ DOWNLOADS ═══ -->
  <section class="card">
    <div class="card-header">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
      Downloads &amp; Resources
    </div>
    <div class="card-body">
      <div class="btn-group">
        <a href="%{vcard_url}" class="btn btn-primary" download>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          vCard (.vcf)
        </a>
        <a href="%{pubkey_pem_url}" class="btn" download>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          Certificate (.pem)
        </a>
        <a href="%{pubkey_der_url}" class="btn" download>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          Certificate (.crt)
        </a>
        <a href="%{prof_url}" class="btn" download>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          Profile (Turtle)
        </a>
        <a href="%{jsonld_prof_url}" class="btn" download>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          Profile (JSON-LD)
        </a>
      </div>
    </div>
  </section>

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
        <button class="btn btn-primary open-button" onclick="document.getElementById('opal-form').style.display='block'">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
          Open Chat
        </button>
      </div>
    </div>
  </section>
  !!.

  <!-- ═══ FOOTER ═══ -->
  <footer class="footer">
    <div class="footer-links">
      <a href="%{webid}">%{subj_name}</a>
      <a href="%{prof_url}">Turtle Profile</a>
      <a href="%{jsonld_prof_url}">JSON-LD Profile</a>
      <a href="%{rdfa_prof_url}">RDFa Profile</a>
      <a href="%{vcard_url}">vCard</a>
    </div>
    <div class="footer-copy">
      Web&#8209;Scale Verifiable Digital Identity generated using
      <a href="https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/youid">youid</a>.
      Linked Data resolved via
      <a href="https://linkeddata.uriburner.com/">URIBurner</a>
      (<a href="https://virtuoso.openlinksw.com/">Virtuoso</a>-backed).
    </div>
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
  var el = document.querySelector('.cardQr');
  if (el && typeof qrcode !== 'undefined') {
    var errorCorrectionLevel = 'M';
    var typeNumber = 10;
    qrcode.stringToBytes = qrcode.stringToBytesFuncs['default'];
    var qr = qrcode(typeNumber, errorCorrectionLevel);
    qr.addData(location.href, 'Byte');
    qr.make();
    el.innerHTML = qr.createImgTag(2, 2, 'QR code');
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
