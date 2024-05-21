import logging
from typing import List

<<<<<<< HEAD:core/routes/prompt_api.py
=======
from core.models import Prompt, Credential
from core.schemas import DetailSchema, PromptSchema,PromptSchemaOut
>>>>>>> d345482 (feat: prompt list changes):core/prompt_api.py
from ninja import Router
import json

from core.models import Prompt
from core.schemas import DetailSchema, PromptSchema

logger = logging.getLogger(__name__)
router = Router()

@router.get("/workspaces/{workspace_id}/prompts", response={200: List[PromptSchema], 400: DetailSchema})
def get_prompts(request):
    try:
        prompts = list(Prompt.objects.all().values())
        connector_ids = list(Credential.objects.values('connector_id').distinct())
        connector_types = [connector['connector_id'] for connector in connector_ids]
        for prompt in prompts:
            prompt["id"]  = str(prompt["id"])
            if prompt["type"] in connector_types:
                prompt["enabled"] = True
            else:
                prompt["enabled"] = False
        return prompts
    except Exception as err:
        logger.exception("prompts listing error:"+ err)
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

    