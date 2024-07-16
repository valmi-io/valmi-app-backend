from ninja import Router
from pydantic import Json

from core.models import Ifttt

router = Router()

@router.get("/workspaces/{workspace_id}/ifttt/{store_id}", response={200: Json, 500: Json})
def get_ifttt(request, workspace_id: str, store_id: str):
    try:
        ifttt_code = Ifttt.objects.get(store_id=store_id).code
        return 200, {"ifttt_code": ifttt_code}
    except Ifttt.DoesNotExist:
        return 500, {"error": "ifttt code not found"}

@router.post("/workspaces/{workspace_id}/ifttt/{store_id}", response={200: Json, 500: Json})
def set_ifttt(request, workspace_id: str, store_id: str, payload: dict):
    try:
        ifttt_code = payload.get("code")
        if ifttt_code is None:
            return 500, {"error": "No ifttt_code provided"}
        ifttt_entry, created = Ifttt.objects.update_or_create(
            store_id=store_id,
            defaults={"code": ifttt_code}
        )
        return 200, {"message": "ifttt code set successfully"}
    except Exception as e:
        return 500, {"error": str(e)}

@router.get("/workspaces/{workspace_id}/ifttt", response={200: Json, 500: Json})
def get_all_ifttt(request, workspace_id: str):
    try:
        ifttt_codes = Ifttt.objects.values('store_id', 'code')
        ifttt_codes_dict = {entry['store_id']: entry['code'] for entry in ifttt_codes}
        return 200, {"ifttt_codes": ifttt_codes_dict}
    except Exception as e:
        return 500, {"error": str(e)}
