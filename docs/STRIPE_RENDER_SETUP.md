# Stripe + Render setup

Production API host: `https://specwright-api.onrender.com`
Webhook URL: `https://specwright-api.onrender.com/api/v1/billing/webhook`

## 1. Stripe Dashboard

1. Open Stripe Dashboard in test mode until go-live.
2. Copy the secret key from Developers -> API keys.
3. Create or open the Specwright Starter and Pro subscription products.
4. Copy the recurring monthly Price IDs. They start with `price_`.

## 2. Render environment

In Render, open `specwright-api` -> Environment and set:

| Key | Value |
| --- | --- |
| `SPECWRIGHT_STRIPE_SECRET_KEY` | `sk_test_...` or `sk_live_...` |
| `SPECWRIGHT_STRIPE_WEBHOOK_SECRET` | `whsec_...` after creating the webhook |
| `SPECWRIGHT_STRIPE_PRICE_ID_STARTER` | Starter recurring `price_...` |
| `SPECWRIGHT_STRIPE_PRICE_ID_PRO` | Pro recurring `price_...` |

These keys are declared in `render.yaml` with `sync: false`, so Render prompts for values and no secrets are committed to git.

## 3. Stripe webhook

Create a Stripe webhook endpoint:

```text
https://specwright-api.onrender.com/api/v1/billing/webhook
```

Required event:

```text
checkout.session.completed
```

Copy the webhook signing secret into `SPECWRIGHT_STRIPE_WEBHOOK_SECRET`, then redeploy `specwright-api`.

## 4. Verify

```bash
python scripts/verify_stripe_config.py
```

Or check directly:

```bash
curl -s https://specwright-api.onrender.com/api/v1/health/billing
```

The response reports only whether each setting exists. It never returns secret values.
