from ninja import Router
from core.models import Storefront, WorkspaceStorefront, Workspace
from core.schemas.schemas import DetailSchema

router = Router()


@router.post("/workspaces/{workspace_id}/storefront/create/{platform}/{storefront}", response={200: str, 500: DetailSchema})
def create_storefront(request, workspace_id: str, platform: str, storefront: str):
    try:
        storefront_object = Storefront.objects.create(platform=platform, id=storefront)
        WorkspaceStorefront.objects.create(workspace=Workspace.objects.get(id=workspace_id), storefront=storefront_object)
        return 200, "Storefront created successfully."
    except Workspace.DoesNotExist:
        return 500, DetailSchema(detail="Workspace not found")
    except Exception as e:
        return 500, DetailSchema(detail=str(e))
