from ninja import Router

router = Router()


# @router.post("/credentials/create")
# def create_article(request, payload: Credential):
#     data = payload.dict()
#     try:
#         # author = Credential.objects.get(id=data["id"])
#         # del data["id"]
#         user = User.objects.get(id=data["user"])
#         credential = Credential.objects.create(credential=credential, **data)
#         return {
#             "detail": "Credential has been successfully created.",
#             "id": credential.id,
#         }
#     except User.DoesNotExist:
#         return {"detail": "The specific user cannot be found."}
