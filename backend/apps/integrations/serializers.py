from rest_framework import serializers

from .crypto import encrypt_secrets
from .models import Connector, Credential


class ConnectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Connector
        fields = (
            "id",
            "organization",
            "name",
            "slug",
            "kind",
            "description",
            "config_schema",
            "is_system",
            "is_active",
        )


class CredentialSerializer(serializers.ModelSerializer):
    secrets = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model = Credential
        fields = (
            "id",
            "organization",
            "connector",
            "name",
            "metadata",
            "expires_at",
            "created_at",
            "secrets",
        )
        read_only_fields = ("id", "created_at")

    def create(self, validated_data):
        secrets = validated_data.pop("secrets", {})
        validated_data["encrypted_secrets"] = encrypt_secrets(secrets)
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)
