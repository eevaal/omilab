from typing import Sequence
from fastapi import APIRouter
from database import crud
from database.dependencies import db_dependency
from schemas.lectures import LectureCreate, LectureResponse

router = APIRouter(prefix="/api/v1/lectures")

@router.post("/", response_model=LectureResponse)
async def create_lecture(lecture: LectureCreate, db: db_dependency):
    return await crud.create_lecture(db=db, lecture=lecture)

@router.get("/search", response_model=Sequence[LectureResponse])
async def search_lectures(q: str, db: db_dependency):
    return await crud.search_lectures(db, query=q)