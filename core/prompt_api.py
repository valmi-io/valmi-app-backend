import logging

from pydantic import Json
from core.models import Prompt
from core.schemas import DetailSchema
from ninja import Router
import json

logger = logging.getLogger(__name__)

router = Router()

@router.get("/", response={200: Json, 400: DetailSchema})
def get_prompts(request):
    try:
        logger.debug("listing connectors")
        prompts = Prompt.objects.all()
        prompts_data = list(prompts.values())
        response = json.dumps(prompts_data)
        logger.info(response)
        logger.info(f"prompts - {prompts}")
        return response
    except Exception:
        logger.exception("prompts listing error")
        return (400, {"detail": "The list of prompts cannot be fetched."})
    