"""
Copyright (c) 2024 valmi.io <https://github.com/valmi-io>

Created Date: Wednesday, March 8th 2023, 9:56:52 pm
Author: Rajashekar Varkala @ valmi.io

"""

import uuid
from enum import Enum

from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone

# Create your models here.


class OAuthKeys(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]


class User(AbstractUser):
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    organizations = models.ManyToManyField(to="Organization", related_name="users", blank=True)
    meta = models.JSONField(default=dict)

    def __str__(self):
        return f"{self.email} - {self.first_name} {self.last_name} - {self.organizations.all()}"


User._meta.get_field("email")._unique = True
User._meta.get_field("email").blank = False
User._meta.get_field("email").null = False


class Organization(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=256, null=False, blank=False)
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
    status = models.CharField(max_length=256, null=False, blank=False, default="active")

    def __str__(self):
        return self.name


class Workspace(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=256, null=False, blank=False)
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
    organization = models.ForeignKey(to=Organization, on_delete=models.CASCADE, related_name="workspaces")
    status = models.CharField(max_length=256, null=False, blank=False, default="active")

    def __str__(self):
        return self.name


class Credential(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    connector = models.ForeignKey(to="Connector", on_delete=models.CASCADE, related_name="credentials")
    connector_config = models.JSONField(blank=False, null=False)
    workspace = models.ForeignKey(to=Workspace, on_delete=models.CASCADE, related_name="credentials")
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
    name = models.CharField(max_length=256, null=False, blank=False, default="DUMMY_CREDENTIAL_NAME")
    status = models.CharField(max_length=256, null=False, blank=False, default="active")
    account = models.ForeignKey(
        to="Account", on_delete=models.CASCADE, related_name="credentials", null=True, blank=True
    )

    def __str__(self):
        return f"{self.connector}: {self.connector_config} : {self.workspace}: {self.id} : {self.name}"
    

class StorageCredentials(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
    workspace = models.ForeignKey(to=Workspace, on_delete=models.CASCADE, related_name="storage_credentials")
    connector_config = models.JSONField(blank=False, null=False)

class Source(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=256, null=False, blank=False)
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
    catalog = models.JSONField(blank=False, null=False)
    workspace = models.ForeignKey(to=Workspace, on_delete=models.CASCADE, related_name="sources")
    credential = models.ForeignKey(to=Credential, on_delete=models.CASCADE, related_name="sources")
    status = models.CharField(max_length=256, null=False, blank=False, default="active")


class Destination(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=256, null=False, blank=False)
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
    catalog = models.JSONField(blank=False, null=False)
    workspace = models.ForeignKey(to=Workspace, on_delete=models.CASCADE, related_name="destinations")
    credential = models.ForeignKey(to=Credential, on_delete=models.CASCADE, related_name="destinations")
    status = models.CharField(max_length=256, null=False, blank=False, default="active")


class Sync(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=256, null=False, blank=False)
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
    source = models.ForeignKey(to=Source, on_delete=models.CASCADE, related_name="syncs")
    destination = models.ForeignKey(to=Destination, on_delete=models.CASCADE, related_name="syncs")
    workspace = models.ForeignKey(to=Workspace, on_delete=models.CASCADE, related_name="syncs")
    schedule = models.JSONField(blank=False, null=False)
    status = models.CharField(max_length=256, null=False, blank=False, default="active")
    ui_state = models.JSONField(blank=False, null=True)


class Connector(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    type = models.CharField(primary_key=True, max_length=64, null=False, blank=False, default="DUMMY_CONNECTOR")
    docker_image = models.CharField(max_length=128, null=False, blank=False, default="DUMMY_CONNECTOR_IMAGE_NAME")
    docker_tag = models.CharField(max_length=64, null=False, blank=False, default="DUMMY_CONNECTOR_TAG")
    display_name = models.CharField(max_length=128, null=False, blank=False, default="DUMMY_CONNECTOR_DISPLAY_NAME")
    status = models.CharField(max_length=256, null=False, blank=False, default="active")
    oauth = models.BooleanField(default=False)
    oauth_keys = models.CharField(max_length=64, choices=OAuthKeys.choices(), default=OAuthKeys.PRIVATE.value)
    mode = ArrayField(models.CharField(max_length=64), blank=True, default=list)


class Package(models.Model):
    name = models.CharField(primary_key=True,max_length=256, null=False, blank=False)
    scopes = ArrayField(models.CharField(max_length=64), blank=True, default=list)
    gated = models.BooleanField(null=False, blank = False, default=True)

class Prompt(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
    name = models.CharField(max_length=256, null=False, blank=False,unique=True)
    description = models.CharField(max_length=1000, null=False, blank=False,default="aaaaaa")
    type = models.CharField(null=False, blank = False,max_length=256, default="SRC_SHOPIFY")
    spec = models.JSONField(blank=False, null=True)
    query = models.CharField(max_length=1000,null=False, blank=False,default="query")
    package_id = models.CharField(null=False, blank = False,max_length=20,default="P0")
    gated = models.BooleanField(null=False, blank = False, default=True)

class SourceAccessInfo(models.Model):
    source = models.ForeignKey(to=Source, on_delete=models.CASCADE, related_name="source_access_info",primary_key=True)
    storage_credentials = models.ForeignKey(to=StorageCredentials,on_delete=models.CASCADE,related_name="source_access_info")

class Account(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
    name = models.CharField(max_length=256, null=False, blank=False)
    external_id = models.CharField(max_length=256, null=False, blank=False)
    profile = models.TextField(blank=False, null=True)
    meta_data = models.JSONField(blank=False, null=True)
    workspace = models.ForeignKey(to=Workspace, on_delete=models.CASCADE, related_name="accounts")


class Explore(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
    name = models.CharField(max_length=256, null=False, blank=False,default="aaaaaa")
    workspace = models.ForeignKey(to=Workspace, on_delete=models.CASCADE, related_name="explore_workspace")
    prompt = models.ForeignKey(to=Prompt, on_delete=models.CASCADE, related_name="explore_prompt")
    sync = models.ForeignKey(to=Sync, on_delete=models.CASCADE, related_name="explore_sync")
    ready = models.BooleanField(null=False, blank = False, default=False)
    account = models.ForeignKey(to=Account, on_delete=models.CASCADE, related_name="explore_account")
    spreadsheet_url = models.URLField(null=True, blank=True, default="https://example.com")

class ValmiUserIDJitsuApiToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    api_token = models.CharField(max_length=256, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class OAuthApiKeys(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    workspace = models.ForeignKey(to=Workspace, on_delete=models.CASCADE, related_name="oauth_api_keys")
    type = models.CharField(max_length=64, null=True, blank=True, default="DUMMY_CONNECTOR")
    oauth_config = models.JSONField(blank=False, null=True)

    class Meta:
        db_table = 'core_oauth_api_keys'
        constraints = [
            models.UniqueConstraint(fields=['workspace', 'type'], name='unique_oauth_keys')
        ]
