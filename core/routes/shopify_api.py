import json
import logging

from ninja import Router
from pydantic import Json


router = Router()

# Get an instance of a logger
logger = logging.getLogger(__name__)


@router.get("/products/{product_id}/recommendations", response={200: Json, 500: Json})
def get_prompts(request, product_id):

    return json.dumps({"hi": "hello"})
