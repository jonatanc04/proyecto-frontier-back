from fastapi import APIRouter, Response

from app.schemas.catalog import LeagueSchema
from app.services.catalog_service import CatalogService
from app.schemas.management import CreateLeagueRequest, UpdateLeagueRequest
from app.services.management_service import ManagementService


router = APIRouter()
service = CatalogService()
management_service = ManagementService()


@router.get("", response_model=list[LeagueSchema])
def list_leagues() -> list[LeagueSchema]:
    return service.list_leagues()


@router.post("", response_model=LeagueSchema, status_code=201)
def create_league(payload: CreateLeagueRequest) -> LeagueSchema:
    return management_service.create_league(name=payload.name)


@router.patch("/{league_id}", response_model=LeagueSchema)
def update_league(league_id: int, payload: UpdateLeagueRequest) -> LeagueSchema:
    return management_service.update_league(league_id=league_id, name=payload.name)


@router.delete("/{league_id}", status_code=204)
def delete_league(league_id: int) -> Response:
    management_service.delete_league(league_id)
    return Response(status_code=204)
