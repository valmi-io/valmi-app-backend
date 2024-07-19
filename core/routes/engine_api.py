"""
Copyright (c) 2024 valmi.io <https://github.com/valmi-io>

Created Date: Wednesday, March 8th 2023, 9:56:52 pm
Author: Rajashekar Varkala @ valmi.io

"""

import json
import logging
from typing import Dict, List

from decouple import Csv, config
# from opentelemetry import trace
from ninja import Router
from opentelemetry.metrics import get_meter_provider

from core.schemas.schemas import (ChannelTopicsSchema, ConnectorSchema, DetailSchema, PackageSchema,
                                  PromptSchema, SyncSchema, ChannelTopicsPayloadSchema)
from valmi_app_backend.utils import replace_values_in_json

from ..models import Connector, OAuthApiKeys, Package, Prompt, Sync, Ifttt, ChannelTopics

router = Router()

# Get an instance of a logger
logger = logging.getLogger(__name__)

meter = get_meter_provider().get_meter("engine_api", "test_version_number")


# Create /syncs api counter
syncs_api_counter = meter.create_counter("syncs_api_counter")


@router.get("/syncs/", response={200: List[SyncSchema], 400: DetailSchema})
def get_all_syncs(request):

    syncs_api_counter.add(1)

    # check for admin permissions
    try:
        syncs = Sync.objects.select_related("source", "destination")

        # Replacing Oauth keys
        oauth_proxy_keys = config("OAUTH_SECRETS", default="", cast=Csv(str))

        if len(oauth_proxy_keys) > 0:
            for sync in syncs:
                src_dst = [sync.source, sync.destination]

                for obj in src_dst:
                    workspace = obj.credential.workspace
                    connector_type = obj.credential.connector.type

                    queryset = OAuthApiKeys.objects.filter(workspace=workspace, type=connector_type)

                    if queryset.exists():

                        keys = queryset.first()

                        # Replacing oauth keys with db values
                        obj.credential.connector_config = replace_values_in_json(
                            obj.credential.connector_config, keys.oauth_config)
                    else:

                        # Replacing oauth keys with .env values
                        config_str = json.dumps(obj.credential.connector_config)

                        for key in oauth_proxy_keys:
                            config_str = config_str.replace(key, config(key))
                        obj.credential.connector_config = json.loads(config_str)

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


@router.post("/prompts/create", response={200: PromptSchema, 400: DetailSchema})
def create_prompt(request, payload: PromptSchema):
    data = payload.dict()
    logger.debug(data)
    try:
        logger.debug("creating prompt")
        prompt = Prompt.objects.create(**data)
        return (200, prompt)
    except Exception as ex:
        logger.debug(f"prompt not created. Attempting to update.")
        # Prompt.objects.filter(name=data['name']) will only return one item as name is unique for every prompt
        data.pop('id')
        logger.debug(f"updating with {data}")
        rows_updated = Prompt.objects.filter(name=data['name']).update(**data)
        if rows_updated == 0:
            logger.debug(f"nothing to update")
        elif rows_updated == 1:
            logger.debug(f"prompt updated")
        else:
            msg = f"something went wrong while creating/updating prompt. message: {ex}"
            logger.debug(msg)
            return (400, {"detail": msg})
        return (200, data)


@router.post("/packages/create", response={200: PackageSchema, 400: DetailSchema})
def create_package(request, payload: PackageSchema):
    # check for admin permissions
    logger.info("logging package schema")
    data = payload.dict()
    logger.debug(data)
    try:
        logger.debug("creating package")
        package = Package.objects.create(**data)
        return (200, package)
    except Exception:
        logger.exception("Package error")
        return (400, {"detail": "The specific package cannot be created."})


@router.get("/connectors/", response={200: Dict[str, List[ConnectorSchema]], 400: DetailSchema})
def get_connectors(request):
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


@router.get("/ifttts", response={200: List, 400: DetailSchema})
def get_ifttts(request):
    try:
        ifttt_codes = Ifttt.objects.values()
        # remove hardcoding later
        ifttt_codes = [
            {
                'store_id': 'sh_1234',
                'code': 'print("hello world")'
            },
            {
                'store_id': 'sh_56789',
                'code': 'print("hello valmi")'
            },

        ]
        return 200, ifttt_codes
    except Exception as e:
        logger.exception("ifttt listing error")
        return (400, {"detail": "The list of ifttt's for all stores cannot be fetched."})


@router.post("/channeltopics", response={200: List[ChannelTopicsSchema], 400: DetailSchema})
def get_channel_topics(request, payload: ChannelTopicsPayloadSchema):
    try:
        topics_list = list(ChannelTopics.objects.all().filter(channel__in=payload.channel_in))
        return (200, topics_list)
    except Exception as e:
        logger.exception("channel topics listing error")
        return (400, {"detail": "The list of channel_topic's cannot be fetched."})
