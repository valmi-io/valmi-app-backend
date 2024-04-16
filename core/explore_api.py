import logging
import uuid
from pydantic import Json
from core.models import Account, Explore, Prompt, Workspace
from core.schemas import DetailSchema
from ninja import Router
import json

logger = logging.getLogger(__name__)

router = Router()

@router.get("/", response={200: Json, 400: DetailSchema})
def get_prompts(request):
    try:
        logger.debug("listing connectors")
        explores = Explore.objects.all()
        explores_data_list = list(explores.values())
        response = json.dumps(explores_data_list)
        return response
    except Exception:
        logger.exception("prompts listing error")
        return (400, {"detail": "The list of explores cannot be fetched."})


@router.post("/workspaces/{workspace_id}/prompts/{prompt_id}",response={200: Json, 400: DetailSchema})
def create_explore(request, workspace_id,prompt_id,payload: Json):
    logger.info("data before creating")
    data = payload.dict()
    logger.info("data before creating")
    logger.info(data)
    try:
        data["id"] = uuid.uuid4()
        data["workspace"] = Workspace.objects.get(id=workspace_id)
        data["prompt"] = Prompt.objects.get(id=prompt_id)
        account_info = data.pop("account", None)
        if account_info and len(account_info) > 0:
            account_info["id"] = uuid.uuid4()
            account_info["workspace"] = data["workspace"]
            data["account"] = Account.objects.create(**account_info)
        logger.debug(data)
        explore = Explore.objects.create(**data)
    except Exception:
        logger.exception("explore creation error")
        return (400, {"detail": "The specific explore cannot be created."})