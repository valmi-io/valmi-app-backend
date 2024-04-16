import logging

from pydantic import Json
from core.models import Package
from core.schemas import DetailSchema
from ninja import Router
import json

logger = logging.getLogger(__name__)

router = Router()

@router.get("/", response={200: Json, 400: DetailSchema})
def get_packages(request):
    try:
        logger.debug("listing packages")
        packages = Package.objects.all()
        packages_data = list(packages.values())
        response = json.dumps(packages_data)
        logger.info(response)
        logger.info(f"packages - {packages_data}")
        return response
    except Exception:
        logger.exception("packages listing error")
        return (400, {"detail": "The list of packages cannot be fetched."})
    
@router.get("/{package_id}", response={200: Json, 400: DetailSchema})
def get_packages(request,package_id):
    try:
        logger.debug("listing packages")
        package_id_upper = package_id.upper()
        package = Package.objects.get(name = package_id_upper)
        package_dict = {
            "scopes":package.scopes,
            "package_id":package.name,
            "gated":package.gated,
        }
        response = json.dumps(package_dict)
        return response
    except Exception:
        logger.exception("package listing error")
        return (400, {"detail": "Package not found"})
