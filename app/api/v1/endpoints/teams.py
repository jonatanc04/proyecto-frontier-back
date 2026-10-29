from typing import Annotated

from fastapi import APIRouter, Query, Response

from app.schemas.catalog import TeamPlayerSchema, TeamSchema
from app.services.catalog_service import CatalogService
from app.schemas.management import (
    AddExistingTeamToSeasonRequest,
    CreateTeamPlayerRequest,
    CreateTeamRequest,
    DeleteTeamParticipationRequest,
    DeleteTeamPlayerRequest,
    MoveTeamPlayerRequest,
    UpdateTeamPlayerRequest,
)
from app.services.management_service import ManagementService


router = APIRouter()
service = CatalogService()
management_service = ManagementService()


@router.get("", response_model=list[TeamSchema])
def list_teams(
    include_players: Annotated[bool, Query(description="Incluye jugadores resueltos")] = False,
    league_id: Annotated[int | None, Query(description="Filtra por liga")] = None,
    season_id: Annotated[int | None, Query(description="Filtra por temporada")] = None,
) -> list[TeamSchema]:
    return service.list_teams(
        include_players=include_players,
        league_id=league_id,
        season_id=season_id,
    )


@router.get("/{team_id}", response_model=TeamSchema)
def get_team(
    team_id: int,
    include_players: Annotated[bool, Query(description="Incluye jugadores resueltos")] = True,
    league_id: Annotated[int | None, Query(description="Filtra por liga")] = None,
    season_id: Annotated[int | None, Query(description="Filtra por temporada")] = None,
) -> TeamSchema:
    return service.get_team(
        team_id=team_id,
        include_players=include_players,
        league_id=league_id,
        season_id=season_id,
    )


@router.get("/{team_id}/players", response_model=list[TeamPlayerSchema])
def get_team_players(
    team_id: int,
    include_coaches: Annotated[bool, Query(description="Incluye entrenadores")] = True,
    league_id: Annotated[int | None, Query(description="Filtra por liga")] = None,
    season_id: Annotated[int | None, Query(description="Filtra por temporada")] = None,
) -> list[TeamPlayerSchema]:
    return service.get_team_players(
        team_id=team_id,
        include_coaches=include_coaches,
        league_id=league_id,
        season_id=season_id,
    )


@router.post("", response_model=TeamSchema, status_code=201)
def create_team(payload: CreateTeamRequest) -> TeamSchema:
    return management_service.create_team(
        league_id=payload.league_id,
        season_id=payload.season_id,
        name=payload.name,
        logo=payload.logo,
        field=payload.field,
        field_element=payload.field_element,
    )


@router.post("/{team_id}/participations", response_model=TeamSchema, status_code=201)
def add_existing_team_to_season(
    team_id: int,
    payload: AddExistingTeamToSeasonRequest,
) -> TeamSchema:
    return management_service.add_existing_team_to_season(
        team_id=team_id,
        league_id=payload.league_id,
        season_id=payload.season_id,
    )


@router.delete("/{team_id}/participations", status_code=204)
def delete_team_participation(
    team_id: int,
    payload: DeleteTeamParticipationRequest,
) -> Response:
    management_service.delete_team_from_season(
        team_id=team_id,
        league_id=payload.league_id,
        season_id=payload.season_id,
    )
    return Response(status_code=204)


@router.post("/{team_id}/players", response_model=TeamPlayerSchema, status_code=201)
def create_team_player(
    team_id: int,
    payload: CreateTeamPlayerRequest,
) -> TeamPlayerSchema:
    return management_service.create_team_player(
        team_id=team_id,
        league_id=payload.league_id,
        season_id=payload.season_id,
        player_id=payload.player_id,
        average=payload.average,
        captain=payload.captain,
    )


@router.patch("/{team_id}/players/{player_id}", response_model=TeamPlayerSchema)
def update_team_player(
    team_id: int,
    player_id: int,
    payload: UpdateTeamPlayerRequest,
) -> TeamPlayerSchema:
    return management_service.update_team_player(
        team_id=team_id,
        player_id=player_id,
        league_id=payload.league_id,
        season_id=payload.season_id,
        average=payload.average,
        captain=payload.captain,
    )


@router.delete("/{team_id}/players/{player_id}", status_code=204)
def delete_team_player(
    team_id: int,
    player_id: int,
    payload: DeleteTeamPlayerRequest,
) -> Response:
    management_service.delete_team_player(
        team_id=team_id,
        player_id=player_id,
        league_id=payload.league_id,
        season_id=payload.season_id,
    )
    return Response(status_code=204)


@router.post("/players/transfer", response_model=TeamPlayerSchema)
def move_team_player(payload: MoveTeamPlayerRequest) -> TeamPlayerSchema:
    return management_service.move_team_player(
        league_id=payload.league_id,
        season_id=payload.season_id,
        player_id=payload.player_id,
        from_team_id=payload.from_team_id,
        to_team_id=payload.to_team_id,
        keep_player_data=payload.keep_player_data,
        transaction_type=payload.transaction_type,
    )
