import binascii
import os
import uuid

import tldextract
from django.contrib.auth import authenticate, get_user_model
from django.db import connection
from djoser.conf import settings
from djoser.serializers import TokenCreateSerializer, UserCreateSerializer

from .models import Organization, Workspace

User = get_user_model()


class CustomerUserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = "__all__"

    def generate_key(self):
        return binascii.hexlify(os.urandom(20)).decode()

    def update_token_for_dummy_user(self, user_id):
        with connection.cursor() as cursor:
            timestamp = "NOW()"
            token = self.generate_key()
            cursor.execute("INSERT INTO authtoken_token values (%s,%s,%s)", [token, timestamp, user_id])

    def create(self, validated_data):
        # validated_data["username"] = validated_data["email"]
        user = super().create(validated_data)
        if user:
            ext = tldextract.extract(user.email)
            organization = ext.domain + "." + ext.suffix

            org = Organization(name="Default Organization", id=uuid.uuid4())
            org.save()
            workspace = Workspace(name="Default Workspace", id=uuid.uuid4(), organization=org)
            workspace.save()
            user.save()
            user.organizations.add(org)

            # Create Access Token for Engine
            engineUser = User(
                email=f"{org.id}@{organization}",
                username=str(org.id),
                first_name="Engine User",
                last_name=str(org.id),
                is_active=True,
            )
            engineUser.set_password(self.generate_key())
            engineUser.save()
            self.update_token_for_dummy_user(engineUser.id)
        return user


class CustomTokenCreateSerializer(TokenCreateSerializer):
    def validate(self, attrs):
        password = attrs.get("password")
        params = {settings.LOGIN_FIELD: attrs.get(settings.LOGIN_FIELD)}
        self.user = authenticate(request=self.context.get("request"), **params, password=password)
        if not self.user:
            self.user = User.objects.filter(**params).first()
            if self.user and not self.user.check_password(password):
                self.fail("invalid_credentials")
        if self.user:  # and self.user.is_active:
            return attrs
        self.fail("invalid_credentials")
