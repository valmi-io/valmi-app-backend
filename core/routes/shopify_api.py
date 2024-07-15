import logging

from ninja import Router
from pydantic import Json
import requests

router = Router()

# Get an instance of a logger
logger = logging.getLogger(__name__)


@router.get("/products/{product_id}/recommendations", response={200: dict, 500: Json})
def get_prompts(request, product_id):
    response = requests.get(
        f'https://thebleulabel.myshopify.com/recommendations/products.json?product_id={product_id}&intent=related')
    logger.debug(response)
    return response.json()
