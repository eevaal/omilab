from typing import Annotated

from database.database import get_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

db_dependency = Annotated[AsyncSession, Depends(get_db)]
