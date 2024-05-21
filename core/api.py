"""
Copyright (c) 2024 valmi.io <https://github.com/valmi-io>

Created Date: Wednesday, March 8th 2023, 9:56:52 pm
Author: Rajashekar Varkala @ valmi.io

"""

import json
import logging
import time
import uuid
import uuid
from datetime import datetime
from typing import Dict, List, Optional
import requests
from decouple import Csv, config
from ninja import Router
from pydantic import UUID4, Json
from core.schemas.schemas import (
    ConnectionSchemaIn,
    ConnectorConfigSchemaIn,
    ConnectorSchema,
    CredentialSchema,
    CredentialSchemaIn,
    CredentialSchemaUpdateIn,
    DestinationSchema,
    DestinationSchemaIn,
    DetailSchema,
    FailureSchema,
    SourceSchema,
    SourceSchemaIn,
    SuccessSchema,
    SyncIdSchema,
    SyncSchema,
    SyncSchemaIn,
    SyncSchemaInWithSourcePayload,
    SyncSchemaUpdateIn,
    SyncStartStopSchemaIn,
    UserSchemaOut,
    CreateConfigSchemaIn
)
from core.services.warehouse_credentials import DefaultWarehouse
from .models import Account, Connector, Credential, Destination, Source, SourceAccessInfo, StorageCredentials, Sync, User, Workspace, OAuthApiKeys
from valmi_app_backend.utils import replace_values_in_json
router = Router()

CONNECTOR_PREFIX_URL = config("ACTIVATION_SERVER") + "/connectors"
ACTIVATION_URL = config("ACTIVATION_SERVER")
ACTIVE = "active"
INACTIVE = "inactive"
DELETED = "deleted"

LONG_TIMEOUT = 60
SHORT_TIMEOUT = 60

# Get an instance of a logger
logger = logging.getLogger(__name__)


def get_workspaces(user):
    queryset = User.objects.prefetch_related("organizations").get(id=user.id)
    for organization in queryset.organizations.all():
        for workspace in organization.workspaces.all():
            yield workspace


@router.get("/spaces/", response=UserSchemaOut)
def list_spaces(request):
    user_id = request.user.id
    queryset = User.objects.prefetch_related("organizations").get(id=user_id)
    logger.debug(queryset)
    return queryset


@router.get("/workspaces/{workspace_id}/connectors/{connector_type}/spec", response=Json)
def connector_spec(request, workspace_id, connector_type):
    # workspace = Workspace.objects.get(id=workspace_id)
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

    queryset = OAuthApiKeys.objects.filter(workspace=workspace, type=connector_type)

    if queryset.exists():
        keys = queryset.first()

        logger.debug("connector spec keys:-", keys)
        # Replacing oauth keys with db values
        payload.config = replace_values_in_json(payload.config, keys.oauth_config)

    else:
        # Replacing oauth keys with .env values
        oauth_proxy_keys = config("OAUTH_SECRETS", default="", cast=Csv(str))
        if len(oauth_proxy_keys) > 0:
            config_str = json.dumps(payload.config)
            for key in oauth_proxy_keys:
                config_str = config_str.replace(key, config(key))
            payload.config = json.loads(config_str)

    return requests.post(
        f"{CONNECTOR_PREFIX_URL}/{connector.type}/check",
        json={**payload.dict(), "docker_image": connector.docker_image, "docker_tag": connector.docker_tag},
        timeout=SHORT_TIMEOUT,
    ).json()


@router.post("/workspaces/{workspace_id}/connectors/{connector_type}/discover", response=Dict)
def connector_discover(request, workspace_id, connector_type, payload: ConnectorConfigSchemaIn):
    workspace = Workspace.objects.get(id=workspace_id)
    connector = Connector.objects.get(type=connector_type)

    queryset = OAuthApiKeys.objects.filter(workspace=workspace, type=connector_type)

    if queryset.exists():
        keys = queryset.first()

        # Replacing oauth keys with db values
        payload.config = replace_values_in_json(payload.config, keys.oauth_config)

    else:
        # Replacing oauth keys with .env values
        oauth_proxy_keys = config("OAUTH_SECRETS", default="", cast=Csv(str))
        if len(oauth_proxy_keys) > 0:
            config_str = json.dumps(payload.config)
            for key in oauth_proxy_keys:
                config_str = config_str.replace(key, config(key))
            payload.config = json.loads(config_str)

    return requests.post(
        f"{CONNECTOR_PREFIX_URL}/{connector.type}/discover",
        json={**payload.dict(), "docker_image": connector.docker_image, "docker_tag": connector.docker_tag},
        timeout=SHORT_TIMEOUT,
    ).json()


