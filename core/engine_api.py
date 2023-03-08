import logging
from typing import List

from ninja import Router

from core.schemas import DetailSchema, SyncSchema, ConnectorSchema
from .models import Connector, Sync

router = Router()


# Get an instance of a logger
logger = logging.getLogger(__name__)


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
