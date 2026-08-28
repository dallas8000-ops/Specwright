# Domain & SSL Setup

Production URL: https://specwright-api-production.up.railway.app
Domain: specwright-api-production.up.railway.app
Framework: django

## SSL
SSL/TLS is automatic on Vercel, Railway, and Fly.io custom domains.

## Stripe Webhook (production)
Update webhook URL to: `https://specwright-api-production.up.railway.app/stripe/webhook/`

## Verification
```bash
curl https://specwright-api-production.up.railway.app/stripe/health
```
Run readiness from Stripe Installer after deploy.
