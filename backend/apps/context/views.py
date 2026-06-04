from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.organizations.models import Membership

from .meaning import screen_context

VALID_SCREENS = {
    "dashboard",
    "cases",
    "approvals",
    "runs",
    "memory",
    "compliance",
    "audit",
    "templates",
    "integrations",
    "workflows",
}


class ScreenContextView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, screen: str):
        if screen not in VALID_SCREENS:
            return Response({"detail": f"Unknown screen. Valid: {sorted(VALID_SCREENS)}"}, status=400)
        membership = request.user.memberships.filter(is_primary=True).first()
        if not membership:
            membership = request.user.memberships.first()
        if not membership:
            return Response({"detail": "No organization membership."}, status=400)
        ctx = screen_context(screen, request.user, membership.organization)
        return Response({"screen": screen, "context": ctx})
