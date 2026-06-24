from fastapi import APIRouter


router = APIRouter(prefix="/api", tags=["stock"])


@router.get("/picks")
def get_picks() -> dict[str, object]:
    return {"status": "ok", "data": []}