@router.post("/workspaces/{workspace_id}/connectors/{connector_type}/create", response=Dict)
def connector_create(request, workspace_id, connector_type, payload: CreateConfigSchemaIn):
    workspace = Workspace.objects.get(id=workspace_id)
    connector = Connector.objects.get(type=connector_type)
    queryset = OAuthApiKeys.objects.filter(workspace=workspace, type=connector_type)
    if queryset.exists():
        keys = queryset.first()

        logger.debug("connector spec keys:-", keys)
        # Replacing oauth keys with db values
        payload.config = replace_values_in_json(payload.config, keys.oauth_config)

    else:
        # Replacing oauth keys with .env values
        oauth_proxy_keys = config("OAUTH_SECRETS", default="", cast=Csv(str))
        if len(oauth_proxy_keys) > 0:
            config_str = json.dumps(payload.config)
            for key in oauth_proxy_keys:
                config_str = config_str.replace(key, config(key))
            payload.config = json.loads(config_str)

    res = requests.post(
        f"{CONNECTOR_PREFIX_URL}/{connector.type}/create",
        json={**payload.dict(), "docker_image": connector.docker_image, "docker_tag": connector.docker_tag},
        timeout=SHORT_TIMEOUT,
    ).json()
    return res


@router.get("/workspaces/{workspace_id}/credentials/", response=List[CredentialSchema])
def list_credentials(request, workspace_id):
    workspace = Workspace.objects.get(id=workspace_id)
    queryset = Credential.objects.filter(workspace=workspace).order_by("-created_at")
    return queryset


@router.post("/workspaces/{workspace_id}/credentials/create", response={200: CredentialSchema, 400: DetailSchema})
def create_credential(request, workspace_id, payload: CredentialSchemaIn):
    data = payload.dict()
    try:
        logger.debug(data)
        logger.debug(workspace_id)
        source = data.get("connector_type")
        data["id"] = uuid.uuid4()
        data["workspace"] = Workspace.objects.get(id=workspace_id)
        data["connector"] = Connector.objects.get(type=data.pop("connector_type"))

        account_info = data.pop("account", None)
        if account_info and len(account_info) > 0:
            account_info["id"] = uuid.uuid4()
            account_info["workspace"] = data["workspace"]
            data["account"] = Account.objects.create(**account_info)

        credential = Credential.objects.create(**data)
        return credential
    except Exception:
        logger.exception("Credential error")
        return {"detail": "The specific credential cannot be created."}


@router.post("/workspaces/{workspace_id}/connection/DefaultWarehouse", response={200: SuccessSchema, 400: DetailSchema})
def create_connection_with_default_warehouse(request, workspace_id, payload: ConnectionSchemaIn):
    data = payload.dict()
    try:
        source_credential_payload = CredentialSchemaIn(
            name=data["name"], account=data["account"], connector_type=data["source_connector_type"], connector_config=data["source_connector_config"])
        source_credential = create_credential(request, workspace_id, source_credential_payload)
        source_payload = SourceSchemaIn(name="shopify", credential_id=source_credential.id,
                                        catalog=data["source_catalog"])
        source = create_source(request, workspace_id, source_payload)
        workspace = Workspace.objects.get(id=workspace_id)
        storage_credentials = DefaultWarehouse.create(workspace)
        source_access_info = {"source": source, "storage_credentials": storage_credentials}
        SourceAccessInfo.objects.create(**source_access_info)
        destination_credential_payload = CredentialSchemaIn(
            name="default warehouse", account=data["account"], connector_type="DEST_POSTGRES-DEST", connector_config=storage_credentials.connector_config)
        destination_credential = create_credential(request, workspace_id, destination_credential_payload)
        destination_payload = DestinationSchemaIn(
            name="default warehouse", credential_id=destination_credential.id, catalog=data["destination_catalog"])
        destination = create_destination(request, workspace_id, destination_payload)
        sync_payload = SyncSchemaIn(name="shopify to default warehouse", source_id=source.id,
                                    destination_id=destination.id, schedule=data["schedule"])
        sync = create_sync(request, workspace_id, sync_payload)
        run_payload = SyncStartStopSchemaIn(full_refresh=True)
        time.sleep(6)
        response = create_new_run(request, workspace_id, sync.id, run_payload)
        logger.debug(response)
        return "starting sync from shopify to default warehouse"
    except Exception as e:
        logger.exception(e)
        return {"detail": "The specific connection cannot be created."}


