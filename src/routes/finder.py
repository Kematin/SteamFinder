from fastapi import APIRouter

route = APIRouter(prefix="/finder", tags=["Finder"])


@route.post("/update")
async def update_stickers():
    return {"message": "None"}
