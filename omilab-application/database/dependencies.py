from fastapi import Depends
from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession

from database.database import get_db

db_dependency = Annotated[AsyncSession, Depends(get_db)]