@router.get("/workspaces/{workspace_id}/storage-credentials", response={200: Json, 400: DetailSchema})
def storage_credentials(request, workspace_id):
    config = {}
    logger.info("came here in storeage")
    try:
        creds = StorageCredentials.objects.get(workspace_id=workspace_id)
        config['username'] = creds.connector_config["username"]
        config['password'] = creds.connector_config["password"]
        config["namespace"] = creds.connector_config["namespace"]
        config["schema"] = creds.connector_config["schema"]
        config['database'] = "dvdrental"
        config['host'] = "classspace.in"
        config['port'] = 5432
        config["ssl"] = False
    except StorageCredentials.DoesNotExist:
        return {"detail": "The specific credential cannot be found."}
    return json.dumps(config)


@router.post("/workspaces/{workspace_id}/credentials/update", response={200: CredentialSchema, 400: DetailSchema})
def update_credential(request, workspace_id, payload: CredentialSchemaUpdateIn):
    data = payload.dict()
    try:
        logger.debug(data)
        credential = Credential.objects.filter(id=data.pop("id"))
        data["workspace"] = Workspace.objects.get(id=workspace_id)
        data["connector"] = Connector.objects.get(type=data.pop("connector_type"))
        account_info = data.pop("account", None)
        if account_info and len(account_info) > 0:
            account = Account.objects.filter(id=account_info.pop("id"))
            account.update(**account_info)
            account = account.first()
            data["account"] = account
        else:
            data["account"] = None

        credential.update(**data)
        return credential.first()
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
    logger.debug("Creating source")
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
        data["source"] = Source.objects.get(id=data["source_id"])
        data["destination"] = Destination.objects.get(id=data["destination_id"])
        del data["source_id"]
        del data["destination_id"]
        schedule = {}
        if len(data["schedule"]) == 0:
            schedule["run_interval"] = 3600000
            data["schedule"] = schedule
        data["workspace"] = Workspace.objects.get(id=workspace_id)
        data["id"] = uuid.uuid4()
        logger.debug(data)
        sync = Sync.objects.create(**data)
        return sync
    except Exception:
        logger.exception("Sync error")
        return {"detail": "The specific sync cannot be created."}


