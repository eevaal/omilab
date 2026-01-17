from typing import Sequence

from fastapi import APIRouter, Request, HTTPException

from database import crud
from database.dependencies import db_dependency
from schemas.lectures import LectureCreate, LectureResponse

from fastapi.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.post("/lectures", response_model=LectureResponse)
async def create_lecture(lecture: LectureCreate, db: db_dependency):
    return await crud.create_lecture(db=db, lecture=lecture)


@router.get("/lecture/{id}")
async def lecture_page(request: Request, id: int, db: db_dependency):
    # 1. Ищем лекцию
    lecture = await crud.get_lecture_by_id(db, lecture_id=id)

    # 2. Если нет такой — 404
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")

    # 3. Отдаем красивый HTML
    return templates.TemplateResponse("lecture.html", {
        "request": request,
        "lecture": lecture
    })

@router.get("/search", response_model=Sequence[LectureResponse])
async def search_lectures(q: str, db: db_dependency):
    return await crud.search_lectures(db, query=q)

# 2. Страница админки (просто отдает HTML)
@router.get("/create")
async def create_page(request: Request):
    return templates.TemplateResponse("create.html", {"request": request})