# OAuth Bearer Token Setup Guide

The ACP API requires a bearer token (`ACP_AUTH_TOKEN`) for all requests. This
guide explains how to obtain one manually via the OpenLink OAuth applications
page.

## Supported Instances

| Instance | OAuth Applications URL |
|---|---|
| **ods-qa (default)** | `https://ods-qa.openlinksw.com/oauth/applications.vsp` |
| **shop (production)** | `https://shop.openlinksw.com/oauth/applications.vsp` |
| **Custom** | `https://{your-host}/oauth/applications.vsp` |

## Step-by-Step Instructions

### 1. Navigate to the OAuth Applications Page

Open your browser and go to the appropriate URL above. If your `ACP_BASE_URL`
is a custom instance, construct the OAuth URL by replacing the path with
`/oauth/applications.vsp`.

### 2. Authenticate

The page is protected. You will see an authentication form with multiple login
options:

- **SQL Digest login** — username and password for the Virtuoso instance
- **WebID-TLS** — authenticate using a client certificate
- **Social login** — GitHub, Google, LinkedIn, etc. (depending on instance
  configuration)

Log in using one of the available methods.

### 3. Register an OAuth Application

After authentication, you will be taken to the OAuth applications management
page. To obtain a bearer token:

1. Click **"Register new application"** (or equivalent)
2. Fill in the application details:
   - **Name**: A descriptive name (e.g., "ACP CLI Client")
   - **Redirect URI**: `https://localhost` (or your actual callback URL)
   - **Scopes**: Select the scopes required for checkout/cart operations
3. Submit the form

### 4. Copy the Bearer Token

After registration, the page will display:

- `client_id`
- `client_secret`
- **Bearer token** (access token)

Copy the **bearer token** value. This is your `ACP_AUTH_TOKEN`.

### 5. Export the Token

In your terminal or shell profile:

```bash
export ACP_AUTH_TOKEN="sk_..."
```

Or provide it when the skill prompts you.

## Troubleshooting

| Issue | Resolution |
|---|---|
| "401 Unauthorized" on API calls | Token expired or invalid; repeat steps 1–5 |
| OAuth page returns 404 | Verify the URL uses `/oauth/applications.vsp` (plural) |
| Cannot log in | Contact the instance administrator for SQL credentials or social login configuration |
| No "Register application" button | Your user account may lack permission; request access |

## Note for Agents

This skill does **not** implement a programmatic OAuth 2.0 flow. The user must
obtain the bearer token manually via the web form. Once obtained, the token is
used in all subsequent `Authorization: Bearer {token}` headers.
