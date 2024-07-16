from ninja import Router
from pydantic import Json

from core.models import LuaIfttt

router = Router()

@router.get("/workspaces/{workspace_id}/api/lua/{store_id}", response={200: Json, 500: Json})
def get_lua(request, workspace_id: str, store_id: str):
    try:
        lua_code = LuaIfttt.objects.get(store_id=store_id).lua_code
        return 200, {"lua_code": lua_code}
    except LuaIfttt.DoesNotExist:
        return 500, {"error": "Lua code not found"}

@router.post("/workspaces/{workspace_id}/api/lua/{store_id}", response={200: Json, 500: Json})
def set_lua(request, workspace_id: str, store_id: str, payload: dict):
    try:
        lua_code = payload.get("lua_code")
        if lua_code is None:
            return 500, {"error": "No lua_code provided"}
        lua_entry, created = LuaIfttt.objects.update_or_create(
            store_id=store_id,
            defaults={"lua_code": lua_code}
        )
        return 200, {"message": "Lua code set successfully"}
    except Exception as e:
        return 500, {"error": str(e)}

@router.get("/workspaces/{workspace_id}/api/lua", response={200: Json, 500: Json})
def get_all_lua(request, workspace_id: str):
    try:
        lua_codes = list(LuaIfttt.objects.values_list('lua_code', flat=True))
        return 200, {"lua_codes": lua_codes}
    except Exception as e:
        return 500, {"error": str(e)}