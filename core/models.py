import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.


class User(AbstractUser):
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    organizations = models.ManyToManyField(to="Organization", related_name="users", blank=True)

    def __str__(self):
        return f"{self.email} - {self.first_name} {self.last_name} - {self.organizations.all()}"


User._meta.get_field("email")._unique = True
User._meta.get_field("email").blank = False
User._meta.get_field("email").null = False
User = get_user_model()


class Organization(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=256, null=False, blank=False)
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))

    def __str__(self):
        return self.name


class Workspace(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=256, null=False, blank=False)
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
    organization = models.ForeignKey(to=Organization, on_delete=models.CASCADE, related_name="workspaces")

    def __str__(self):
        return self.name


class Credential(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    connector = models.ForeignKey(to="Connector", on_delete=models.CASCADE, related_name="credentials")
    connector_config = models.JSONField(blank=False, null=False)
    workspace = models.ForeignKey(to=Workspace, on_delete=models.CASCADE, related_name="credentials")
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))

    def __str__(self):
        return f"{self.connector}: {self.connector_config} : {self.workspace}: {self.id}"


class Source(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=256, null=False, blank=False)
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
    catalog = models.JSONField(blank=False, null=False)
    workspace = models.ForeignKey(to=Workspace, on_delete=models.CASCADE, related_name="sources")
    credential = models.ForeignKey(to=Credential, on_delete=models.CASCADE, related_name="sources")


class Destination(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=256, null=False, blank=False)
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
    catalog = models.JSONField(blank=False, null=False)
    workspace = models.ForeignKey(to=Workspace, on_delete=models.CASCADE, related_name="destinations")
    credential = models.ForeignKey(to=Credential, on_delete=models.CASCADE, related_name="destinations")


class Sync(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=256, null=False, blank=False)
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
    source_id = models.ForeignKey(to=Source, on_delete=models.CASCADE, related_name="syncs")
    destination = models.ForeignKey(to=Destination, on_delete=models.CASCADE, related_name="syncs")
    workspace = models.ForeignKey(to=Workspace, on_delete=models.CASCADE, related_name="syncs")
    schedule = models.JSONField(blank=False, null=False)


class Connector(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    type = models.CharField(primary_key=True, max_length=16, null=False, blank=False, default="DUMMY_CONNECTOR")
