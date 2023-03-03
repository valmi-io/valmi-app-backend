import logging
import uuid
from typing import List

from ninja import Router

from core.schemas import (
    ConnectorSchema,
    CredentialSchema,
    CredentialSchemaIn,
    DestinationSchema,
    DestinationSchemaIn,
    DetailSchema,
    SourceSchema,
    SourceSchemaIn,
    SyncSchema,
    SyncSchemaIn,
    UserSchemaOut,
)

from .models import Connector, Credential, Destination, Source, Sync, User, Workspace

router = Router()


# Get an instance of a logger
logger = logging.getLogger(__name__)


@router.get("/spaces/", response=UserSchemaOut)
def list_spaces(request):
    user_id = request.user.id
    queryset = User.objects.prefetch_related("organizations").get(id=user_id)
    logger.debug(queryset)
    return queryset


@router.get("/workspaces/{workspace_id}/credentials/", response=List[CredentialSchema])
def list_credentials(request, workspace_id):
    workspace = Workspace.objects.get(id=workspace_id)
    queryset = Credential.objects.filter(workspace=workspace)
    return queryset


@router.post("/workspaces/{workspace_id}/credentials/create", response={200: CredentialSchema, 400: DetailSchema})
def create_credential(request, workspace_id, payload: CredentialSchemaIn):
    data = payload.dict()
    try:
        logger.debug(data)
        data["id"] = uuid.uuid4()
        data["workspace"] = Workspace.objects.get(id=workspace_id)
        data["connector"] = Connector.objects.get(type=data["connector_type"])
        del data["connector_type"]

        credential = Credential.objects.create(**data)
        return credential
    except Exception:
        logger.exception("Credential error")
        return {"detail": "The specific credential cannot be created."}


@router.get("/workspaces/{workspace_id}/sources/", response=List[SourceSchema])
def list_sources(request, workspace_id):
    workspace = Workspace.objects.get(id=workspace_id)
    queryset = Source.objects.filter(workspace=workspace)
    return queryset


@router.post("/workspaces/{workspace_id}/sources/create", response={200: SourceSchema, 400: DetailSchema})
def create_source(request, workspace_id, payload: SourceSchemaIn):
    data = payload.dict()
    logger.debug(dict)
    try:
        data["id"] = uuid.uuid4()
        data["workspace"] = Workspace.objects.get(id=workspace_id)
        data["credential"] = Credential.objects.get(id=payload.credential_id)
        del data["credential_id"]
        source = Source.objects.create(**data)
        return source
    except Exception:
        return {"detail": "The specific source cannot be created."}


@router.get("/workspaces/{workspace_id}/destinations/", response=List[DestinationSchema])
def list_definitions(request, workspace_id):
    workspace = Workspace.objects.get(id=workspace_id)
    queryset = Destination.objects.filter(workspace=workspace)
    return queryset


@router.post("/workspaces/{workspace_id}/destinations/create", response={200: DestinationSchema, 400: DetailSchema})
def create_destination(request, workspace_id, payload: DestinationSchemaIn):
    data = payload.dict()
    logger.debug(dict)
    try:
        data["id"] = uuid.uuid4()
        data["workspace"] = Workspace.objects.get(id=workspace_id)
        data["credential"] = Credential.objects.get(id=payload.credential_id)
        del data["credential_id"]
        destination = Destination.objects.create(**data)
        return destination
    except Exception:
        return {"detail": "The specific destination cannot be created."}


@router.post("/workspaces/{workspace_id}/syncs/create", response={200: SyncSchema, 400: DetailSchema})
def create_sync(request, workspace_id, payload: SyncSchemaIn):
    data = payload.dict()
    try:
        logger.debug(dict)
        logger.debug(payload.source_id)
        logger.debug(payload.destination_id)
        data["id"] = uuid.uuid4()
        data["workspace"] = Workspace.objects.get(id=workspace_id)
        data["source"] = Source.objects.get(id=payload.source_id)
        data["destination"] = Destination.objects.get(id=payload.destination_id)

        del data["source_id"]
        del data["destination_id"]
        logger.debug(data["schedule"])
        sync = Sync.objects.create(**data)
        return sync
    except Exception:
        logger.exception("Sync error")
        return {"detail": "The specific sync cannot be created."}


@router.get("/workspaces/{workspace_id}/syncs/", response=List[SyncSchema])
def list_syncs(request, workspace_id):
    # use request.user_id to check access control in the middleware
    workspace = Workspace.objects.get(id=workspace_id)
    syncs = Sync.objects.filter(workspace=workspace)
    queryset = syncs.select_related("source", "destination")
    for e in queryset:
        logger.info(e)
    return queryset


@router.get("/workspaces/{workspace_id}/syncs/{sync_id}", response=SyncSchema)
def get_sync(request, workspace_id, sync_id):
    sync = Sync.objects.get(id=sync_id)
    return sync


################################# ADMIN API #######################


@router.get("/syncs/", response={200: List[SyncSchema], 400: DetailSchema})
def get_all_syncs(request):
    # check for admin permissions
    try:
        syncs = Sync.objects.select_related("source", "destination")
        return syncs
    except Exception:
        logger.exception("syncs all error")
        return (400, {"detail": "The syncs cannot be fetched."})


@router.post("/connectors/create", response={200: ConnectorSchema, 400: DetailSchema})
def create_connector(request, payload: ConnectorSchema):
    # check for admin permissions
    data = payload.dict()
    try:
        logger.debug("creating connector")
        connector = Connector.objects.create(**data)

        return (200, connector)
    except Exception:
        logger.exception("Connector error")
        return (400, {"detail": "The specific connector cannot be created."})
