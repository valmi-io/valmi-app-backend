from ninja import Router, Schema
from rest_framework.authtoken.models import Token
from core.schemas import SocialAuthLoginSchema
from core.models import User, Organization, Workspace, OAuthApiKeys
import binascii
import os
import uuid
router = Router()

class AuthToken(Schema):
    auth_token: str

#TODO took from serializaer. move to utils
def generate_key():
    return binascii.hexlify(os.urandom(20)).decode()


#TODO response for bad request, 400
@router.post("/login", response = {200:AuthToken})
def login(request, req: SocialAuthLoginSchema):
    email = req.user.email
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        user = User()
        user.email = req.user.email
        user.username = req.user.name
        user.password =  generate_key()
        user.save(force_insert=True)
        org = Organization(name="Default Organization", id=uuid.uuid4())
        org.save()
        workspace = Workspace(name="Default Workspace", id=uuid.uuid4(), organization=org)
        workspace.save()
        user.save()
        user.organizations.add(org)
        oauth = OAuthApiKeys(workspace=workspace, type = 'GOOGLE_LOGIN',id = uuid.uuid4())
        oauth.oauth_config = {
            "access_token": req.account.access_token,
            "refresh_token": req.account.refresh_token,
            "expires_at": req.account.expires_at 
        }
        oauth.save()
    token, _ = Token.objects.get_or_create(user=user)
    return {"auth_token": token.key}
