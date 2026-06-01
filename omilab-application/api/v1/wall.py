from core.security import get_current_user
from database.database import get_db
from fastapi import APIRouter, Depends, HTTPException
from models.users import User
from models.wall import WallPost
from schemas.wall import WallPostCreate, WallPostDisplay
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/wall", tags=["Wall"])


@router.post("/post", response_model=WallPostDisplay)
async def create_post(
    post_data: WallPostCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    target = await db.get(User, post_data.target_user_id)
    if not target:
        raise HTTPException(404, detail="Пользователь не найден")

    new_post = WallPost(
        content=post_data.content, author_id=user.id, target_user_id=post_data.target_user_id
    )

    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)

    return WallPostDisplay(
        id=new_post.id,
        content=new_post.content,
        created_at=new_post.created_at,
        author_username=user.username,
        author_avatar_url=user.avatar_url,  # <--- ВАЖНО
        author_is_verified=user.is_verified,  # <--- ВАЖНО
    )


@router.get("/{user_id}", response_model=list[WallPostDisplay])
async def get_wall(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WallPost)
        .options(selectinload(WallPost.author))
        .where(WallPost.target_user_id == user_id)
        .order_by(WallPost.created_at.desc())
        .limit(50)
    )
    posts = result.scalars().all()

    return [
        WallPostDisplay(
            id=p.id,
            content=p.content,
            created_at=p.created_at,
            author_username=p.author.username,
            author_avatar_url=p.author.avatar_url,  # <--- ВАЖНО
            author_is_verified=p.author.is_verified,  # <--- ВАЖНО
        )
        for p in posts
    ]
