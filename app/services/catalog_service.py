import math

from fastapi import HTTPException, status

from app.models.domain import Character, League, Season, Team, TeamParticipation, TeamRosterEntry
from app.repositories.json_repository import JsonRepository
from app.schemas.catalog import (
    LeagueSchema,
    MetadataItemSchema,
    MetadataListResponse,
    PaginationSchema,
    PlayerSchema,
    PlayersListResponse,
    SeasonSchema,
    TeamPlayerSchema,
    TeamParticipationSchema,
    TeamSchema,
    TeamSummarySchema,
)


class CatalogService:
    def __init__(self, repository: JsonRepository | None = None) -> None:
        self.repository = repository or JsonRepository()

    def list_players(
        self,
        search: str | None = None,
        active: bool | None = None,
        gender: str | None = None,
        element: str | None = None,
        position: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> PlayersListResponse:
        players = self.repository.get_players()
        filtered_players = [
            player
            for player in players
            if self._matches_player_filters(
                player=player,
                search=search,
                active=active,
                gender=gender,
                element=element,
                position=position,
            )
        ]
        filtered_players.sort(key=lambda player: (player.name.lower(), player.id))

        total = len(filtered_players)
        total_pages = max(1, math.ceil(total / page_size))
        start = (page - 1) * page_size
        end = start + page_size
        items = [self._serialize_player(player) for player in filtered_players[start:end]]

        return PlayersListResponse(
            items=items,
            pagination=PaginationSchema(
                page=page,
                page_size=page_size,
                total=total,
                total_pages=total_pages,
            ),
        )

    def get_player(self, player_id: int) -> PlayerSchema:
        character = self._players_by_id().get(player_id)
        if character is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No existe ningun jugador con id {player_id}.",
            )
        return self._serialize_player(character)

    def list_leagues(self) -> list[LeagueSchema]:
        leagues = self.repository.get_leagues()
        return [self._serialize_league(league) for league in leagues]

    def list_seasons(self, league_id: int | None = None) -> list[SeasonSchema]:
        seasons = self.repository.get_seasons()
        if league_id is not None:
            seasons = [season for season in seasons if season.id_league == league_id]
        return [self._serialize_season(season) for season in seasons]

    def list_teams(
        self,
        include_players: bool = False,
        league_id: int | None = None,
        season_id: int | None = None,
    ) -> list[TeamSchema]:
        teams = self._filter_teams_by_participation(
            teams=self.repository.get_teams(),
            league_id=league_id,
            season_id=season_id,
        )
        return [
            self._serialize_team(
                team,
                include_players=include_players,
                league_id=league_id,
                season_id=season_id,
            )
            for team in teams
        ]

    def get_team(
        self,
        team_id: int,
        include_players: bool = True,
        league_id: int | None = None,
        season_id: int | None = None,
    ) -> TeamSchema:
        team = next((team for team in self.repository.get_teams() if team.id == team_id), None)
        if team is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No existe ningun equipo con id {team_id}.",
            )
        self._ensure_team_participation(team=team, league_id=league_id, season_id=season_id)
        return self._serialize_team(
            team,
            include_players=include_players,
            league_id=league_id,
            season_id=season_id,
        )

    def get_team_players(
        self,
        team_id: int,
        include_coaches: bool = True,
        league_id: int | None = None,
        season_id: int | None = None,
    ) -> list[TeamPlayerSchema]:
        team = next((team for team in self.repository.get_teams() if team.id == team_id), None)
        if team is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No existe ningun equipo con id {team_id}.",
            )
        self._ensure_team_participation(team=team, league_id=league_id, season_id=season_id)

        resolved_players = [
            self._serialize_team_player(team_player)
            for team_player in self._get_roster_entries_for_team(
                team_id=team_id,
                league_id=league_id,
                season_id=season_id,
            )
        ]
        if include_coaches:
            return resolved_players
        return [player for player in resolved_players if player.is_coach is False]

    def get_elements_metadata(self) -> MetadataListResponse:
        items = [
            MetadataItemSchema(key=key, value=value)
            for key, value in self.repository.get_elements().items()
        ]
        return MetadataListResponse(items=items)

    def get_genders_metadata(self) -> MetadataListResponse:
        items = [
            MetadataItemSchema(key=key, value=value)
            for key, value in self.repository.get_genders().items()
        ]
        return MetadataListResponse(items=items)

    def _matches_player_filters(
        self,
        player: Character,
        search: str | None,
        active: bool | None,
        gender: str | None,
        element: str | None,
        position: str | None,
    ) -> bool:
        if active is not None and player.active is not active:
            return False

        if gender and player.gender.lower() != gender.lower():
            return False

        if element and player.element.upper() != element.upper():
            return False

        if position and player.position.upper() != position.upper():
            return False

        if search:
            normalized_search = search.strip().lower()
            searchable_text = f"{player.name} {player.nickname}".lower()
            if normalized_search not in searchable_text:
                return False

        return True

    def _players_by_id(self) -> dict[int, Character]:
        return {player.id: player for player in self.repository.get_players()}

    def _players_by_name(self) -> dict[str, Character]:
        return {
            player.name.strip().lower(): player
            for player in self.repository.get_players()
        }

    def _resolve_team_player_character(self, team_player: TeamRosterEntry) -> Character | None:
        if isinstance(team_player.id_player, int):
            return self._players_by_id().get(team_player.id_player)

        if isinstance(team_player.id_player, str):
            return self._players_by_name().get(team_player.id_player.strip().lower())

        return None

    def _serialize_league(self, league: League) -> LeagueSchema:
        return LeagueSchema(id=league.id, name=league.name)

    def _serialize_season(self, season: Season) -> SeasonSchema:
        return SeasonSchema(id=season.id, name=season.name, id_league=season.id_league)

    def _serialize_player(self, player: Character) -> PlayerSchema:
        return PlayerSchema(
            id=player.id,
            name=player.name,
            nickname=player.nickname,
            img=player.img,
            gender=player.gender,
            element=player.element,
            position=player.position,
            active=player.active,
        )

    def _serialize_team_player(self, team_player: TeamRosterEntry) -> TeamPlayerSchema:
        character = self._resolve_team_player_character(team_player)
        player_id = (
            team_player.id_player
            if isinstance(team_player.id_player, int)
            else character.id if character else None
        )
        fallback_name = (
            team_player.id_player
            if isinstance(team_player.id_player, str)
            else f"Jugador {team_player.id_player}"
        )

        return TeamPlayerSchema(
            player_id=player_id,
            team_id=team_player.team_id,
            id_league=team_player.id_league,
            id_season=team_player.id_season,
            name=character.name if character else fallback_name,
            nickname=character.nickname if character else "",
            img=character.img if character else "",
            gender=character.gender if character else "",
            element=character.element if character else "",
            position=character.position if character else "",
            active=character.active if character else None,
            average=team_player.average,
            captain=team_player.captain,
            is_coach=team_player.average is None,
        )

    def _build_team_summary(self, resolved_players: list[TeamPlayerSchema]) -> TeamSummarySchema:
        normal_players = [player for player in resolved_players if player.is_coach is False]
        return TeamSummarySchema(
            total_entries=len(resolved_players),
            total_players=len(normal_players),
            total_active_players=sum(1 for player in normal_players if player.active is True),
            total_coaches=sum(1 for player in resolved_players if player.is_coach is True),
        )

    def _serialize_participation(self, participation: TeamParticipation) -> TeamParticipationSchema:
        return TeamParticipationSchema(
            id_league=participation.id_league,
            id_season=participation.id_season,
        )

    def _get_roster_entries_for_team(
        self,
        team_id: int,
        league_id: int | None = None,
        season_id: int | None = None,
    ) -> list[TeamRosterEntry]:
        entries = [
            entry
            for entry in self.repository.get_team_roster_entries()
            if entry.team_id == team_id
        ]

        if league_id is not None:
            entries = [entry for entry in entries if entry.id_league == league_id]

        if season_id is not None:
            entries = [entry for entry in entries if entry.id_season == season_id]

        return entries

    def _matches_participation_filter(
        self,
        participation: TeamParticipation,
        league_id: int | None,
        season_id: int | None,
    ) -> bool:
        if league_id is not None and participation.id_league != league_id:
            return False
        if season_id is not None and participation.id_season != season_id:
            return False
        return True

    def _filter_teams_by_participation(
        self,
        teams: list[Team],
        league_id: int | None,
        season_id: int | None,
    ) -> list[Team]:
        if league_id is None and season_id is None:
            return teams
        return [
            team
            for team in teams
            if any(
                self._matches_participation_filter(
                    participation=participation,
                    league_id=league_id,
                    season_id=season_id,
                )
                for participation in team.participations
            )
        ]

    def _ensure_team_participation(
        self,
        team: Team,
        league_id: int | None,
        season_id: int | None,
    ) -> None:
        if league_id is None and season_id is None:
            return
        if any(
            self._matches_participation_filter(
                participation=participation,
                league_id=league_id,
                season_id=season_id,
            )
            for participation in team.participations
        ):
            return
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"El equipo con id {team.id} no participa en la liga/temporada solicitada."
            ),
        )

    def _serialize_team(
        self,
        team: Team,
        include_players: bool,
        league_id: int | None = None,
        season_id: int | None = None,
    ) -> TeamSchema:
        roster_entries = self._get_roster_entries_for_team(
            team_id=team.id,
            league_id=league_id,
            season_id=season_id,
        )
        resolved_players = [self._serialize_team_player(team_player) for team_player in roster_entries]
        participations = [
            self._serialize_participation(participation)
            for participation in team.participations
            if self._matches_participation_filter(
                participation=participation,
                league_id=league_id,
                season_id=season_id,
            )
        ]
        if league_id is None and season_id is None:
            participations = [
                self._serialize_participation(participation)
                for participation in team.participations
            ]
        return TeamSchema(
            id=team.id,
            name=team.name,
            logo=team.logo,
            field=team.field,
            field_element=team.field_element,
            participations=participations,
            summary=self._build_team_summary(resolved_players),
            players=resolved_players if include_players else [],
        )
