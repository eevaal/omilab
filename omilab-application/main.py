from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, func

from database import crud
from database.database import engine, Base
from database.dependencies import db_dependency

from api.v1.lectures import router as lectures_router
from api.v1.auth import router as auth_router

from fastapi.responses import HTMLResponse

from models.lectures import Lecture
from models.users import User


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database created")
    yield


app = FastAPI(lifespan=lifespan)


app.include_router(lectures_router)
app.include_router(auth_router, prefix="/api/v1")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def read_root(request: Request, db: db_dependency):
    recent_lectures = await crud.get_recent_lectures(db, limit=3)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "lectures": recent_lectures
    })


@app.get("/create")
async def create_page(request: Request):
    return templates.TemplateResponse("create.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/lecture/{id}")
async def lecture_page(request: Request, id: int, db: db_dependency):
    lecture = await crud.get_lecture_by_id(db, lecture_id=id)
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")

    return templates.TemplateResponse("lecture.html", {
        "request": request,
        "lecture": lecture
    })

# Страница входа
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Страница профиля (та самая "пушка")
@app.get("/profile/{username}", response_class=HTMLResponse)
async def profile_page(request: Request, username: str, db: db_dependency):
    # 1. Ищем юзера в базе
    query_user = select(User).where(User.username == username)
    result_user = await db.execute(query_user)
    user = result_user.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # 2. Считаем общее кол-во лекций автора
    query_count = select(func.count(Lecture.id)).where(Lecture.author == username)
    count_result = await db.execute(query_count)
    total_lectures = count_result.scalar()

    # 3. Считаем новые лекции за последние 4 дня
    four_days_ago = datetime.utcnow() - timedelta(days=4)
    query_new = select(func.count(Lecture.id)).where(
        Lecture.author == username,
        Lecture.created_at >= four_days_ago
    )
    new_result = await db.execute(query_new)
    new_lectures_count = new_result.scalar()

    # 4. Получаем последние 10 лекций
    query_lectures = select(Lecture).where(Lecture.author == username).order_by(Lecture.created_at.desc()).limit(10)
    lectures_result = await db.execute(query_lectures)
    user_lectures = lectures_result.scalars().all()

    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": user,
        "total_lectures": total_lectures,
        "new_lectures_count": new_lectures_count,
        "lectures": user_lectures
    })