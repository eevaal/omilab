from api.v1.auth import get_current_user
from database.dependencies import db_dependency
from fastapi import APIRouter, Depends, HTTPException, status
from models.lectures import Lecture
from models.users import User

router = APIRouter()


@router.post("/{lecture_id}")
async def toggle_bookmark(
    lecture_id: int,
    db: db_dependency,
    current_user: User = Depends(get_current_user),
):
    lecture = await db.get(Lecture, lecture_id)
    if not lecture:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Лекция не найдена")

    is_bookmarked = False

    if lecture in current_user.bookmarks:
        current_user.bookmarks.remove(lecture)
        is_bookmarked = False
        message = "Лекция удалена из закладок"
    else:
        current_user.bookmarks.append(lecture)
        is_bookmarked = True
        message = "Лекция добавлена в закладки"

    await db.commit()

    return {"ok": True, "is_bookmarked": is_bookmarked, "message": message}
