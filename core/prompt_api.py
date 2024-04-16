import logging
from typing import List
import uuid

from core.models import Prompt
from core.schemas import DetailSchema, PromptSchema
from ninja import Router
import json

logger = logging.getLogger(__name__)

router = Router()

@router.get("/", response={200: List[PromptSchema], 400: DetailSchema})
def get_prompts(request):
    try:
        logger.debug("listing prompts")
        prompts = Prompt.objects.all()
        prompts_data = list(prompts.values())
        for prompt in prompts_data:
            for key, value in prompt.items():
                if isinstance(value, uuid.UUID):
                    prompt[key] = str(value)
        response = json.dumps(prompts_data)
        logger.info(response)
        logger.info(f"prompts - {prompts}")
        return prompts
    except Exception:
        logger.exception("prompts listing error")
        return (400, {"detail": "The list of prompts cannot be fetched."})
    