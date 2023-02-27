import uuid

from django.contrib.auth import authenticate, get_user_model
from djoser.conf import settings
from djoser.serializers import TokenCreateSerializer, UserCreateSerializer

from .models import Organization, Workspace

User = get_user_model()


class CustomerUserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = "__all__"

    def create(self, validated_data):
        # validated_data["username"] = validated_data["email"]
        user = super().create(validated_data)
        if user:
            # ext = tldextract.extract(self.user.email)
            # organization = ext.domain + "." + ext.suffix

            org = Organization(name="Default Organization", id=uuid.uuid4())
            org.save()
            workspace = Workspace(name="Default Workspace", id=uuid.uuid4(), organization=org)
            workspace.save()
            user.save()
            user.organizations.add(org)
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
