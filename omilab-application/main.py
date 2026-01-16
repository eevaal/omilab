import sqlite3
from contextlib import asynccontextmanager
from typing import Sequence

from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import or_

from database import crud
from database.database import engine, Base
from database.dependencies import db_dependency
from models.lectures import Lecture
from schemas.lectures import LectureCreate, LectureResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database created")
    yield
app = FastAPI(
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/")
async def read_root(request: Request, db: db_dependency):
    recent_lectures = await crud.get_recent_lectures(db, limit=3)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "lectures": recent_lectures
    })
@app.post("/api/lectures", response_model=LectureResponse)
async def create_lecture(lecture: LectureCreate, db: db_dependency):
    return await crud.create_lecture(db=db, lecture=lecture)


@app.get("/api/search", response_model=Sequence[LectureResponse])
async def search_lectures(q: str, db: db_dependency):
    return await crud.search_lectures(db, query=q)


@app.get("/lecture/{id}")
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

# 2. Страница админки (просто отдает HTML)
@app.get("/create")
async def create_page(request: Request):
    return templates.TemplateResponse("create.html", {"request": request})