import logging
import uuid
from typing import Dict, List
from ninja import Router
from pydantic import Json
from decouple import config
import requests
from core.schemas import (
    ConnectorConfigSchemaIn,
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
    SuccessSchema,
    FailureSchema,
    SyncIdSchema,
)

from .models import Connector, Credential, Destination, Source, Sync, User, Workspace

router = Router()

CONNECTOR_PREFIX_URL = config("ACTIVATION_SERVER") + "/connectors"
ACTIVE = "active"
INACTIVE = "inactive"
DELETED = "deleted"

LONG_TIMEOUT = 60
SHORT_TIMEOUT = 10

# Get an instance of a logger
logger = logging.getLogger(__name__)


@router.get("/spaces/", response=UserSchemaOut)
def list_spaces(request):
    user_id = request.user.id
    queryset = User.objects.prefetch_related("organizations").get(id=user_id)
    logger.debug(queryset)
    return queryset


@router.get("/workspaces/{workspace_id}/connectors/{connector_type}/spec", response=Json)
def connector_spec(request, workspace_id, connector_type):
    workspace = Workspace.objects.get(id=workspace_id)
    connector = Connector.objects.get(type=connector_type)

    return requests.post(
        f"{CONNECTOR_PREFIX_URL}/{connector.type}/spec",
        json={"docker_image": connector.docker_image, "docker_tag": connector.docker_tag},
        timeout=SHORT_TIMEOUT,
    ).text


@router.post("/workspaces/{workspace_id}/connectors/{connector_type}/check", response=Dict)
def connector_check(request, workspace_id, connector_type, payload: ConnectorConfigSchemaIn):
    workspace = Workspace.objects.get(id=workspace_id)
    connector = Connector.objects.get(type=connector_type)

    return requests.post(
        f"{CONNECTOR_PREFIX_URL}/{connector.type}/check",
        json={**payload.dict(), "docker_image": connector.docker_image, "docker_tag": connector.docker_tag},
        timeout=SHORT_TIMEOUT,
    ).json()


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


@router.post("/workspaces/{workspace_id}/syncs/enable", response={200: SuccessSchema, 502: FailureSchema})
def enable_sync(request, workspace_id, payload: SyncIdSchema):
    try:
        sync_id = payload.sync_id
        sync = Sync.objects.get(id=sync_id)
        sync.status = ACTIVE
        sync.save()
        return (200, SuccessSchema())
    except Exception:
        logger.exception("delete operation failed")
        return (502, FailureSchema())


@router.post("/workspaces/{workspace_id}/syncs/disable", response={200: SuccessSchema, 502: FailureSchema})
def disable_sync(request, workspace_id, payload: SyncIdSchema):
    try:
        sync_id = payload.sync_id
        sync = Sync.objects.get(id=sync_id)
        sync.status = INACTIVE
        sync.save()
        return (200, SuccessSchema())
    except Exception:
        logger.exception("delete operation failed")
        return (502, FailureSchema())


@router.delete("/workspaces/{workspace_id}/syncs/delete", response={200: SuccessSchema, 502: FailureSchema})
def delete_sync(request, workspace_id, payload: SyncIdSchema):
    try:
        sync_id = payload.sync_id
        sync = Sync.objects.get(id=sync_id)
        sync.status = DELETED
        sync.save()
        return (200, SuccessSchema())
    except Exception:
        logger.exception("delete operation failed")
        return (502, FailureSchema())


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


@router.get("/connectors/", response={200: Dict[str, List[ConnectorSchema]], 400: DetailSchema})
def create_connector(request):
    # check for admin permissions
    try:
        logger.debug("listing connectors")
        connectors = Connector.objects.all()
        src_dst_dict: Dict[str, List[ConnectorSchema]] = {}
        src_dst_dict["SRC"] = []
        src_dst_dict["DEST"] = []
        for conn in connectors:
            arr = conn.type.split("_")
            if arr[0] == "SRC":
                src_dst_dict["SRC"].append(conn)
            elif arr[0] == "DEST":
                src_dst_dict["DEST"].append(conn)
        return src_dst_dict
    except Exception:
        logger.exception("connector listing error")
        return (400, {"detail": "The list of connectors cannot be fetched."})
