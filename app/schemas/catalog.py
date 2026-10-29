from pydantic import BaseModel, Field


class PaginationSchema(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class PlayerSchema(BaseModel):
    id: int
    name: str
    nickname: str
    img: str
    gender: str
    element: str
    position: str
    active: bool


class PlayersListResponse(BaseModel):
    items: list[PlayerSchema]
    pagination: PaginationSchema


class LeagueSchema(BaseModel):
    id: int
    name: str


class SeasonSchema(BaseModel):
    id: int
    name: str
    id_league: int


class TeamParticipationSchema(BaseModel):
    id_league: int
    id_season: int


class TeamPlayerSchema(BaseModel):
    player_id: int | None
    team_id: int
    id_league: int
    id_season: int
    name: str
    nickname: str
    img: str
    gender: str
    element: str
    position: str
    active: bool | None
    average: int | None
    captain: int = 0
    is_coach: bool


class TeamSummarySchema(BaseModel):
    total_entries: int
    total_players: int
    total_active_players: int
    total_coaches: int


class TeamSchema(BaseModel):
    id: int
    name: str
    logo: str
    field: str
    field_element: str
    participations: list[TeamParticipationSchema] = Field(default_factory=list)
    summary: TeamSummarySchema
    players: list[TeamPlayerSchema] = Field(default_factory=list)


class MetadataItemSchema(BaseModel):
    key: str
    value: str


class MetadataListResponse(BaseModel):
    items: list[MetadataItemSchema]
