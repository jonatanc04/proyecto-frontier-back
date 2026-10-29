from typing import Annotated

from fastapi import APIRouter, Query, Response

from app.schemas.catalog import SeasonSchema
from app.services.catalog_service import CatalogService
from app.schemas.management import CreateSeasonRequest, UpdateSeasonRequest
from app.services.management_service import ManagementService


router = APIRouter()
service = CatalogService()
management_service = ManagementService()


@router.get("", response_model=list[SeasonSchema])
def list_seasons(
    league_id: Annotated[int | None, Query(description="Filtra temporadas por liga")] = None,
) -> list[SeasonSchema]:
    return service.list_seasons(league_id=league_id)


@router.post("", response_model=SeasonSchema, status_code=201)
def create_season(payload: CreateSeasonRequest) -> SeasonSchema:
    return management_service.create_season(
        league_id=payload.league_id,
        name=payload.name,
        source_season_id=payload.source_season_id,
        copy_teams=payload.copy_teams,
        copy_players=payload.copy_players,
        copy_player_data=payload.copy_player_data,
    )


@router.patch("/{season_id}", response_model=SeasonSchema)
def update_season(season_id: int, payload: UpdateSeasonRequest) -> SeasonSchema:
    return management_service.update_season(
        season_id=season_id,
        league_id=payload.league_id,
        name=payload.name,
    )


@router.delete("/{season_id}", status_code=204)
def delete_season(
    season_id: int,
    league_id: Annotated[int, Query(description="Liga a la que pertenece la temporada")],
) -> Response:
    management_service.delete_season(league_id=league_id, season_id=season_id)
    return Response(status_code=204)
