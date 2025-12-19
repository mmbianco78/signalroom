# Service Account Setup Guide

This guide walks through setting up all service accounts needed for SignalRoom notifications and deployment.

**Sending Domain:** `criticalsignals.io`

---

## Table of Contents

1. [Slack (Notifications)](#1-slack-notifications)
2. [Resend (Email)](#2-resend-email)
3. [Twilio (SMS)](#3-twilio-sms)
4. [Fly.io (Deployment)](#4-flyio-deployment)
5. [Summary: Values Needed](#5-summary-values-needed)

---

## 1. Slack (Notifications)

### Step 1.1: Create Slack App

1. Go to https://api.slack.com/apps
2. Click **"Create New App"**
3. Select **"From scratch"**
4. Enter:
   - App Name: `SignalRoom`
   - Workspace: Select your workspace
5. Click **"Create App"**

### Step 1.2: Configure Bot Permissions

1. In the left sidebar, click **"OAuth & Permissions"**
2. Scroll to **"Scopes"** → **"Bot Token Scopes"**
3. Click **"Add an OAuth Scope"** and add:
   - `chat:write` (Send messages)
   - `chat:write.public` (Send to channels without joining)

### Step 1.3: Install to Workspace

1. Scroll up to **"OAuth Tokens for Your Workspace"**
2. Click **"Install to Workspace"**
3. Review permissions and click **"Allow"**
4. Copy the **Bot User OAuth Token** (starts with `xoxb-`)

app id: A0A5JPTBS3A
client id: 3003448746865.10188809400112
client secret: a480e2196b5904aae531f2c4bfa31f34
signing secret: 
bf330ee4d7102b6071e5b4025e2ad222
ver token: zKytTV5YgNlqAbjO8mo3VwYS

### Step 1.4: Get Channel ID


1. Open Slack and go to the channel where you want reports sent
2. Right-click the channel name → **"View channel details"**
3. Scroll to the bottom and copy the **Channel ID** (starts with `C`)

### What I Need Back

```
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx
SLACK_CHANNEL_ID=C0123456789
```

---

## 2. Resend (Email)

Resend is a modern email API. We'll set up domain verification for `criticalsignals.io`.

### Step 2.1: Create Resend Account

1. Go to https://resend.com
2. Click **"Start for free"**
3. Sign up with email or GitHub

### Step 2.2: Get API Key

1. Go to https://resend.com/api-keys
2. Click **"Create API Key"**
3. Enter:
   - Name: `signalroom-production`
   - Permission: **Sending access** (default)
   - Domain: Leave as "All domains" for now
4. Click **"Add"**
5. Copy the API key (starts with `re_`)

### Step 2.3: Add Domain

1. Go to https://resend.com/domains
2. Click **"Add Domain"**
3. Enter: `criticalsignals.io`
4. Click **"Add"**

### Step 2.4: Configure DNS Records

Resend will show you DNS records to add. You'll need to add these to your domain registrar:

| Type | Name | Value |
|------|------|-------|
| TXT | `resend._domainkey` | (Resend provides this - DKIM key) |
| TXT | `@` or root | (Resend provides this - SPF record) |
| CNAME | `r` | `smtp.resend.com` (optional, for tracking) |

**At your domain registrar (e.g., Namecheap, Cloudflare, GoDaddy):**

1. Go to DNS settings for `criticalsignals.io`
2. Add each record Resend shows you
3. Wait 5-10 minutes for propagation
4. Go back to Resend and click **"Verify"**

### Step 2.5: Choose From Email

Once verified, you can send from any address at your domain. Recommended:
- `reports@criticalsignals.io` - For scheduled reports
- `alerts@criticalsignals.io` - For error alerts

### What I Need Back

```
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
RESEND_FROM_EMAIL=reports@criticalsignals.io
```

Also confirm: **Domain verified?** Yes/No

---

## 3. Twilio (SMS)

### Step 3.1: Create Twilio Account

1. Go to https://www.twilio.com/try-twilio
2. Sign up with email
3. Verify your phone number (required)

### Step 3.2: Get Account Credentials

1. Go to https://console.twilio.com
2. On the dashboard, find **"Account Info"** panel
3. Copy:
   - **Account SID** (starts with `AC`)
   - **Auth Token** (click to reveal)

### Step 3.3: Get a Phone Number

1. Go to https://console.twilio.com/us1/develop/phone-numbers/manage/incoming
2. Click **"Buy a number"**
3. Select a number with SMS capability
4. Click **"Buy"** (free with trial, or ~$1.15/month)
5. Copy the phone number (format: `+15551234567`)

### Step 3.4: Upgrade Account (Optional but Recommended)

Trial accounts have limitations:
- Can only send to verified numbers
- Messages include "Sent from Twilio trial" prefix

To remove limitations:
1. Go to https://console.twilio.com/us1/billing
2. Add payment method and upgrade

### What I Need Back

```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_FROM_NUMBER=+15551234567
```

---

## 4. Fly.io (Deployment)

### Step 4.1: Create Fly.io Account

1. Go to https://fly.io
2. Click **"Sign Up"**
3. Sign up with GitHub (recommended) or email
4. Add a credit card (required for deployment, but generous free tier)

### Step 4.2: Install flyctl CLI

**macOS (Homebrew):**
```bash
brew install flyctl
```

**macOS/Linux (curl):**
```bash
curl -L https://fly.io/install.sh | sh
```

### Step 4.3: Login to Fly

```bash
fly auth login
```

This opens a browser window to authenticate.

### Step 4.4: Verify Installation

```bash
fly version
fly auth whoami
```

### What I Need Back

Confirm:
- [ ] Fly.io account created
- [ ] Credit card added
- [ ] `flyctl` installed
- [ ] `fly auth login` successful

(No secrets needed - we'll configure the app together)

---

## 5. Summary: Values Needed

Once you complete the steps above, provide these values:

### Slack
```
SLACK_BOT_TOKEN=
SLACK_CHANNEL_ID=
```

### Resend
```
RESEND_API_KEY=
RESEND_FROM_EMAIL=reports@criticalsignals.io
```
- Domain verified? [ ]

### Twilio
```
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=
```

### Fly.io
- Account created? [ ]
- CLI installed? [ ]
- Logged in? [ ]

---

## Already Configured (No Action Needed)

These are already set up:

| Service | Status |
|---------|--------|
| Supabase | ✅ foieoinshqlescyocbld |
| Temporal Cloud | ✅ signalroom-713.nzg5u |
| AWS/S3 | ✅ Configured |
| Everflow | ✅ API key configured |
| Redtrack | ✅ API key configured |

---

## DNS Records Reference (criticalsignals.io)

After Resend setup, your DNS should have:

| Type | Name | Purpose |
|------|------|---------|
| TXT | `resend._domainkey.criticalsignals.io` | DKIM (email authentication) |
| TXT | `criticalsignals.io` | SPF (sender verification) |
| CNAME | `r.criticalsignals.io` | Tracking (optional) |

---

## Testing After Setup

Once all values are provided, we can test:

```bash
# Test Slack
python -c "
from signalroom.notifications import send_slack
import asyncio
asyncio.run(send_slack('Test from SignalRoom'))
"

# Test Email
python -c "
from signalroom.notifications import send_email
import asyncio
asyncio.run(send_email('your-email@example.com', 'Test', '<h1>Test</h1>'))
"

# Test SMS
python -c "
from signalroom.notifications import send_sms
import asyncio
asyncio.run(send_sms('+1YOURPHONE', 'Test from SignalRoom'))
"
```

---

## Questions?

If you get stuck on any step, let me know:
- Which service
- Which step
- What error or issue you see
