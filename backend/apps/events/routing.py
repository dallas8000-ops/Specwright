from django.urls import path

from .consumers import OpsEventConsumer

websocket_urlpatterns = [
    path("ws/ops/", OpsEventConsumer.as_asgi()),
]
