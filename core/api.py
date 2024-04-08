"""
Copyright (c) 2024 valmi.io <https://github.com/valmi-io>

Created Date: Wednesday, March 8th 2023, 9:56:52 pm
Author: Rajashekar Varkala @ valmi.io

"""

import json
import logging
import os
import random
import string
import uuid
import psycopg2
import uuid

from datetime import datetime
from typing import Dict, List, Optional

import requests
from decouple import Csv, config
from ninja import Router
from pydantic import UUID4, Json

from core.schemas import (
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
    SyncSchemaUpdateIn,
    SyncStartStopSchemaIn,
    UserSchemaOut,
    CreateConfigSchemaIn
)

from .models import Account, Connector, Credential, Destination, Source, StorageCredentials, Sync, User, Workspace, OAuthApiKeys

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
        # if source=="SRC_SHOPIFY":
        #     host_url = os.environ["DB_URL"]
        #     db_password = os.environ["DB_PASSWORD"]
        #     db_username = os.environ["DB_USERNAME"]
        #     conn = psycopg2.connect(host=host_url,port="5432",database="dvdrental",user=db_username,password=db_password)
        #     cursor = conn.cursor()
        #     create_new_cred = True
        #     try:
        #         do_id_exists = StorageCredentials.objects.get(workspace_id=workspace_id)
        #         create_new_cred = False
        #     except Exception:
        #         create_new_cred = True
        #     if create_new_cred:
        #         user_name = ''.join(random.choices(string.ascii_lowercase, k=17))
        #         password = ''.join(random.choices(string.ascii_uppercase, k=17))
        #         creds = {'username': user_name, 'password': password}
        #         credential_info = {"id": uuid.uuid4()}
        #         credential_info["workspace"] = Workspace.objects.get(id=workspace_id)
        #         credential_info["connector_config"] = creds
        #         result = StorageCredentials.objects.create(**credential_info)
        #         logger.debug(result)
        #         query = ("CREATE ROLE {username} LOGIN PASSWORD %s").format(username=user_name)
        #         cursor.execute(query, (password,))
        #         query = ("GRANT INSERT, UPDATE, SELECT ON ALL TABLES IN SCHEMA public TO {username}").format(username=user_name)
        #         cursor.execute(query)
        #         conn.commit()
        #         conn.close()
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
    

@router.get("/workspaces/{workspace_id}/storage-credentials",response={200: Json, 400: DetailSchema})
def get_storage_credentials(request, workspace_id):
    host_url = os.environ["DB_URL"]
    db_password = os.environ["DB_PASSWORD"]
    db_username = os.environ["DB_USERNAME"]
    conn = psycopg2.connect(host=host_url,port="5432",database="dvdrental",user=db_username,password=db_password)
    cursor = conn.cursor()
    create_new_cred = True
    try:
        do_id_exists = StorageCredentials.objects.get(workspace_id=workspace_id)
        create_new_cred = False
    except Exception:
        create_new_cred = True
    if create_new_cred:
        user_name = ''.join(random.choices(string.ascii_lowercase, k=17))
        password = ''.join(random.choices(string.ascii_uppercase, k=17))
        creds = {'username': user_name, 'password': password}
        credential_info = {"id": uuid.uuid4()}
        credential_info["workspace"] = Workspace.objects.get(id=workspace_id)
        credential_info["connector_config"] = creds
        result = StorageCredentials.objects.create(**credential_info)
        logger.debug(result)
        query = ("CREATE ROLE {username} LOGIN PASSWORD %s").format(username=user_name)
        cursor.execute(query, (password,))
        query = ("CREATE SCHEMA AUTHORIZATION {name}").format(name = user_name)
        cursor.execute(query)
        query = ("GRANT INSERT, UPDATE, SELECT ON ALL TABLES IN SCHEMA {schema} TO {username}").format(schema=user_name,username=user_name)
        cursor.execute(query)
        conn.commit()
        conn.close()
    config = {}
    if not create_new_cred:
        config['username'] = do_id_exists.connector_config.get('username')
        config['password'] = do_id_exists.connector_config.get('password')
        config["schema"] = do_id_exists.connector_config.get("username")
    else:
        config['username'] = user_name
        config['password'] = password
        config["schema"] = user_name
    config['database'] = "dvdrental"
    config['host'] = host_url
    config['port'] = 5432
    config["ssl"] = False
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
