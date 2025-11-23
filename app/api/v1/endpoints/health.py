from fastapi import APIRouter
from sqlalchemy import text
from app.db.session import engine

router = APIRouter()


@router.get("/", summary="Состояние API и базы данных")
async def health_check():
    db_status = "ok"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    return {"api": "ok", "db": db_status}
