from typing import List

from django.core import serializers
from django.http import HttpResponse
from ninja import Router

from core.schemas import (
    BaseSchemaIn,
    CredentialSchema,
    DestinationSchema,
    OrganizationSchema,
    SourceSchema,
    SyncSchema,
    UserSchemaOut,
)

from .models import Credential, Destination, Organization, Source, Sync, User, Workspace

router = Router()


@router.get("/organizations/", response=list[OrganizationSchema])
def list_organizations(request):
    queryset = Organization.objects.prefetch_related("workspace_set")
    return queryset


@router.get("/spaces/", response=UserSchemaOut)
def list_spaces(request):
    user_id = request.user.id
    queryset = User.objects.select_related("organizations").prefetch_related("organizations__workspaces")

    return queryset


@router.get("/syncs/", response=List[SyncSchema])
def list_syncs(request, data: BaseSchemaIn):
    workspace = Workspace.objects.get(id=data.workspace_id)
    syncs = Sync.objects.filter(workspace=workspace)
    queryset = syncs.select_related("source", "destination")
    return queryset


@router.get("/syncs/{sync_id}", response=SyncSchema)
def get_sync(request, sync_id):
    sync = Sync.objects.get(id=sync_id)
    qs_json = serializers.serialize("json", sync)
    return HttpResponse(qs_json, content_type="application/json")


@router.get("/credentials/", response=List[CredentialSchema])
def list_credentials(request, data: BaseSchemaIn):
    workspace = Workspace.objects.get(id=data.workspace_id)
    queryset = Credential.objects.filter(workspace=workspace)
    return queryset


@router.post("/credentials/create", response=CredentialSchema)
def create_credential(request, payload: CredentialSchema):
    data = payload.dict()
    try:
        credential = Credential.objects.create(**data)
        return {
            "detail": "Credential has been successfully created.",
            "id": credential.id,
        }
    except Exception:
        return {"detail": "The specific credential cannot be created."}


@router.get("/sources/", response=List[SourceSchema])
def list_sources(request, data: BaseSchemaIn):
    workspace = Workspace.objects.get(id=data.workspace_id)
    queryset = Source.objects.filter(workspace=workspace)
    return queryset


@router.post("/sources/create", response=SourceSchema)
def create_source(request, payload: SourceSchema):
    data = payload.dict()
    try:
        source = Source.objects.create(**data)
        return {
            "detail": "Source has been successfully created.",
            "id": source.id,
        }
    except Exception:
        return {"detail": "The specific source cannot be created."}


@router.post("/destinations/create", response=DestinationSchema)
def create_destination(request, payload: DestinationSchema):
    data = payload.dict()
    try:
        destination = Destination.objects.create(**data)
        return {
            "detail": "Destination has been successfully created.",
            "id": destination.id,
        }
    except Exception:
        return {"detail": "The specific Destination cannot be created."}


@router.get("/destinations/", response=List[DestinationSchema])
def list_definitions(request, data: BaseSchemaIn):
    workspace = Workspace.objects.get(id=data.workspace_id)
    queryset = Destination.objects.filter(workspace=workspace)
    return queryset


# @router.post("/credentials/create")
# def create_article(request, payload: Credential):
#     data = payload.dict()
#     try:
#         # author = Credential.objects.get(id=data["id"])
#         # del data["id"]
#         user = User.objects.get(id=data["user"])
#         credential = Credential.objects.create(credential=credential, **data)
#         return {
#             "detail": "Credential has been successfully created.",
#             "id": credential.id,
#         }
#     except User.DoesNotExist:
#         return {"detail": "The specific user cannot be found."}
