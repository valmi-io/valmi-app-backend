"""
Copyright (c) 2023 valmi.io <https://github.com/valmi-io>

Created Date: Wednesday, March 8th 2023, 9:56:52 pm
Author: Rajashekar Varkala @ valmi.io

"""

import logging
from typing import Dict, List

from decouple import Csv, config
from ninja import Router

from core.schemas import ConnectorSchema, DetailSchema, SyncSchema

from .models import Connector, Sync

router = Router()


# Get an instance of a logger
logger = logging.getLogger(__name__)


@router.get("/syncs/", response={200: List[SyncSchema], 400: DetailSchema})
def get_all_syncs(request):
    # check for admin permissions
    try:
        syncs = Sync.objects.select_related("source", "destination")
        oauth_proxy_keys = config("OAUTH_SECRETS", default="", cast=Csv(str))
        if len(oauth_proxy_keys) > 0:
            for sync in syncs:
                credentials = sync.destination.credential.connector_config["credentials"]
                for k, v in credentials.items():
                    credentials[k] = config(v, default=v)
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
