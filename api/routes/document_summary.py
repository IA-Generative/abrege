from fastapi import File, Body, UploadFile, APIRouter, status
from api.schemas.content import Content


router = APIRouter(tags=["Documents"])


@router.post("/doc/{user_id}", status_code=status.HTTP_201_CREATED)
async def summarize_doc(
    user_id: str,
    content: Content = Body(...),
    file: UploadFile = File(...),
):
    return {}
