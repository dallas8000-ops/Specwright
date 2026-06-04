import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

from apps.organizations.models import Membership

logger = logging.getLogger(__name__)
User = get_user_model()


class OpsEventConsumer(AsyncJsonWebsocketConsumer):
    """
    Real-time ops stream — subscribes client to org + user groups.
    Connect: ws://host/ws/ops/?token=<jwt>
    """

    async def connect(self):
        self.user = await self._authenticate()
        if not self.user:
            await self.close(code=4001)
            return

        self.org_ids = await self._org_ids_for_user()
        await self.channel_layer.group_add("ops_global", self.channel_name)
        for org_id in self.org_ids:
            await self.channel_layer.group_add(f"org_{org_id}", self.channel_name)
        await self.channel_layer.group_add(f"user_{self.user.id}", self.channel_name)

        await self.accept()
        await self.send_json(
            {
                "type": "connection.established",
                "user_id": self.user.id,
                "organizations": self.org_ids,
                "message": "Realtime ops stream connected",
            }
        )

    async def disconnect(self, close_code):
        if hasattr(self, "org_ids"):
            await self.channel_layer.group_discard("ops_global", self.channel_name)
            for org_id in self.org_ids:
                await self.channel_layer.group_discard(f"org_{org_id}", self.channel_name)
            if hasattr(self, "user") and self.user:
                await self.channel_layer.group_discard(f"user_{self.user.id}", self.channel_name)

    async def receive_json(self, content, **kwargs):
        if content.get("type") == "ping":
            await self.send_json({"type": "pong", "ts": content.get("ts")})

    async def ops_event(self, event):
        await self.send_json({"type": "domain.event", **event["envelope"]})

    @database_sync_to_async
    def _authenticate(self):
        token = None
        query_string = self.scope.get("query_string", b"").decode()
        if "token=" in query_string:
            for part in query_string.split("&"):
                if part.startswith("token="):
                    token = part.split("=", 1)[1]
                    break
        if not token:
            headers = dict(self.scope.get("headers", []))
            auth = headers.get(b"authorization", b"").decode()
            if auth.lower().startswith("bearer "):
                token = auth[7:].strip()

        if not token:
            return None
        try:
            validated = AccessToken(token)
            user_id = validated.get("user_id")
            return User.objects.get(id=user_id, is_active=True)
        except (InvalidToken, TokenError, User.DoesNotExist):
            return None

    @database_sync_to_async
    def _org_ids_for_user(self):
        return list(
            Membership.objects.filter(user=self.user)
            .values_list("organization_id", flat=True)
            .distinct()
        )
