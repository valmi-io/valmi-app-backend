import logging
from typing import List

from core.models import Package
from core.schemas.schemas import DetailSchema, PackageSchema
from ninja import Router

logger = logging.getLogger(__name__)

router = Router()

@router.get("/", response={200: List[PackageSchema], 400: DetailSchema})
def get_packages(request):
    try:
        logger.debug("listing packages")
        packages = Package.objects.all()
        return packages
    except Exception:
        logger.exception("packages listing error")
        return (400, {"detail": "The list of packages cannot be fetched."})
    
@router.get("/{package_id}", response={200: PackageSchema, 400: DetailSchema})
def get_packages(request,package_id):
    try:
        logger.debug("listing packages")
        package_id_upper = package_id.upper()
        package = Package.objects.get(name = package_id_upper)
        return package
    except Exception:
        logger.exception("package listing error")
        return (400, {"detail": "Package not found"})
