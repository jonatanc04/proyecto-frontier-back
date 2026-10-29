from typing import Annotated

from fastapi import APIRouter, Query

from app.schemas.catalog import PlayerSchema, PlayersListResponse
from app.services.catalog_service import CatalogService


router = APIRouter()
service = CatalogService()


@router.get("", response_model=PlayersListResponse)
def list_players(
    search: Annotated[str | None, Query(description="Busca por nombre o apodo")] = None,
    active: Annotated[bool | None, Query(description="Filtra por estado activo")] = None,
    gender: Annotated[str | None, Query(description="Filtra por genero")] = None,
    element: Annotated[str | None, Query(description="Filtra por elemento")] = None,
    position: Annotated[str | None, Query(description="Filtra por posicion")] = None,
    page: Annotated[int, Query(ge=1, description="Pagina actual")] = 1,
    page_size: Annotated[int, Query(ge=1, le=200, description="Tamano de pagina")] = 50,
) -> PlayersListResponse:
    return service.list_players(
        search=search,
        active=active,
        gender=gender,
        element=element,
        position=position,
        page=page,
        page_size=page_size,
    )


@router.get("/{player_id}", response_model=PlayerSchema)
def get_player(player_id: int) -> PlayerSchema:
    return service.get_player(player_id)
