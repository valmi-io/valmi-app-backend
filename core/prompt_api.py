import logging
from typing import List

from core.models import Prompt
from core.schemas import DetailSchema, PromptSchema
from ninja import Router

logger = logging.getLogger(__name__)

router = Router()

@router.get("/", response={200: List[PromptSchema], 400: DetailSchema})
def get_prompts(request):
    try:
        logger.debug("listing prompts")
        prompts = Prompt.objects.all()
        return prompts
    except Exception:
        logger.exception("prompts listing error")
        return (400, {"detail": "The list of prompts cannot be fetched."})
    