@router.post("/workspaces/{workspace_id}/syncs/create_with_defaults", response={200: SyncSchema, 400: DetailSchema})
def create_sync(request, workspace_id, payload: SyncSchemaInWithSourcePayload):
    data = payload.dict()
    source_config = data["source"]["config"]
    catalog = data["source"]["catalog"]
    for stream in catalog["streams"]:
        primary_key = [["id"]]
        stream["primary_key"] = primary_key
        stream["destination_sync_mode"] = "append_dedup"
    # creating source credential
    source_credential_payload = CredentialSchemaIn(
        name=source_config["name"], account=data["account"], connector_type=source_config["source_connector_type"],
        connector_config=source_config["source_connector_config"])
    source_credential = create_credential(request, workspace_id, source_credential_payload)
    # creating source
    source_payload = SourceSchemaIn(
        name="shopify", credential_id=source_credential.id, catalog=catalog)
    source = create_source(request, workspace_id, source_payload)
    workspace = Workspace.objects.get(id=workspace_id)
    # creating default warehouse
    storage_credentials = DefaultWarehouse.create(workspace)
    source_access_info = {"source": source, "storage_credentials": storage_credentials}
    SourceAccessInfo.objects.create(**source_access_info)
    # creating destination credential
    destination_credential_payload = CredentialSchemaIn(
        name="default warehouse", account=data["account"], connector_type="DEST_POSTGRES-DEST", connector_config=storage_credentials.connector_config)
    destination_credential = create_credential(request, workspace_id, destination_credential_payload)
    # creating destination
    destination_payload = DestinationSchemaIn(
        name="default warehouse", credential_id=destination_credential.id, catalog=catalog)
    destination = create_destination(request, workspace_id, destination_payload)
    data["source"] = Source.objects.get(id=source.id)
    data["destination"] = Destination.objects.get(id=destination.id)
    del data["account"]
    schedule = {}
    if len(data["schedule"]) == 0:
        schedule["run_interval"] = 3600000
        data["schedule"] = schedule
    data["workspace"] = Workspace.objects.get(id=workspace_id)
    data["id"] = uuid.uuid4()
    logger.debug(data)
    sync = Sync.objects.create(**data)
    return sync


@router.post("/workspaces/{workspace_id}/syncs/update", response={200: SyncSchema, 400: DetailSchema})
def update_sync(request, workspace_id, payload: SyncSchemaUpdateIn):
    data = payload.dict()
    try:
        logger.debug(dict)
        logger.debug(payload.source_id)
        logger.debug(payload.destination_id)
        sync = Sync.objects.filter(id=data.pop("id"))
        data["workspace"] = Workspace.objects.get(id=workspace_id)
        data["source"] = Source.objects.get(id=payload.source_id)
        data["destination"] = Destination.objects.get(id=payload.destination_id)

        del data["source_id"]
        del data["destination_id"]
        logger.debug(data["schedule"])

        sync.update(**data)
        return sync.first()
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
    syncs = Sync.objects.filter(workspace=workspace).order_by("-created_at")
    queryset = syncs.select_related("source", "destination")
    for e in queryset:
        logger.info(e)
    return queryset


# TODO: Activation Server sends dummy wordspace_id for the sync details. Need to fix it.
@router.get("/workspaces/{workspace_id}/syncs/{sync_id}", response=SyncSchema)
def get_sync(request, workspace_id, sync_id):
    sync = Sync.objects.get(id=sync_id)
    return sync


@router.get("/workspaces/{workspace_id}/syncs/{sync_id}/runs/", response=Json)
def get_sync_runs(
    request,
    workspace_id,
    sync_id: UUID4,
    before: datetime = datetime.now(),
    limit: int = 25,
):
    return requests.get(
        f"{ACTIVATION_URL}/syncs/{sync_id}/runs/",
        params={"before": before, "limit": limit},
        timeout=SHORT_TIMEOUT,
    ).text


@router.post("/workspaces/{workspace_id}/syncs/{sync_id}/runs/{run_id}/abort", response=Json)
def abort_run(request, workspace_id, sync_id: UUID4, run_id: UUID4):
    return requests.post(
        f"{ACTIVATION_URL}/syncs/{sync_id}/runs/{run_id}/abort",
        timeout=SHORT_TIMEOUT,
    ).text


@router.post("/workspaces/{workspace_id}/syncs/{sync_id}/runs/create", response=Json)
def create_new_run(request, workspace_id, sync_id: UUID4, payload: SyncStartStopSchemaIn):
    # Prepare run time args for the sync
    run_time_args_config = {"run_time_args": {"full_refresh": payload.full_refresh}}

    return requests.post(
        f"{ACTIVATION_URL}/syncs/{sync_id}/runs/create",
        json=run_time_args_config,
        timeout=SHORT_TIMEOUT,
    ).text


@router.get("/workspaces/{workspace_id}/syncs/{sync_id}/runs/{run_id}", response=Json)
def get_run(request, workspace_id, sync_id: UUID4, run_id: UUID4):
    return requests.get(
        f"{ACTIVATION_URL}/syncs/{sync_id}/runs/{run_id}",
        timeout=SHORT_TIMEOUT,
    ).text


