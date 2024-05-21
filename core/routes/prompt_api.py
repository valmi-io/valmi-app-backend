import logging
from typing import List

from ninja import Router

from core.models import Prompt
from core.schemas import DetailSchema, PromptSchema

logger = logging.getLogger(__name__)
router = Router()

@router.get("/workspaces/{workspace_id}/prompts", response={200: List[PromptSchema], 400: DetailSchema})
def get_prompts(request):
    try:
        logger.debug("listing prompts")
        prompts = Prompt.objects.all()
        return prompts
    except Exception:
        logger.exception("prompts listing error")
        return (400, {"detail": "The list of prompts cannot be fetched."})

@router.get("/workspaces/{workspace_id}/prompts/{prompt_id}", response={200: PromptSchema, 400: DetailSchema})
def get_prompts(request,prompt_id):
    try:
        logger.debug("listing prompts")
        prompt = Prompt.objects.get(id=prompt_id)
        return prompt
    except Exception:
        logger.exception("prompt listing error")
        return (400, {"detail": "The  prompt cannot be fetched."})

    