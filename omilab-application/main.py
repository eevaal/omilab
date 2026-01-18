from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from database import crud
from database.database import engine, Base
from database.dependencies import db_dependency
from api.v1.lectures import router as lectures_router

from fastapi.responses import HTMLResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database created")
    yield


app = FastAPI(lifespan=lifespan)


app.include_router(lectures_router)

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