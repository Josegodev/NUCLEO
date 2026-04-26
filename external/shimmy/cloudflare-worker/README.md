# Shimmy License Webhook (Cloudflare Worker)

Receives Stripe `checkout.session.completed` webhooks and creates licenses in Keygen.

## Setup

### 1. Install Wrangler CLI
```bash
npm install -g wrangler
wrangler login
```

### 2. Deploy the Worker
```bash
cd cloudflare-worker
wrangler deploy
```

This will output a URL like: `https://shimmy-license-webhook.<your-subdomain>.workers.dev`

### 3. Set Secrets

```bash
# Your Keygen account ID
wrangler secret put KEYGEN_ACCOUNT_ID
# Enter: 6270bf9c-23ad-4483-9296-3a6d9178514a

# Your Keygen product token (starts with prod-)
wrangler secret put KEYGEN_PRODUCT_TOKEN
# Enter: (from .env KEYGEN_PRODUCT_TOKEN)

# Your Keygen policy ID for Shimmy Vision
wrangler secret put KEYGEN_POLICY_ID
# Enter: (your shimmy-vision policy ID)

# Stripe webhook signing secret (get this after creating webhook in Stripe)
wrangler secret put STRIPE_WEBHOOK_SECRET
# Enter: whsec_... (from Stripe dashboard)
```

### 4. Create Stripe Webhook

1. Go to [Stripe Webhooks](https://dashboard.stripe.com/test/webhooks) (TEST MODE)
2. Click "Add endpoint"
3. Endpoint URL: `https://shimmy-license-webhook.<your-subdomain>.workers.dev/stripe-webhook`
4. Select events: `checkout.session.completed`
5. Click "Add endpoint"
6. Copy the "Signing secret" (starts with `whsec_`)
7. Run `wrangler secret put STRIPE_WEBHOOK_SECRET` and paste it

### 5. Create Test Payment Link

1. Go to [Stripe Payment Links](https://dashboard.stripe.com/test/payment-links)
2. Create a product "Shimmy Vision Test" for $1.00
3. Create payment link
4. Test with card `4242 4242 4242 4242`

### 6. Verify License Created

Check Keygen dashboard or:
```bash
curl -s "https://api.keygen.sh/v1/accounts/$KEYGEN_ACCOUNT_ID/licenses" \
  -H "Authorization: Bearer $KEYGEN_PRODUCT_TOKEN" | jq '.data[-1]'
```

## Local Development

Create `.dev.vars` (gitignored):
```
STRIPE_WEBHOOK_SECRET=whsec_test_...
KEYGEN_ACCOUNT_ID=6270bf9c-23ad-4483-9296-3a6d9178514a
KEYGEN_PRODUCT_TOKEN=prod-...
KEYGEN_POLICY_ID=...
```

Then:
```bash
wrangler dev
# Use Stripe CLI to forward webhooks:
stripe listen --forward-to localhost:8787/stripe-webhook
```

## Endpoints

- `POST /stripe-webhook` - Stripe webhook receiver
- `POST /health` - Health check (returns `{"status": "ok"}`)

## Logs

View real-time logs:
```bash
wrangler tail
```
