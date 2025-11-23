from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.team import Team, TeamCreate, TeamResponse, TeamDeactivateRequest
from app.schemas.error import ErrorResponse, ErrorCode
from app.services.team_service import TeamService

router = APIRouter()


@router.post(
    "/add",
    summary="Создать команду с участниками (создаёт/обновляет пользователей)",
    response_model=TeamResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
async def create_team(team_in: TeamCreate, db: AsyncSession = Depends(get_db)):
    team, error = await TeamService.create_team(db, team_in)
    if error:
        if error == ErrorCode.TEAM_EXISTS:
            return JSONResponse(
                status_code=400, content={"error": {"code": error, "message": "team_name already exists"}}
            )
        if error == ErrorCode.USER_EXISTS:
            return JSONResponse(
                status_code=400,
                content={"error": {"code": error, "message": "one or more users already in another team"}},
            )

    return {"team": team}


@router.get(
    "/get", summary="Получить команду с участниками", response_model=Team, responses={404: {"model": ErrorResponse}}
)
async def get_team(team_name: str, db: AsyncSession = Depends(get_db)):
    team, error = await TeamService.get_team(db, team_name)
    if error:
        if error == ErrorCode.NOT_FOUND:
            return JSONResponse(status_code=404, content={"error": {"code": error, "message": "team not found"}})
    return team


@router.post("/deactivate", summary="Деактивировать пользователей в команде", response_model=dict, responses={404: {"model": ErrorResponse}})
async def deactivate_users(deactivate_in: TeamDeactivateRequest, db: AsyncSession = Depends(get_db)):
    error = await TeamService.deactivate_users(db, deactivate_in)
    if error:
        if error == ErrorCode.NOT_FOUND:
            return JSONResponse(status_code=404, content={"error": {"code": error, "message": "team not found"}})

    return {"status": "ok"}
