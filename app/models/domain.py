from dataclasses import dataclass


@dataclass(frozen=True)
class Character:
    id: int
    name: str
    nickname: str
    img: str
    gender: str
    element: str
    position: str
    active: bool


@dataclass(frozen=True)
class League:
    id: int
    name: str


@dataclass(frozen=True)
class Season:
    id: int
    name: str
    id_league: int


@dataclass(frozen=True)
class TeamParticipation:
    id_league: int
    id_season: int


@dataclass(frozen=True)
class TeamRosterEntry:
    team_id: int
    id_player: int | str
    id_league: int
    id_season: int
    average: int | None
    captain: int = 0


@dataclass(frozen=True)
class Team:
    id: int
    name: str
    logo: str
    field: str
    field_element: str
    participations: list[TeamParticipation]


@dataclass(frozen=True)
class TransferTransaction:
    id: int
    league_id: int
    season_id: int
    player_id: int
    from_team_id: int
    to_team_id: int
    transaction_type: str
    average: int | None
    captain: int
    created_at: str
