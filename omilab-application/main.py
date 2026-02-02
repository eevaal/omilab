import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from api.v1.auth import router as auth_router
from api.v1.lectures import decrypt_text
from api.v1.lectures import router as lectures_router
from api.v1.users import router as users_router
from core.security import decode_access_token
from database import crud
from database.database import Base, engine
from database.dependencies import db_dependency
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from models.lectures import Lecture, LectureRating
from models.users import User
from models.bookmarks import bookmarks_table
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.v1.bookmarks import router as bookmarks_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database created")
    yield


load_dotenv()
print("--- ПРОВЕРКА ENV ---")
print(f"Все ключи: {list(os.environ.keys())[-5:]}")
print(f"Значение MAINTENANCE_MODE: {os.getenv('MAINTENANCE_MODE')}")
print("--------------------")

app = FastAPI(lifespan=lifespan)


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "status_code": exc.status_code, "detail": exc.detail},
        status_code=exc.status_code,
    )


@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "status_code": 500, "detail": "Internal Server Error"},
        status_code=500,
    )


app.include_router(lectures_router)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(bookmarks_router, prefix="/api/v1/bookmarks")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def home_page(request: Request, db: db_dependency):
    current_user = await get_current_user_from_cookie(request, db)

    if current_user:
        print(f"Главная страница: Пользователь найден -> {current_user.username}")
    else:
        print("Главная страница: Пользователь НЕ найден (Аноним)")

    query = (
        select(Lecture, User)
        .join(User, Lecture.author == User.username)
        .order_by(Lecture.created_at.desc())
        .limit(3)
    )
    result = await db.execute(query)
    recent_lectures = result.all()

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "lectures": recent_lectures, "user": current_user},
    )


@app.get("/create")
async def create_page(request: Request):
    return templates.TemplateResponse("create.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/lecture/{id}")
async def lecture_page(request: Request, id: int, db: db_dependency):
    current_user = await get_current_user_from_cookie(request, db)

    lecture = await crud.get_lecture_by_id(db, lecture_id=id)
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")

    lecture.content = decrypt_text(lecture.content)

    query = select(User).where(User.username == lecture.author)
    result = await db.execute(query)
    author_user = result.scalars().first()

    user_rating = 0
    if current_user:
        query_rating = select(LectureRating).where(
            LectureRating.user_id == current_user.id, LectureRating.lecture_id == id
        )
        res_rating = await db.execute(query_rating)
        vote = res_rating.scalar_one_or_none()
        if vote:
            user_rating = vote.score

    query_avg = select(func.avg(LectureRating.score)).where(LectureRating.lecture_id == id)
    res_avg = await db.execute(query_avg)
    average_rating = res_avg.scalar() or 0.0

    average_rating = round(average_rating, 1)

    return templates.TemplateResponse(
        "lecture.html",
        {
            "request": request,
            "lecture": lecture,
            "user": current_user,
            "author": author_user,
            "user_rating": user_rating,
            "average_rating": average_rating,
        },
    )


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/profile/{username}", response_class=HTMLResponse)
async def profile_page(request: Request, username: str, db: db_dependency):
    current_user = await get_current_user_from_cookie(request, db)

    query_user = select(User).where(User.username == username)
    result_user = await db.execute(query_user)
    profile_owner = result_user.scalars().first()

    if not profile_owner:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    query_count = select(func.count(Lecture.id)).where(Lecture.author == profile_owner.username)
    count_result = await db.execute(query_count)
    total_lectures = count_result.scalar()

    four_days_ago = datetime.utcnow() - timedelta(days=4)
    query_new = select(func.count(Lecture.id)).where(
        Lecture.author == profile_owner.username, Lecture.created_at >= four_days_ago
    )
    new_result = await db.execute(query_new)
    new_lectures_count = new_result.scalar()

    query_lectures = (
        select(Lecture)
        .where(Lecture.author == profile_owner.username)
        .order_by(Lecture.created_at.desc())
    )
    lectures_result = await db.execute(query_lectures)
    user_lectures = lectures_result.scalars().all()

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": current_user,
            "profile_user": profile_owner,
            "total_lectures": total_lectures,
            "new_lectures_count": new_lectures_count,
            "lectures": user_lectures,
        },
    )


async def get_current_user_from_cookie(request: Request, db: AsyncSession):
    token = request.cookies.get("access_token")
    if not token:
        return None

    scheme, _, param = token.partition(" ")
    actual_token = param if scheme.lower() == "bearer" else token

    payload = decode_access_token(actual_token)
    if not payload:
        return None

    username = payload.get("sub")
    if not username:
        return None

    query = select(User).where(User.username == username)
    result = await db.execute(query)
    return result.scalars().first()


MAINTENANCE_MODE = os.getenv("IS_MAINTENANCE", "false").lower() == "true"


@app.middleware("http")
async def maintenance_middleware(request: Request, call_next):
    current_maintenance = os.getenv("MAINTENANCE_MODE", "false").lower() == "true"

    is_static = request.url.path.startswith("/static")

    if current_maintenance and not is_static:
        print("!!! ДОСТУП ОГРАНИЧЕН: Режим техобслуживания ВКЛЮЧЕН")
        return templates.TemplateResponse(
            "error.html", {"request": request, "status_code": 503}, status_code=503
        )

    return await call_next(request)
