from ninja import Router
from core.models import Ifttt, Workspace
from core.schemas.schemas import DetailSchema, IftttCodeResponseSchema, SuccessSchema, IftttPayloadSchema

router = Router()


@router.get("/workspaces/{workspace_id}/ifttt/{store_id}", response={200: IftttCodeResponseSchema, 500: DetailSchema})
def get_ifttt(request, workspace_id: str, store_id: str):
    try:
        ifttt_code = Ifttt.objects.get(workspace=workspace_id, store_id=store_id).code
        return 200, {"ifttt_code": ifttt_code}
    except Ifttt.DoesNotExist:
        return 500, {"detail": "IFTTT code not found"}


@router.post("/workspaces/{workspace_id}/ifttt/{store_id}", response={200: SuccessSchema, 422: DetailSchema, 500: DetailSchema})
def set_ifttt(request, workspace_id: str, store_id: str, payload: IftttPayloadSchema):
    try:
        ifttt_code = payload.code
        ifttt_entry, created = Ifttt.objects.update_or_create(
            store_id=store_id,
            defaults={"code": ifttt_code, "workspace": Workspace.objects.get(id=workspace_id)}
        )
        return 200, {"status": "IFTTT code set successfully"}
    except Exception as e:
        return 500, {"detail": str(e)}
