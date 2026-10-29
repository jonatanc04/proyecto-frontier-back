from pydantic import BaseModel, Field, field_validator

from app.schemas.catalog import LeagueSchema, SeasonSchema, TeamPlayerSchema, TeamSchema


class CreateLeagueRequest(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("El nombre de la liga es obligatorio.")
        return cleaned_value


class UpdateLeagueRequest(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("El nombre de la liga es obligatorio.")
        return cleaned_value


class CreateSeasonRequest(BaseModel):
    league_id: int
    name: str
    source_season_id: int | None = None
    copy_teams: bool = False
    copy_players: bool = False
    copy_player_data: bool = False

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("El nombre de la temporada es obligatorio.")
        return cleaned_value


class UpdateSeasonRequest(BaseModel):
    league_id: int
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("El nombre de la temporada es obligatorio.")
        return cleaned_value


class CreateTeamRequest(BaseModel):
    league_id: int
    season_id: int
    name: str
    logo: str = ""
    field: str = ""
    field_element: str = ""

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("El nombre del equipo es obligatorio.")
        return cleaned_value

    @field_validator("field_element")
    @classmethod
    def normalize_field_element(cls, value: str) -> str:
        return value.strip().upper()


class AddExistingTeamToSeasonRequest(BaseModel):
    league_id: int
    season_id: int


class DeleteTeamParticipationRequest(BaseModel):
    league_id: int
    season_id: int


class CreateTeamPlayerRequest(BaseModel):
    team_id: int
    league_id: int
    season_id: int
    player_id: int
    average: int | None = None
    captain: int = Field(default=0, ge=0, le=2)


class UpdateTeamPlayerRequest(BaseModel):
    league_id: int
    season_id: int
    average: int | None = None
    captain: int = Field(default=0, ge=0, le=2)


class MoveTeamPlayerRequest(BaseModel):
    league_id: int
    season_id: int
    player_id: int
    from_team_id: int
    to_team_id: int
    transaction_type: str = "fichaje"
    keep_player_data: bool = True

    @field_validator("transaction_type")
    @classmethod
    def validate_transaction_type(cls, value: str) -> str:
        normalized_value = value.strip().lower()
        if normalized_value not in {"fichaje", "cesion"}:
            raise ValueError("El tipo de transaccion debe ser fichaje o cesion.")
        return normalized_value


class DeleteTeamPlayerRequest(BaseModel):
    league_id: int
    season_id: int


class ManagementStateResponse(BaseModel):
    leagues: list[LeagueSchema]
    seasons: list[SeasonSchema]
    teams: list[TeamSchema]


class TeamPlayerOperationResponse(BaseModel):
    item: TeamPlayerSchema


class TransferTransactionSchema(BaseModel):
    id: int
    league_id: int
    season_id: int
    player_id: int
    player_name: str
    from_team_id: int
    from_team_name: str
    to_team_id: int
    to_team_name: str
    transaction_type: str
    average: int | None
    captain: int
    created_at: str
