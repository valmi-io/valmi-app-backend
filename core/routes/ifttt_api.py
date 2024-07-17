from ninja import Router
from core.models import Ifttt
from core.schemas.schemas import DetailSchema, SuccessSchema, IftttPayloadSchema

router = Router()


@router.get("/workspaces/{workspace_id}/ifttt/{store_id}", response={200: str, 500: DetailSchema})
def get_ifttt(request, workspace_id: str, store_id: str):
    try:
        ifttt_code = Ifttt.objects.get(store_id=store_id).code
        Ifttt.objects.filter()
        return 200, ifttt_code
    except Ifttt.DoesNotExist:
        return 500, {"detail": "IFTTT code not found"}


@router.post("/workspaces/{workspace_id}/ifttt/{store_id}", response={200: SuccessSchema, 422: DetailSchema, 500: DetailSchema})
def set_ifttt(request, workspace_id: str, store_id: str, payload: IftttPayloadSchema):
    try:
        ifttt_code = payload.code
        Ifttt.objects.update_or_create(
            store_id=store_id,
            defaults={"code": ifttt_code}
        )
        return 200, {"status": "IFTTT code set successfully"}
    except Exception as e:
        return 500, {"detail": str(e)}
