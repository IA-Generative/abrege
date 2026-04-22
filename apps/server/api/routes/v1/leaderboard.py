from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status as http_status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.security.token import RequestContext
from api.core.security.factory import TokenVerifier
from src.internal.db import get_async_session_dep
from src.schemas.task import Task
from pydantic import BaseModel

router = APIRouter(prefix="/v1/leaderboard", tags=["Leaderboard"])

TokenDep = Annotated[RequestContext, Depends(TokenVerifier)]
DbDep = Annotated[AsyncSession, Depends(get_async_session_dep)]


class LeaderboardEntryResponse(BaseModel):
    rank: int
    user_id: str
    task_count: int
    is_me: bool


class LeaderboardResponse(BaseModel):
    entries: list[LeaderboardEntryResponse]
    my_rank: Optional[int] = None
    total_participants: int


@router.get("", response_model=LeaderboardResponse)
async def get_leaderboard(
    ctx: TokenDep,
    db: DbDep,
    start_date: Optional[int] = None,
    end_date: Optional[int] = None,
    task_type: Optional[str] = None,
    limit: int = 20,
):
    if ctx.user_id is None:
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    # Build base query: count tasks per user
    q = select(Task.user_id, func.count(Task.id).label("task_count")).group_by(Task.user_id)

    if start_date is not None:
        q = q.filter(Task.created_at >= start_date)
    if end_date is not None:
        q = q.filter(Task.created_at <= end_date)
    if task_type:
        q = q.filter(Task.type == task_type)

    q = q.order_by(func.count(Task.id).desc())

    # Get all participants for ranking
    all_rows = (await db.execute(q)).all()
    total_participants = len(all_rows)

    # Build ranked entries
    ranked = [
        {
            "rank": idx + 1,
            "user_id": row.user_id,
            "task_count": row.task_count,
            "is_me": row.user_id == ctx.user_id,
        }
        for idx, row in enumerate(all_rows)
    ]

    # Find current user's rank
    my_rank = None
    for entry in ranked:
        if entry["is_me"]:
            my_rank = entry["rank"]
            break

    # Return top N + current user if not in top N
    top = ranked[:limit]
    top_user_ids = {e["user_id"] for e in top}

    if ctx.user_id not in top_user_ids and my_rank is not None:
        my_entry = next(e for e in ranked if e["is_me"])
        top.append(my_entry)

    return LeaderboardResponse(
        entries=[LeaderboardEntryResponse(**e) for e in top],
        my_rank=my_rank,
        total_participants=total_participants,
    )
