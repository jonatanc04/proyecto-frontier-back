from typing import Annotated

from fastapi import APIRouter, Query

from app.schemas.management import MoveTeamPlayerRequest, TransferTransactionSchema
from app.services.management_service import ManagementService


router = APIRouter()
management_service = ManagementService()


@router.get("", response_model=list[TransferTransactionSchema])
def list_transfers(
    league_id: Annotated[int | None, Query(description="Filtra por liga")] = None,
    season_id: Annotated[int | None, Query(description="Filtra por temporada")] = None,
) -> list[TransferTransactionSchema]:
    return management_service.list_transfer_transactions(
        league_id=league_id,
        season_id=season_id,
    )


@router.post("", response_model=TransferTransactionSchema, status_code=201)
def create_transfer(payload: MoveTeamPlayerRequest) -> TransferTransactionSchema:
    management_service.move_team_player(
        league_id=payload.league_id,
        season_id=payload.season_id,
        player_id=payload.player_id,
        from_team_id=payload.from_team_id,
        to_team_id=payload.to_team_id,
        keep_player_data=payload.keep_player_data,
        transaction_type=payload.transaction_type,
    )
    return management_service.list_transfer_transactions(
        league_id=payload.league_id,
        season_id=payload.season_id,
    )[0]
