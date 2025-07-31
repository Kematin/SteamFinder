from fastapi import APIRouter

route = APIRouter(prefix="/cache", tags=["Cache"])


@route.post("/update")
async def update_cache():
    return {"message": "None"}
