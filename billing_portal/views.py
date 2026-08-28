import json
import os

import stripe
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from . import client  # noqa: F401 — configures stripe.api_key
from .webhook_handlers import dispatch_stripe_event

# No one knows test/doc coverage: price_1ThGVPRxznXvj6jhV69geQ0S
# **Team dashboard**: price_1ThGVQRxznXvj6jhaR9a6Adl
# **Watch + live sync**: price_1ThGVQRxznXvj6jhwv6NHmtI
# **Drifted this week**: price_1ThGVRRxznXvj6jhwm6PsaEm
# **All projects**: price_1ThGVSRxznXvj6jhZp0y2DVs
# **Team score trend**: price_1ThGVSRxznXvj6jhExAlFxW1
# `GET /badge/{slug}.svg`: price_1ThGVTRxznXvj6jhPUpe5XFJ
# API: price_1ThGVURxznXvj6jhdxHhf2tF
# Server: price_1ThGVURxznXvj6jhw95sgVeI
# Starter: price_1ThGVVRxznXvj6jhkTEN7JyG
# Pro: price_1ThGVVRxznXvj6jhfB7TBkpu


def _post_value(request, key):
    if request.content_type and "application/json" in request.content_type:
        try:
            return json.loads(request.body).get(key)
        except json.JSONDecodeError:
            return None
    return request.POST.get(key)


@csrf_exempt
@require_POST
def webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    if not sig_header or not secret:
        return HttpResponse("Missing signature or webhook secret", status=400)
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, secret)
    except ValueError:
        return HttpResponse("Invalid payload", status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse("Invalid signature", status=400)

    try:
        dispatch_stripe_event(event)
    except Exception as exc:
        print(f"[stripe] Webhook handler error: {exc}")
        return JsonResponse({"error": "handler failed"}, status=500)

    return JsonResponse({"received": True})


@require_POST
def checkout(request):
    price_id = _post_value(request, "priceId")
    if not price_id:
        return JsonResponse({"error": "priceId required"}, status=400)
    app_url = os.environ.get("APP_URL", "https://specwright-api-production.up.railway.app")
    user_id = None
    if getattr(request, "user", None) and request.user.is_authenticated:
        user_id = str(request.user.pk)
    session = stripe.checkout.Session.create(
        mode="subscription",
        customer_email=_post_value(request, "customerEmail") or getattr(request.user, "email", None),
        client_reference_id=user_id,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{app_url}/stripe/success/?session_id=",
        cancel_url=f"{app_url}/stripe/pricing/",
    )
    return redirect(session.url)


@require_POST
def portal(request):
    customer_id = _post_value(request, "customerId")
    if not customer_id and getattr(request, "user", None) and request.user.is_authenticated:
        from .db import get_stripe_customer_for_user
        customer_id = get_stripe_customer_for_user(request.user.pk)
    if not customer_id:
        customer_id = request.session.get("stripe_customer_id")
    if not customer_id:
        return JsonResponse({"error": "customerId required"}, status=400)
    app_url = os.environ.get("APP_URL", "https://specwright-api-production.up.railway.app")
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=f"{app_url}/stripe/account/",
    )
    return redirect(session.url)


@csrf_exempt
@require_POST
def session_info(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    session_id = data.get("sessionId")
    if not session_id:
        return JsonResponse({"error": "sessionId required"}, status=400)
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError as e:
        return JsonResponse({"error": str(e)}, status=400)
    customer_id = session.customer if isinstance(session.customer, str) else getattr(session.customer, "id", None)
    return JsonResponse({
        "customerId": customer_id,
        "email": session.customer_email,
        "status": session.status,
    })


def stripe_me(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return JsonResponse({"customerId": None, "source": None}, status=401)
    from .db import get_stripe_customer_for_user, get_active_subscription_for_customer

    customer_id = get_stripe_customer_for_user(request.user.pk)
    source = "database" if customer_id else None
    if not customer_id:
        customer_id = request.session.get("stripe_customer_id")
        source = "session" if customer_id else None
    payload = {"customerId": customer_id, "source": source}
    if customer_id:
        sub = get_active_subscription_for_customer(customer_id)
        if sub:
            payload["subscription"] = sub
    return JsonResponse(payload)


STRIPE_TIERS = [
    {"key": "no-one-knows-test-doc-coverage", "tier": "No one knows test/doc coverage", "price_id": "price_1ThGVPRxznXvj6jhV69geQ0S", "label": "$0.00/month"},
    {"key": "team-dashboard", "tier": "**Team dashboard**", "price_id": "price_1ThGVQRxznXvj6jhaR9a6Adl", "label": "$7.00/month"},
    {"key": "watch-live-sync", "tier": "**Watch + live sync**", "price_id": "price_1ThGVQRxznXvj6jhwv6NHmtI", "label": "$3.00/month"},
    {"key": "drifted-this-week", "tier": "**Drifted this week**", "price_id": "price_1ThGVRRxznXvj6jhwm6PsaEm", "label": "$7.00/month"},
    {"key": "all-projects", "tier": "**All projects**", "price_id": "price_1ThGVSRxznXvj6jhZp0y2DVs", "label": "$7.00/month"},
    {"key": "team-score-trend", "tier": "**Team score trend**", "price_id": "price_1ThGVSRxznXvj6jhExAlFxW1", "label": "$8.00/month"},
    {"key": "get-badge-slug-svg", "tier": "`GET /badge/{slug}.svg`", "price_id": "price_1ThGVTRxznXvj6jhPUpe5XFJ", "label": "$302.00/month"},
    {"key": "api", "tier": "API", "price_id": "price_1ThGVURxznXvj6jhdxHhf2tF", "label": "$1.00/month"},
    {"key": "server", "tier": "Server", "price_id": "price_1ThGVURxznXvj6jhw95sgVeI", "label": "$120.00/month"},
    {"key": "starter", "tier": "Starter", "price_id": "price_1ThGVVRxznXvj6jhkTEN7JyG", "label": "$29.00/month"},
    {"key": "pro", "tier": "Pro", "price_id": "price_1ThGVVRxznXvj6jhfB7TBkpu", "label": "$79.00/month"},
]


def pricing(request):
    return render(request, "billing_portal/pricing.html", {"tiers": STRIPE_TIERS})


def success(request):
    session_id = request.GET.get("session_id")
    if session_id:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            customer_id = session.customer if isinstance(session.customer, str) else getattr(session.customer, "id", None)
            if customer_id:
                request.session["stripe_customer_id"] = customer_id
        except stripe.error.StripeError:
            pass
    return render(request, "billing_portal/success.html", {"session_id": session_id})


def account(request):
    customer_id = request.session.get("stripe_customer_id")
    if not customer_id and getattr(request, "user", None) and request.user.is_authenticated:
        from .db import get_stripe_customer_for_user
        customer_id = get_stripe_customer_for_user(request.user.pk)
    return render(request, "billing_portal/account.html", {"customer_id": customer_id})
