import logging
from typing import List
import uuid
from core.models import Account, Explore, Prompt, Workspace
from core.schemas import DetailSchema, ExploreSchema, ExploreSchemaIn
from ninja import Router

logger = logging.getLogger(__name__)

router = Router()

@router.get("/workspaces/{workspace_id}", response={200: List[ExploreSchema], 400: DetailSchema})
def get_prompts(request,workspace_id):
    try:
        logger.debug("listing connectors")
        workspace = Workspace.objects.get(id=workspace_id)
        explores = Explore.objects.filter(workspace=workspace)
        return explores
    except Exception:
        logger.exception("explores listing error")
        return (400, {"detail": "The list of explores cannot be fetched."})


@router.post("/workspaces/{workspace_id}/create",response={200: ExploreSchema, 400: DetailSchema})
def create_explore(request, workspace_id,payload: ExploreSchemaIn):
    logger.info("data before creating")
    data = payload.dict()
    logger.info("data before creating")
    logger.info(data)
    try:
        data["id"] = uuid.uuid4()
        data["workspace"] = Workspace.objects.get(id=workspace_id)
        data["prompt"] = Prompt.objects.get(id=data["prompt_id"])
        account_info = data.pop("account", None)
        if account_info and len(account_info) > 0:
            account_info["id"] = uuid.uuid4()
            account_info["workspace"] = data["workspace"]
            data["account"] = Account.objects.create(**account_info)
        logger.debug(data)
        explore = Explore.objects.create(**data)
        return explore
    except Exception:
        logger.exception("explore creation error")
        return (400, {"detail": "The specific explore cannot be created."})