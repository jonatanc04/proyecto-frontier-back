from fastapi import APIRouter

from app.api.v1.endpoints import health, leagues, metadata, players, seasons, teams, transfers


api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(leagues.router, prefix="/leagues", tags=["leagues"])
api_router.include_router(seasons.router, prefix="/seasons", tags=["seasons"])
api_router.include_router(players.router, prefix="/players", tags=["players"])
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])
api_router.include_router(transfers.router, prefix="/transfers", tags=["transfers"])
api_router.include_router(metadata.router, prefix="/metadata", tags=["metadata"])