@router.get("/connectors/", response={200: Dict[str, List[ConnectorSchema]], 400: DetailSchema})
def get_connectors(request):
    # check for admin permissions
    try:
        logger.debug("listing connectors")
        connectors = Connector.objects.all()

        logger.info(f"connectors - {connectors}")
        src_dst_dict: Dict[str, List[ConnectorSchema]] = {}
        src_dst_dict["SRC"] = []
        src_dst_dict["DEST"] = []
        for conn in connectors:
            logger.info(f"conn{conn}")
            arr = conn.type.split("_")
            if arr[0] == "SRC":
                src_dst_dict["SRC"].append(conn)
            elif arr[0] == "DEST":
                src_dst_dict["DEST"].append(conn)
        return src_dst_dict
    except Exception:
        logger.exception("connector listing error")
        return (400, {"detail": "The list of connectors cannot be fetched."})


@router.get("/workspaces/{workspace_id}/syncs/{sync_id}/runs/{run_id}/logs", response=Json)
def get_logs(
        request,
        workspace_id: UUID4,
        sync_id: UUID4,
        run_id: UUID4,
        connector: str,
        since: Optional[int] = None,
        before: Optional[int] = None):
    return requests.get(
        f"{ACTIVATION_URL}/syncs/{sync_id}/runs/{run_id}/logs",
        params={"connector": connector, "since": since, "before": before},
        timeout=LONG_TIMEOUT,
    ).text


@router.get("/workspaces/{workspace_id}/syncs/{sync_id}/runs/{run_id}/samples", response=Json)
def get_samples(
        request,
        workspace_id: UUID4,
        sync_id: UUID4,
        run_id: UUID4,
        connector: str,
        metric_type: str):
    return requests.get(
        f"{ACTIVATION_URL}/syncs/{sync_id}/runs/{run_id}/samples",
        params={"collector": connector, "metric_type": metric_type},
        timeout=LONG_TIMEOUT,
    ).text


@router.get("/connectors/{workspace_id}/configured", response={200: Dict[str, List[ConnectorSchema]],
                                                               400: DetailSchema})
def get_connectors_configured(request, workspace_id):

    try:
        # Get the connectors that match the criteria
        logger.debug("listing all configured connectors")
        workspace = Workspace.objects.get(id=workspace_id)

        configured_connectors = OAuthApiKeys.objects.filter(workspace=workspace).values('type')

        connectors = Connector.objects.filter(
            oauth=True,
            oauth_keys="private",
            type__in=configured_connectors)

        src_dst_dict: Dict[str, List[ConnectorSchema]] = {}
        src_dst_dict["SRC"] = []
        src_dst_dict["DEST"] = []
        logger.debug("Connectors:-", connectors)
        for conn in connectors:
            arr = conn.type.split("_")
            logger.debug("Arr:_", arr)
            if arr[0] == "SRC":
                src_dst_dict["SRC"].append(conn)
            elif arr[0] == "DEST":
                src_dst_dict["DEST"].append(conn)

        return src_dst_dict

    except Workspace.DoesNotExist:
        return (400, {"detail": "Workspace not found."})

    except Exception:
        logger.exception("connector listing error")
        return (400, {"detail": "The list of  connectors cannot be fetched."})


@router.get("/connectors/{workspace_id}/not-configured",
            response={200: Dict[str, List[ConnectorSchema]], 400: DetailSchema})
def get_connectors_not_configured(request, workspace_id):

    try:
        # Get the connectors that match the criteria

        workspace = Workspace.objects.get(id=workspace_id)

        configured_connectors = OAuthApiKeys.objects.filter(workspace=workspace).values('type')

        connectors = Connector.objects.filter(
            oauth=True,
            oauth_keys="private"
        ).exclude(type__in=configured_connectors)

        src_dst_dict: Dict[str, List[ConnectorSchema]] = {}
        src_dst_dict["SRC"] = []
        src_dst_dict["DEST"] = []
        logger.debug("Connectors:-", connectors)
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
