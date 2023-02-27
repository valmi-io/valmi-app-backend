import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.


class User(AbstractUser):
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    organizations = models.ManyToManyField(to="Organization", related_name="users", blank=True)

    pass


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
    organization = models.ForeignKey(to=Organization, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Credential(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    connector_type = models.CharField(max_length=64, null=False, blank=False)
    connector_config = models.JSONField(blank=False, null=False)
    workspace = models.ForeignKey(to=Workspace, on_delete=models.CASCADE)
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))

    def __str__(self):
        return f"{self.author.connector_type}: {self.connector_config}"


class Source(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=256, null=False, blank=False)
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
    catalog = models.JSONField(blank=False, null=False)
    workspace = models.ForeignKey(to=Workspace, on_delete=models.CASCADE)
    credential = models.ForeignKey(to=Credential, on_delete=models.CASCADE)


class Destination(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=256, null=False, blank=False)
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
    catalog = models.JSONField(blank=False, null=False)
    workspace = models.ForeignKey(to=Workspace, on_delete=models.CASCADE)
    credential = models.ForeignKey(to=Credential, on_delete=models.CASCADE)


class Sync(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=256, null=False, blank=False)
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
    source = models.ForeignKey(to=Source, on_delete=models.CASCADE)
    destination = models.ForeignKey(to=Destination, on_delete=models.CASCADE)
    workspace = models.ForeignKey(to=Workspace, on_delete=models.CASCADE)
    schedule = models.JSONField(blank=False, null=False)
