---
name: mpp-stripe-client
description: >
  Machine Payment Protocol (MPP) client using Stripe. Prompts for a target MPP-protected
  URL, then handles the 402 challenge flow automatically — creating a Stripe Shared Payment
  Token (SPT) and retrying to retrieve the paid resource.
version: 1.0.0
type: skill
---

# MPP Stripe Client Skill

## When to Use

- "Pay for this resource at ..."
- "Access this MPP-protected URL ..."
- "Use Stripe to pay for ..."
- "Run MPP client against ..."
- Any request referencing a URL that returns `402 Payment Required` with an MPP challenge.

## Prerequisites

The project must be installed at `~/Documents/Management/Development/mpp-stripe-client/`:

```bash
cd ~/Documents/Management/Development/mpp-stripe-client
npm install
```

A Stripe test secret key (`sk_test_...`) is required. Set it as an environment variable:

```bash
export STRIPE_SECRET_KEY=sk_test_...
```

Or the skill will ask for it.

## Workflow

⛔ **PRE-BUILD CHECK**: Before producing output, re-read the relevant workflow section above and re-read any checklists or verification gates defined in this skill. Confirm each checklist item before writing output. Build to pass — do not retro-fit. Apply the CLAUDE.md Anti-Drift Protocol: re-read spec section before build, gate-first validation, section-by-section delivery.

### Step 1 — Collect target URL and Stripe key

Ask the user for:

1. **Target URL** — the MPP-protected resource to access
2. **Stripe secret key** — if `STRIPE_SECRET_KEY` is not already in the environment

If no URL is provided, ask for it. Do not assume defaults.

### Step 2 — Run the MPP client

With the target URL and Stripe key confirmed, execute the client. The client runs from the installed project directory and accepts the target URL as `SERVER_URL`:

```bash
cd ~/Documents/Management/Development/mpp-stripe-client \
  && SERVER_URL="<target-url>" STRIPE_SECRET_KEY="<key>" npx tsx cli.ts
```

Do **not** use `npm run cli` — it reads `.env` which overrides inline variables with localhost defaults. Always invoke `npx tsx cli.ts` directly with inline `SERVER_URL` and `STRIPE_SECRET_KEY`.

The client will:

1. `GET <target-url>` — receive `402 Payment Required` with challenge
2. Create a Stripe test payment method
3. Create a Stripe Shared Payment Token (SPT) scoped to the challenge amount
4. `GET <target-url>` with `Authorization: Payment <credential>`
5. Receive `200` with the paid resource and receipt

### Step 3 — Present the result

Show the user:

- The HTTP status
- The response body (the paid resource)
- The receipt header value (`Authentication-Info`)

### Error handling

- If the server doesn't return `402`, report the actual status and body.
- If Stripe calls fail, report the Stripe error message.
- If the MPP challenge parsing fails, report the raw challenge for diagnosis.

## Configuration

| Variable | Required | Default |
|----------|:---:|---------|
| `STRIPE_SECRET_KEY` | Yes | Prompted if missing |
| `SERVER_URL` | Yes | Prompted if missing |
| `STRIPE_PAYMENT_METHOD` | No | Creates test card `pm_...` |
| `MPPX_STRIPE_SPT_URL` | No | Stripe test endpoint |
