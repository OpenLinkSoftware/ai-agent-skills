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
!!{use_opal_widget}
<link rel="stylesheet" href="./style_opal.css" />
!!.

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
    --accent: #2563eb;
    --accent-light: #3b82f6;
    --accent-gradient: linear-gradient(135deg, #2563eb, #7c3aed);
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

  /* ── Header / Hero ── */
  .hero {
    background: var(--accent-gradient);
    border-radius: var(--radius);
    padding: 40px 32px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 28px;
    flex-wrap: wrap;
    color: white;
    position: relative;
    overflow: hidden;
  }
  .hero::before {
    content: '';
    position: absolute;
    top: -50%; right: -20%;
    width: 400px; height: 400px;
    border-radius: 50%;
    background: rgba(255,255,255,0.05);
    pointer-events: none;
  }
  .hero::after {
    content: '';
    position: absolute;
    bottom: -30%; left: -10%;
    width: 300px; height: 300px;
    border-radius: 50%;
    background: rgba(255,255,255,0.04);
    pointer-events: none;
  }
  .hero-photo {
    width: 120px; height: 120px;
    border-radius: 50%;
    object-fit: cover;
    border: 3px solid rgba(255,255,255,0.3);
    flex-shrink: 0;
    position: relative;
    z-index: 1;
  }
  .hero-body { position:relative; z-index:1; flex:1; min-width:200px; }
  .hero-name {
    font-size: 1.65rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    margin-bottom: 2px;
  }
  .hero-name a {
    color: inherit;
    text-decoration: none;
  }
  .hero-name a:hover {
    text-decoration: underline;
  }
  .hero-title {
    font-size: 0.95rem;
    opacity: 0.85;
    font-weight: 400;
  }
  .hero-meta {
    display: flex;
    gap: 12px;
    margin-top: 10px;
    flex-wrap: wrap;
    font-size: 0.82rem;
  }
  .hero-meta-item {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: rgba(255,255,255,0.12);
    padding: 3px 10px;
    border-radius: 20px;
    backdrop-filter: blur(4px);
  }
  .verified-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: rgba(255,255,255,0.15);
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 500;
  }
  .qr-container {
    position: relative;
    z-index: 1;
    width: 88px; height: 88px;
    background: white;
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
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  .card-header svg {
    width: 18px; height: 18px;
    flex-shrink: 0;
    opacity: 0.7;
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

  /* ── Accordion (details/summary) ── */
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

  /* ── Nested Accordion (Public Key inside Certificate) ── */
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
    border-color: var(--accent);
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
    padding: 24px 0 8px;
    font-size: 0.75rem;
    color: var(--text-muted);
    border-top: 1px solid var(--border);
    margin-top: 24px;
  }
  .footer a { color: var(--accent); text-decoration: none; }
  .footer a:hover { text-decoration: underline; }

  /* ── QR fallback ── */
  .cardQr img { width: 80px; height: 80px; }

  /* ── Responsive tweaks ── */
  @media (max-width:480px) {
    .hero { padding: 24px 20px; gap: 16px; }
    .hero-photo { width: 80px; height: 80px; }
    .hero-name { font-size: 1.25rem; }
    .qr-container { width: 64px; height: 64px; }
    .qr-container canvas, .qr-container img { width: 58px; height: 58px; }
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
        <span class="verified-badge">✓ Verified WebID</span>
      </div>
    </div>
    <div class="qr-container cardQr"></div>
  </header>

  <!-- ═══ CERTIFICATE ═══ -->
  <section class="card" typeof="oplcert:Certificate" resource="%{card_url}#cert">
    <div class="card-header">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
      X.509 Certificate
      <span style="margin-left:auto;display:flex;gap:6px;flex-wrap:wrap">
        <span class="tag tag-valid">✓ Active</span>
        <span class="tag tag-valid">RSA 2048</span>
      </span>
    </div>
    <details class="card-body">
      <summary>
        <span>Subject: <strong>%{subj_name}</strong></span>
        <span class="summary-preview">%{date_before}–%{date_after} · Self‑Signed</span>
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
              RSA Public Key — <strong>%{exponent}</strong> · 2048 bit
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
      AI Agent — OPAL
    </div>
    <div class="card-body">
      <p style="font-size:0.88rem;color:var(--text-secondary);margin-bottom:12px">
        Ask questions about this identity, the certificate, or explore the knowledge graph.
      </p>
      <div class="btn-group">
        <button class="btn btn-primary open-button" id="open-chat-btn">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
          Open Chat
        </button>
      </div>
    </div>
  </section>

  <!-- ═══ OPAL CHAT FORM ═══ -->
  <textarea id="clipboard-text" style="display:none"></textarea>
  <div class="chat-popup" id="opal-form">
    <div class="form-container">
      <div class="form-header">
        <div class="form-header-title">
          <h1>Talk with OPAL</h1>
          <span id="info" style="margin-left:10px;color:yellow;display:none">Connecting</span>
        </div>
        <div class="form-header-btn">
          <span type="button" title="Copy" class="header-btn clipboard-btn" data-clipboard-target="#clipboard-text">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>
          </span>
          <span type="button" title="Share" class="header-btn share-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M4 12v8a2 2 0 002 2h12a2 2 0 002-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" y1="2" x2="12" y2="15"/></svg>
          </span>
          <a class="header-btn loggedin-btn" id="uid-icon-link" href="" target="_blank" style="display:none" title="">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          </a>
          <button type="button" title="Logout" id="logoutID" style="display:none;background:none;border:none;cursor:pointer;padding:4px"><img src="./logout.svg" width="16" height="16"/></button>
          <button type="button" title="Login" id="loginID" style="display:none;background:none;border:none;cursor:pointer;padding:4px"><img src="./login.svg" width="16" height="16"/></button>
          <span type="button" title="Close" class="header-btn close-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </span>
        </div>
      </div>
      <div class="messages">
        <div class="questions">
          <button type="button" class="prompt">Who are you?</button>
          <button type="button" class="prompt">What are your capabilities?</button>
          <button type="button" class="prompt">How can you help me?</button>
        </div>
      </div>
      <div class="input_wrapper">
        <div style="flex:1">
          <textarea placeholder="Type message.." id="message_input" required></textarea>
        </div>
        <div class="input_btns">
          <button type="button" class="send">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
          </button>
          <button type="button" class="stop" style="display:none">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><circle cx="12" cy="12" r="10"/><line x1="8" y1="12" x2="16" y2="12"/></svg>
          </button>
        </div>
      </div>
    </div>
    <div style="display:flex;flex-direction:row-reverse">
      <img class="resizer" src="data:image/gif;base64,R0lGODlhCgAKAJEAAAAAAP///6CgpP///yH5BAEAAAMALAAAAAAKAAoAAAIRnI+JosbN3hryRDqvxfp2zhUAOw==" alt="Resize" width="15" height="15"/>
    </div>
  </div>
  !!.

  <!-- ═══ FOOTER ═══ -->
  <footer class="footer">
    <p>
      Web‑Scale Verifiable Digital Identity for <a href="%{webid}">%{subj_name}</a> ·
      Generated using <a href="https://github.com/OpenLinkSoftware/ai-agent-skills/tree/main/youid">youid</a> ·
      <a href="%{prof_url}">Turtle</a> ·
      <a href="%{jsonld_prof_url}">JSON-LD</a> ·
      <a href="%{rdfa_prof_url}">RDFa</a> ·
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

<!-- ═══ OPAL Chat Widget ═══ -->
!!{use_opal_widget}
<script src="https://cdn.jsdelivr.net/npm/markdown-it@14/dist/markdown-it.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/clipboard@2/dist/clipboard.min.js"></script>
<script src="./solid-client-authn.bundle.js"></script>
<script src="./opal.js"></script>
<script src="./win.js"></script>
<script>
(function() {
  var md = window.markdownit({ html: true, breaks: true, linkify: true, langPrefix: 'language-' });

  md.renderer.rules.link_open = function(tokens, idx, options, env, self) {
    var hrefIndex = tokens[idx].attrIndex('href');
    var href = hrefIndex >= 0 ? tokens[idx].attrs[hrefIndex][1] : '';
    if (href && href.startsWith('#')) return self.renderToken(tokens, idx, options);
    var targetIndex = tokens[idx].attrIndex('target');
    if (targetIndex < 0) tokens[idx].attrPush(['target', '_blank']);
    else tokens[idx].attrs[targetIndex][1] = '_blank';
    var relIndex = tokens[idx].attrIndex('rel');
    if (relIndex < 0) tokens[idx].attrPush(['rel', 'noopener noreferrer']);
    else tokens[idx].attrs[relIndex][1] = 'noopener noreferrer';
    return self.renderToken(tokens, idx, options);
  };

  var clipboard = new ClipboardJS('.clipboard-btn');
  clipboard.on('success', function() { showNotice('Copied.'); });

  var baseUrl = '%{w_opl_endpoint}';
  var hostname = new URL(baseUrl).hostname;

  var authClient = solidClientAuthentication.default;
  var session = authClient.getDefaultSession();

  var opal = new Opal(authClient, hostname, receiveMessage, errorHandler, {
    model: '%{w_model}',
    top_p: %{w_top_p},
    temperature: %{w_temperature},
    module: '%{w_module}'
  });

  var $currentMessage = null;
  var currentText = '';
  var messagesEl = document.querySelector('.chat-popup .messages');

  function receiveMessage(role, chunk) {
    if (role === 'function' || role === 'tool' || role === 'function_response') return;
    if (role === 'notice') { showNotice(chunk); return; }
    if (chunk === '[DONE]' || chunk === '[LENGTH]') {
      $currentMessage = null;
      currentText = '';
      var cursor = messagesEl.querySelector('.cursor');
      if (cursor) cursor.remove();
      document.querySelector('.stop').style.display = 'none';
      document.querySelector('.send').style.display = '';
      messagesEl.scrollTop = messagesEl.scrollHeight;
      document.querySelectorAll('.prompt').forEach(function(el) {
        el.onclick = sendPredefinedPrompt;
      });
    } else if (!$currentMessage) {
      currentText = chunk;
      $currentMessage = document.createElement('div');
      $currentMessage.className = 'agent-message';
      $currentMessage.innerHTML = md.render(currentText);
      messagesEl.appendChild($currentMessage);
      messagesEl.scrollTop = messagesEl.scrollHeight;
      var cursor = document.createElement('span');
      cursor.className = 'cursor';
      $currentMessage.insertAdjacentElement('afterend', cursor);
      document.querySelector('.stop').style.display = '';
      document.querySelector('.send').style.display = 'none';
      var ct = document.getElementById('clipboard-text');
      ct.value = ct.value + '\nassistant: ' + chunk;
    } else {
      currentText = currentText + chunk;
      $currentMessage.innerHTML = md.render(currentText);
      messagesEl.scrollTop = messagesEl.scrollHeight;
      var ct = document.getElementById('clipboard-text');
      ct.value = ct.value + chunk;
    }
  }

  function errorHandler(error) {
    var msg = document.createElement('div');
    msg.className = 'agent-message';
    msg.textContent = error;
    messagesEl.appendChild(msg);
  }

  function showNotice(text) {
    var info = document.getElementById('info');
    info.textContent = text;
    info.style.display = 'inline';
    setTimeout(function() { info.style.display = 'none'; }, 3000);
  }

  function sleep(ms) { return new Promise(function(resolve) { setTimeout(resolve, ms); }); }

  function connect() {
    var tm_sleep = 250;
    var cnt = Math.floor(10000 / tm_sleep);
    return new Promise(async function(resolve) {
      if (opal.getChatId()) { resolve(1); return; }
      showNotice('Connecting...');
      try {
        if (!opal.isConnecting()) await opal.connect();
        for (var i = 0; i < cnt; i++) {
          if (opal.getChatId()) { resolve(1); return; }
          await sleep(tm_sleep);
        }
        resolve(0);
      } catch(_) { resolve(0); }
    });
  }

  function sendPrompt(text) {
    text = text.trim();
    if (!text.length) return;
    var ct = document.getElementById('clipboard-text');
    if (!session.info.isLoggedIn) {
      localStorage.setItem('prompt0', text);
      var msg = document.createElement('div');
      msg.className = 'user-message';
      msg.innerHTML = '<pre style="color:red">You need to Login</pre>';
      messagesEl.appendChild(msg);
      setTimeout(function() { document.getElementById('loginID').click(); }, 300);
      return;
    }
    (async function() {
      if (!opal.getChatId()) await connect();
      var msg = document.createElement('div');
      msg.className = 'user-message';
      msg.innerHTML = '<pre>' + text.replace(/</g,'&lt;') + '</pre>';
      messagesEl.appendChild(msg);
      messagesEl.scrollTop = messagesEl.scrollHeight;
      document.querySelectorAll('.prompt').forEach(function(el) { el.onclick = null; });
      ct.value = ct.value + '\nuser: ' + text;
      await opal.send(text);
      var questions = document.querySelector('.questions');
      if (questions) questions.style.display = 'none';
      document.getElementById('message_input').value = '';
    })();
  }

  function sendPredefinedPrompt(e) {
    var text = e.target.innerHTML;
    var ob = document.getElementById('open-chat-btn');
    if (ob && ob.style.display !== 'none') {
      ob.style.display = 'none';
      document.getElementById('opal-form').style.display = 'block';
    }
    sendPrompt(text);
  }

  document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('open-chat-btn').onclick = function() {
      this.style.display = 'none';
      document.getElementById('opal-form').style.display = 'block';
    };
    document.querySelector('.close-btn').onclick = function() {
      document.getElementById('opal-form').style.display = 'none';
      document.getElementById('open-chat-btn').style.display = '';
    };
    document.querySelector('.share-btn').onclick = function() { opal.share(); };
    document.getElementById('message_input').addEventListener('keypress', function(e) {
      if (!e.shiftKey && e.which === 13) {
        e.preventDefault();
        sendPrompt(this.value);
      }
    });
    document.querySelector('.send').onclick = function() {
      sendPrompt(document.getElementById('message_input').value);
    };
    document.querySelector('.stop').onclick = function() { opal.stop(); };
    document.querySelectorAll('.prompt').forEach(function(el) { el.onclick = sendPredefinedPrompt; });

    try {
      var imgBase = new URL('/chat/', baseUrl).toString();
      document.querySelectorAll('img').forEach(function(img) {
        var src = img.getAttribute('src');
        if (src && src.indexOf('svg/') === 0) img.src = new URL(src, imgBase).href;
      });
    } catch(_) {}

    var opalWin = document.querySelector('#opal-form');
    var headerTitle = document.querySelector('div.form-header-title');
    if (opalWin && headerTitle) dragElement(opalWin, headerTitle);
    if (opalWin) makeResizable(opalWin, document.querySelector('#opal-form .resizer'), 405, 585);

    document.getElementById('loginID').onclick = function() {
      var url = new URL(window.location.href);
      url.hash = '';
      localStorage.setItem('login', '1');
      authClient.login({
        oidcIssuer: baseUrl,
        redirectUrl: url.toString(),
        tokenType: 'DPoP',
        clientName: 'OpenLink Demo'
      });
    };
    document.getElementById('logoutID').onclick = function() {
      var url = new URL(window.location.href);
      url.search = '';
      authClient.logout().then(function() { location.replace(url.toString()); });
    };

    authClient.handleIncomingRedirect({ restorePreviousSession: false }).then(function(info) {
      var loggedIn = info && info.isLoggedIn;
      document.getElementById('loginID').style.display = loggedIn ? 'none' : '';
      document.getElementById('logoutID').style.display = loggedIn ? '' : 'none';
      var isLogin = localStorage.getItem('login');
      localStorage.removeItem('login');
      var prompt = localStorage.getItem('prompt0');
      localStorage.removeItem('prompt0');
      if (info && info.webId) {
        var link = document.getElementById('uid-icon-link');
        link.href = info.webId;
        link.title = info.webId;
        link.style.display = '';
        if (isLogin) {
          document.getElementById('open-chat-btn').click();
          if (prompt) sendPrompt(prompt);
        }
      }
    }).catch(function(e) { errorHandler(e.toString()); });
  });
})();
</script>
!!.

<!-- ═══ Hidden RDFa annotations ═══ -->
!!{em_rdfa}
%{rdfa}
!!.
</body>
</html>