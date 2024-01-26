"""
Copyright (c) 2024 valmi.io <https://github.com/valmi-io>

Created Date: Wednesday, March 8th 2023, 9:56:52 pm
Author: Rajashekar Varkala @ valmi.io

"""

import binascii
import os
import uuid

from django.contrib.auth import authenticate, get_user_model
from django.db import connection, transaction
from djoser.serializers import TokenCreateSerializer, UserCreateSerializer
from decouple import config
from djoser.conf import settings

from .models import Organization, Workspace, ValmiUserIDJitsuApiToken
import hashlib

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

    def patch_jitsu_user(self, user, workspace):
        jitsu_defaultSeed = "dea42a58-acf4-45af-85bb-e77e94bd5025"
        with connection.cursor() as cursor:
            with transaction.atomic():
                cursor.execute('INSERT INTO "jitsu"."Workspace" ( id, name ) VALUES ( %s, %s ) ',
                               [str(workspace.id), workspace.name])
                cursor.execute('INSERT INTO "jitsu"."UserProfile" (id, name, email, "loginProvider", "externalId") VALUES (%s, %s, %s, %s, %s) ',
                               [str(user.id), user.username, user.email, "valmi", str(user.id)])
                cursor.execute('INSERT INTO "jitsu"."WorkspaceAccess" ("workspaceId", "userId") VALUES ( %s, %s) ',
                               [str(workspace.id), str(user.id)])
                apiKeyId = self.generate_key()
                apiKeySecret = self.generate_key()
                randomSeed = self.generate_key()
                hash = randomSeed + "." + hashlib.sha512((apiKeySecret + randomSeed + jitsu_defaultSeed).encode('utf-8')).hexdigest()
                cursor.execute('INSERT INTO "jitsu"."UserApiToken" (id, hint, hash, "userId") VALUES ( %s, %s, %s, %s)',
                               [apiKeyId, apiKeySecret[0:3] + '*' + apiKeySecret[-3:], hash, str(user.id)])

                # store jitsu apitoken for valmi user
                ValmiUserIDJitsuApiToken.objects.create(user=user, api_token=apiKeyId + ":" + apiKeySecret)

    def create(self, validated_data):
        # validated_data["username"] = validated_data["email"]
        user = super().create(validated_data)
        if user:
            org = Organization(name="Default Organization", id=uuid.uuid4())
            org.save()
            workspace = Workspace(name="Default Workspace", id=uuid.uuid4(), organization=org)
            workspace.save()
            user.save()
            user.organizations.add(org)

            if config("ENABLE_JITSU", default=False, cast=bool):
                self.patch_jitsu_user(user, workspace)

            """
            ext = tldextract.extract(user.email)
            organization = ext.domain + "." + ext.suffix
            # Create Access Token for Engine :: TODO: User Exisiting Organization if available
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
            """
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
