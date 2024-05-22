import logging
from typing import Dict, List

from ninja import Router

from core.schemas.schemas import ConnectorSchema, DetailSchema

from core.models import Connector, OAuthApiKeys, Workspace

router = Router()

# Get an instance of a logger
logger = logging.getLogger(__name__)


@router.get("/", response={200: Dict[str, List[ConnectorSchema]], 400: DetailSchema})
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


@router.get("{workspace_id}/configured", response={200: Dict[str, List[ConnectorSchema]],
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


@router.get("{workspace_id}/not-configured",
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