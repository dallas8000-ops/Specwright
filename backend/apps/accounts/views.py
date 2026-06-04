from rest_framework import generics, permissions
from rest_framework.response import Response

from .serializers import RegisterSerializer, UserSerializer
from .workspace import get_workspace_for_user


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        data = UserSerializer(user).data
        data["workspace"] = get_workspace_for_user(user)
        return Response(data)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class CurrentUserMixin:
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user
        return context
