
import json
import logging
import os
import uuid
from urllib.parse import urlparse
import psycopg2
from ninja import Router
from pydantic import Json
from rest_framework.authtoken.models import Token

from core.models import Organization, User, Workspace
from core.schemas.schemas import DetailSchema, SocialAuthLoginSchema
from core.services.user import UserService


router = Router()


logger = logging.getLogger(__name__)


# TODO took from serializaer. move to utils


# TODO response for bad request, 400
@router.post("/login", response={200: Json, 400: DetailSchema})
def login(request, payload: SocialAuthLoginSchema):

    req = payload.dict()

    user_data = req["user"]

    account = req["account"]

    email = user_data["email"]
    try:
        user = User.objects.get(email=email)
        result = urlparse(os.environ["DATABASE_URL"])
        username = result.username
        password = result.password
        database = result.path[1:]
        hostname = result.hostname
        port = result.port
        conn = psycopg2.connect(user=username, password=password, host=hostname, port=port, database=database)
        cursor = conn.cursor()
        query = ("select organization_id from core_user_organizations where user_id = {user_id}").format(
            user_id=user.id)
        cursor.execute(query)
        result = cursor.fetchone()
        logger.debug(result)
        conn.close()
        workspace = Workspace.objects.get(organization_id=result)
        workspace_id = workspace.id
        # this below function creates oauth token if not exists for an existing user else updates , creates new jitsu token if not exists
        UserService.manage_oauth_and_jitsu_tokens(user, account, workspace)
        # this below function creates channel topics for chatbot if not exists for an existing user
        UserService.create_channel_topics(request, user, workspace_id)
    except User.DoesNotExist:
        user = User()
        user.email = user_data["email"]
        user.username = user_data["name"]
        user.meta = user_data['meta']
        user.password = UserService.generate_key()
        user.save(force_insert=True)
        org = Organization(name=f"{user.username} Organization", id=uuid.uuid4())
        org.save()
        workspace = Workspace(name=f"{user.username} Workspace", id=uuid.uuid4(), organization=org)
        workspace.save()
        user.save()
        user.organizations.add(org)
        # this below function creates oauth token for an new user else updates if user exists, creates new jitsu token if not exists
        UserService.manage_oauth_and_jitsu_tokens(user, account, workspace)
        # create the channle topics for new users
        UserService.create_channel_topics(request, user, workspace.id)

    token, _ = Token.objects.get_or_create(user=user)
    user_id = user.id
    try:
        user = User.objects.get(id=user.id)
        user_id = user.id
        orgnizations_workspaces = User.objects.prefetch_related('organizations__workspaces').get(id=user_id)
        organizations = []
        for organization in orgnizations_workspaces.organizations.all():
            workspaces = []
            for workspace in organization.workspaces.all():
                workspace_data = {
                    "created_at": workspace.created_at.isoformat(),
                    "updated_at": workspace.updated_at.isoformat(),
                    "name": workspace.name,
                    "id": str(workspace.id),
                    "organization": str(workspace.organization.id),
                    "status": workspace.status
                }
                workspaces.append(workspace_data)
            org_data = {
                "created_at": organization.created_at.isoformat(),
                "updated_at": organization.updated_at.isoformat(),
                "name": organization.name,
                "id": str(organization.id),
                "status": organization.status,
                "workspaces": workspaces
            }

            organizations.append(org_data)

        response = {
            "auth_token": token.key,
            "organizations": organizations
        }
        logger.debug(response)
        return json.dumps(response)
    except Exception as e:
        return (400, {"detail": e.message})
