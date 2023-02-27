from ninja import ModelSchema

from valmi_app_backend.models import Credential


def to_camel(string: str) -> str:
    return "".join(word.capitalize() for word in string.split("_"))


class CredentialSchema(ModelSchema):
    class Config:
        alias_generator = to_camel
        model = Credential
        model_fields = "__all__"
