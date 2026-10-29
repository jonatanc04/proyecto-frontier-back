from datetime import datetime, UTC

from fastapi import HTTPException, status

from app.models.domain import League, Season, Team, TeamParticipation, TeamRosterEntry, TransferTransaction
from app.repositories.json_repository import JsonRepository
from app.schemas.catalog import LeagueSchema, SeasonSchema, TeamPlayerSchema, TeamSchema
from app.schemas.management import TransferTransactionSchema
from app.services.catalog_service import CatalogService


class ManagementService:
    def __init__(self, repository: JsonRepository | None = None) -> None:
        self.repository = repository or JsonRepository()
        self.catalog_service = CatalogService(self.repository)

    def create_league(self, name: str) -> LeagueSchema:
        leagues = self.repository.get_leagues()

        if any(league.name.strip().lower() == name.strip().lower() for league in leagues):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una liga con ese nombre.",
            )

        league = League(
            id=self._next_id([league.id for league in leagues]),
            name=name.strip(),
        )
        leagues.append(league)
        self.repository.save_leagues(leagues)
        return self.catalog_service._serialize_league(league)

    def update_league(self, league_id: int, name: str) -> LeagueSchema:
        leagues = self.repository.get_leagues()
        league_index = self._find_league_index(leagues, league_id)

        if any(
            league.id != league_id and league.name.strip().lower() == name.strip().lower()
            for league in leagues
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una liga con ese nombre.",
            )

        updated_league = League(
            id=league_id,
            name=name.strip(),
        )
        leagues[league_index] = updated_league
        self.repository.save_leagues(leagues)
        return self.catalog_service._serialize_league(updated_league)

    def delete_league(self, league_id: int) -> None:
        leagues = self.repository.get_leagues()
        self._get_league_or_404(league_id)

        remaining_leagues = [
            league
            for league in leagues
            if league.id != league_id
        ]
        seasons_to_delete = {
            season.id
            for season in self.repository.get_seasons()
            if season.id_league == league_id
        }
        remaining_seasons = [
            season
            for season in self.repository.get_seasons()
            if season.id_league != league_id
        ]
        remaining_roster_entries = [
            entry
            for entry in self.repository.get_team_roster_entries()
            if entry.id_league != league_id
        ]
        remaining_transactions = [
            transaction
            for transaction in self.repository.get_transfer_transactions()
            if transaction.league_id != league_id
        ]
        remaining_teams = self._remove_participations(
            teams=self.repository.get_teams(),
            predicate=lambda participation: participation.id_league == league_id
            or participation.id_season in seasons_to_delete,
        )

        self.repository.save_leagues(remaining_leagues)
        self.repository.save_seasons(remaining_seasons)
        self.repository.save_team_roster_entries(remaining_roster_entries)
        self.repository.save_transfer_transactions(remaining_transactions)
        self.repository.save_teams(remaining_teams)

    def create_season(
        self,
        league_id: int,
        name: str,
        source_season_id: int | None = None,
        copy_teams: bool = False,
        copy_players: bool = False,
        copy_player_data: bool = False,
    ) -> SeasonSchema:
        self._get_league_or_404(league_id)
        seasons = self.repository.get_seasons()

        if copy_player_data and copy_players is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pueden copiar los datos de jugadores sin copiar antes los jugadores.",
            )

        if copy_players and copy_teams is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pueden copiar jugadores sin copiar antes los equipos.",
            )

        if copy_teams and source_season_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debes indicar una temporada origen para copiar equipos o plantillas.",
            )

        if any(
            season.id_league == league_id and season.name.strip().lower() == name.strip().lower()
            for season in seasons
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una temporada con ese nombre dentro de la liga.",
            )

        source_season = None
        if source_season_id is not None:
            source_season = next(
                (
                    season
                    for season in seasons
                    if season.id == source_season_id and season.id_league == league_id
                ),
                None,
            )
            if source_season is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="La temporada origen no existe dentro de la liga indicada.",
                )

        season = Season(
            id=self._next_id([season.id for season in seasons]),
            name=name.strip(),
            id_league=league_id,
        )
        seasons.append(season)
        self.repository.save_seasons(seasons)

        if copy_teams and source_season is not None:
            self._copy_season_structure(
                league_id=league_id,
                source_season_id=source_season.id,
                target_season_id=season.id,
                copy_players=copy_players,
                copy_player_data=copy_player_data,
            )

        return self.catalog_service._serialize_season(season)

    def update_season(self, season_id: int, league_id: int, name: str) -> SeasonSchema:
        self._get_league_or_404(league_id)
        seasons = self.repository.get_seasons()
        season_index = self._find_season_index(seasons, season_id)
        current_season = seasons[season_index]

        if any(
            season.id != season_id
            and season.id_league == league_id
            and season.name.strip().lower() == name.strip().lower()
            for season in seasons
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una temporada con ese nombre dentro de la liga.",
            )

        updated_season = Season(
            id=current_season.id,
            name=name.strip(),
            id_league=league_id,
        )
        seasons[season_index] = updated_season
        self.repository.save_seasons(seasons)

        if current_season.id_league != league_id:
            updated_teams: list[Team] = []
            for team in self.repository.get_teams():
                updated_participations = [
                    TeamParticipation(
                        id_league=league_id,
                        id_season=participation.id_season,
                    )
                    if participation.id_league == current_season.id_league
                    and participation.id_season == season_id
                    else participation
                    for participation in team.participations
                ]
                updated_teams.append(
                    Team(
                        id=team.id,
                        name=team.name,
                        logo=team.logo,
                        field=team.field,
                        field_element=team.field_element,
                        participations=updated_participations,
                    )
                )
            self.repository.save_teams(updated_teams)

            updated_roster_entries = [
                TeamRosterEntry(
                    team_id=entry.team_id,
                    id_player=entry.id_player,
                    id_league=league_id if (
                        entry.id_league == current_season.id_league
                        and entry.id_season == season_id
                    ) else entry.id_league,
                    id_season=entry.id_season,
                    average=entry.average,
                    captain=entry.captain,
                )
                for entry in self.repository.get_team_roster_entries()
            ]
            self.repository.save_team_roster_entries(updated_roster_entries)

            updated_transactions = [
                TransferTransaction(
                    id=transaction.id,
                    league_id=league_id if (
                        transaction.league_id == current_season.id_league
                        and transaction.season_id == season_id
                    ) else transaction.league_id,
                    season_id=transaction.season_id,
                    player_id=transaction.player_id,
                    from_team_id=transaction.from_team_id,
                    to_team_id=transaction.to_team_id,
                    transaction_type=transaction.transaction_type,
                    average=transaction.average,
                    captain=transaction.captain,
                    created_at=transaction.created_at,
                )
                for transaction in self.repository.get_transfer_transactions()
            ]
            self.repository.save_transfer_transactions(updated_transactions)

        return self.catalog_service._serialize_season(updated_season)

    def delete_season(self, league_id: int, season_id: int) -> None:
        self._get_season_or_404(league_id=league_id, season_id=season_id)

        remaining_seasons = [
            season
            for season in self.repository.get_seasons()
            if not (season.id == season_id and season.id_league == league_id)
        ]
        remaining_roster_entries = [
            entry
            for entry in self.repository.get_team_roster_entries()
            if not (entry.id_league == league_id and entry.id_season == season_id)
        ]
        remaining_transactions = [
            transaction
            for transaction in self.repository.get_transfer_transactions()
            if not (transaction.league_id == league_id and transaction.season_id == season_id)
        ]
        remaining_teams = self._remove_participations(
            teams=self.repository.get_teams(),
            predicate=lambda participation: (
                participation.id_league == league_id
                and participation.id_season == season_id
            ),
        )

        self.repository.save_seasons(remaining_seasons)
        self.repository.save_team_roster_entries(remaining_roster_entries)
        self.repository.save_transfer_transactions(remaining_transactions)
        self.repository.save_teams(remaining_teams)

    def create_team(
        self,
        league_id: int,
        season_id: int,
        name: str,
        logo: str = "",
        field: str = "",
        field_element: str = "",
    ) -> TeamSchema:
        self._get_season_or_404(league_id=league_id, season_id=season_id)
        teams = self.repository.get_teams()

        team = Team(
            id=self._next_id([team.id for team in teams]),
            name=name.strip(),
            logo=logo.strip(),
            field=field.strip(),
            field_element=field_element.strip().upper(),
            participations=[TeamParticipation(id_league=league_id, id_season=season_id)],
        )
        teams.append(team)
        self.repository.save_teams(teams)
        return self.catalog_service.get_team(team.id, include_players=False, league_id=league_id, season_id=season_id)

    def add_existing_team_to_season(
        self,
        team_id: int,
        league_id: int,
        season_id: int,
    ) -> TeamSchema:
        self._get_season_or_404(league_id=league_id, season_id=season_id)
        teams = self.repository.get_teams()
        team_index = self._find_team_index(teams, team_id)
        team = teams[team_index]

        if any(
            participation.id_league == league_id and participation.id_season == season_id
            for participation in team.participations
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ese equipo ya participa en la temporada seleccionada.",
            )

        updated_team = Team(
            id=team.id,
            name=team.name,
            logo=team.logo,
            field=team.field,
            field_element=team.field_element,
            participations=[
                *team.participations,
                TeamParticipation(id_league=league_id, id_season=season_id),
            ],
        )
        teams[team_index] = updated_team
        self.repository.save_teams(teams)
        return self.catalog_service.get_team(team.id, include_players=False, league_id=league_id, season_id=season_id)

    def delete_team_from_season(self, team_id: int, league_id: int, season_id: int) -> None:
        teams = self.repository.get_teams()
        team_index = self._find_team_index(teams, team_id)
        team = teams[team_index]

        remaining_participations = [
            participation
            for participation in team.participations
            if not (
                participation.id_league == league_id
                and participation.id_season == season_id
            )
        ]

        if len(remaining_participations) == len(team.participations):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ese equipo no participa en la temporada indicada.",
            )

        roster_entries = [
            entry
            for entry in self.repository.get_team_roster_entries()
            if not (
                entry.team_id == team_id
                and entry.id_league == league_id
                and entry.id_season == season_id
            )
        ]
        self.repository.save_team_roster_entries(roster_entries)

        if remaining_participations:
            teams[team_index] = Team(
                id=team.id,
                name=team.name,
                logo=team.logo,
                field=team.field,
                field_element=team.field_element,
                participations=remaining_participations,
            )
        else:
            del teams[team_index]

        self.repository.save_teams(teams)

    def create_team_player(
        self,
        team_id: int,
        league_id: int,
        season_id: int,
        player_id: int,
        average: int | None,
        captain: int,
    ) -> TeamPlayerSchema:
        self._ensure_team_participation(team_id=team_id, league_id=league_id, season_id=season_id)
        self._ensure_master_player_exists(player_id)
        roster_entries = self.repository.get_team_roster_entries()

        if any(
            entry.team_id == team_id
            and entry.id_league == league_id
            and entry.id_season == season_id
            and entry.id_player == player_id
            for entry in roster_entries
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ese jugador ya esta en el equipo para esa temporada.",
            )

        if any(
            entry.id_league == league_id
            and entry.id_season == season_id
            and entry.id_player == player_id
            and entry.team_id != team_id
            for entry in roster_entries
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ese jugador ya pertenece a otro equipo en la misma temporada.",
            )

        roster_entry = TeamRosterEntry(
            team_id=team_id,
            id_player=player_id,
            id_league=league_id,
            id_season=season_id,
            average=average,
            captain=captain,
        )
        roster_entries.append(roster_entry)
        self.repository.save_team_roster_entries(roster_entries)
        return self.catalog_service._serialize_team_player(roster_entry)

    def update_team_player(
        self,
        team_id: int,
        player_id: int,
        league_id: int,
        season_id: int,
        average: int | None,
        captain: int,
    ) -> TeamPlayerSchema:
        roster_entries = self.repository.get_team_roster_entries()
        entry_index = self._find_roster_entry_index(
            roster_entries=roster_entries,
            team_id=team_id,
            player_id=player_id,
            league_id=league_id,
            season_id=season_id,
        )
        updated_entry = TeamRosterEntry(
            team_id=team_id,
            id_player=player_id,
            id_league=league_id,
            id_season=season_id,
            average=average,
            captain=captain,
        )
        roster_entries[entry_index] = updated_entry
        self.repository.save_team_roster_entries(roster_entries)
        return self.catalog_service._serialize_team_player(updated_entry)

    def delete_team_player(
        self,
        team_id: int,
        player_id: int,
        league_id: int,
        season_id: int,
    ) -> None:
        roster_entries = self.repository.get_team_roster_entries()
        entry_index = self._find_roster_entry_index(
            roster_entries=roster_entries,
            team_id=team_id,
            player_id=player_id,
            league_id=league_id,
            season_id=season_id,
        )
        del roster_entries[entry_index]
        self.repository.save_team_roster_entries(roster_entries)

    def move_team_player(
        self,
        league_id: int,
        season_id: int,
        player_id: int,
        from_team_id: int,
        to_team_id: int,
        keep_player_data: bool,
        transaction_type: str = "fichaje",
    ) -> TeamPlayerSchema:
        self._ensure_team_participation(team_id=from_team_id, league_id=league_id, season_id=season_id)
        self._ensure_team_participation(team_id=to_team_id, league_id=league_id, season_id=season_id)
        roster_entries = self.repository.get_team_roster_entries()

        if any(
            entry.team_id == to_team_id
            and entry.id_league == league_id
            and entry.id_season == season_id
            and entry.id_player == player_id
            for entry in roster_entries
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ese jugador ya existe en el equipo de destino.",
            )

        entry_index = self._find_roster_entry_index(
            roster_entries=roster_entries,
            team_id=from_team_id,
            player_id=player_id,
            league_id=league_id,
            season_id=season_id,
        )
        current_entry = roster_entries[entry_index]
        moved_entry = TeamRosterEntry(
            team_id=to_team_id,
            id_player=player_id,
            id_league=league_id,
            id_season=season_id,
            average=current_entry.average if keep_player_data else None,
            captain=current_entry.captain if keep_player_data else 0,
        )
        roster_entries[entry_index] = moved_entry
        self.repository.save_team_roster_entries(roster_entries)
        self._register_transfer_transaction(
            league_id=league_id,
            season_id=season_id,
            player_id=player_id,
            from_team_id=from_team_id,
            to_team_id=to_team_id,
            transaction_type=transaction_type,
            average=moved_entry.average,
            captain=moved_entry.captain,
        )
        return self.catalog_service._serialize_team_player(moved_entry)

    def list_transfer_transactions(
        self,
        league_id: int | None = None,
        season_id: int | None = None,
    ) -> list[TransferTransactionSchema]:
        transactions = self.repository.get_transfer_transactions()
        if league_id is not None:
            transactions = [
                transaction for transaction in transactions if transaction.league_id == league_id
            ]
        if season_id is not None:
            transactions = [
                transaction for transaction in transactions if transaction.season_id == season_id
            ]
        transactions.sort(key=lambda transaction: transaction.id, reverse=True)
        return [
            self._serialize_transfer_transaction(transaction)
            for transaction in transactions
        ]

    def _copy_season_structure(
        self,
        league_id: int,
        source_season_id: int,
        target_season_id: int,
        copy_players: bool,
        copy_player_data: bool,
    ) -> None:
        teams = self.repository.get_teams()
        updated_teams: list[Team] = []
        copied_team_ids: list[int] = []

        for team in teams:
            participates_in_source = any(
                participation.id_league == league_id and participation.id_season == source_season_id
                for participation in team.participations
            )

            if not participates_in_source:
                updated_teams.append(team)
                continue

            copied_team_ids.append(team.id)
            updated_teams.append(
                Team(
                    id=team.id,
                    name=team.name,
                    logo=team.logo,
                    field=team.field,
                    field_element=team.field_element,
                    participations=[
                        *team.participations,
                        TeamParticipation(id_league=league_id, id_season=target_season_id),
                    ],
                )
            )

        self.repository.save_teams(updated_teams)

        if not copy_players:
            return

        roster_entries = self.repository.get_team_roster_entries()
        copied_entries = [
            TeamRosterEntry(
                team_id=entry.team_id,
                id_player=entry.id_player,
                id_league=league_id,
                id_season=target_season_id,
                average=entry.average if copy_player_data else None,
                captain=entry.captain if copy_player_data else 0,
            )
            for entry in roster_entries
            if entry.id_league == league_id
            and entry.id_season == source_season_id
            and entry.team_id in copied_team_ids
        ]
        self.repository.save_team_roster_entries([*roster_entries, *copied_entries])

    def _ensure_team_participation(self, team_id: int, league_id: int, season_id: int) -> None:
        teams = self.repository.get_teams()
        team = next((team for team in teams if team.id == team_id), None)
        if team is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El equipo indicado no existe.",
            )
        if any(
            participation.id_league == league_id and participation.id_season == season_id
            for participation in team.participations
        ):
            return
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El equipo no participa en la liga y temporada indicadas.",
        )

    def _register_transfer_transaction(
        self,
        league_id: int,
        season_id: int,
        player_id: int,
        from_team_id: int,
        to_team_id: int,
        transaction_type: str,
        average: int | None,
        captain: int,
    ) -> None:
        transactions = self.repository.get_transfer_transactions()
        transactions.append(
            TransferTransaction(
                id=self._next_id([transaction.id for transaction in transactions]),
                league_id=league_id,
                season_id=season_id,
                player_id=player_id,
                from_team_id=from_team_id,
                to_team_id=to_team_id,
                transaction_type=transaction_type,
                average=average,
                captain=captain,
                created_at=datetime.now(UTC).isoformat(),
            )
        )
        self.repository.save_transfer_transactions(transactions)

    def _serialize_transfer_transaction(
        self,
        transaction: TransferTransaction,
    ) -> TransferTransactionSchema:
        player = self.catalog_service._players_by_id().get(transaction.player_id)
        teams_by_id = {team.id: team for team in self.repository.get_teams()}
        from_team = teams_by_id.get(transaction.from_team_id)
        to_team = teams_by_id.get(transaction.to_team_id)

        return TransferTransactionSchema(
            id=transaction.id,
            league_id=transaction.league_id,
            season_id=transaction.season_id,
            player_id=transaction.player_id,
            player_name=player.name if player else f"Jugador {transaction.player_id}",
            from_team_id=transaction.from_team_id,
            from_team_name=from_team.name if from_team else f"Equipo {transaction.from_team_id}",
            to_team_id=transaction.to_team_id,
            to_team_name=to_team.name if to_team else f"Equipo {transaction.to_team_id}",
            transaction_type=transaction.transaction_type,
            average=transaction.average,
            captain=transaction.captain,
            created_at=transaction.created_at,
        )

    @staticmethod
    def _remove_participations(
        teams: list[Team],
        predicate,
    ) -> list[Team]:
        remaining_teams: list[Team] = []

        for team in teams:
            remaining_participations = [
                participation
                for participation in team.participations
                if not predicate(participation)
            ]

            if not remaining_participations:
                continue

            remaining_teams.append(
                Team(
                    id=team.id,
                    name=team.name,
                    logo=team.logo,
                    field=team.field,
                    field_element=team.field_element,
                    participations=remaining_participations,
                )
            )

        return remaining_teams

    def _ensure_master_player_exists(self, player_id: int) -> None:
        if player_id in {player.id for player in self.repository.get_players()}:
            return
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El jugador indicado no existe en el catalogo maestro.",
        )

    def _get_league_or_404(self, league_id: int) -> League:
        league = next((league for league in self.repository.get_leagues() if league.id == league_id), None)
        if league is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La liga indicada no existe.",
            )
        return league

    def _get_season_or_404(self, league_id: int, season_id: int) -> Season:
        season = next(
            (
                season
                for season in self.repository.get_seasons()
                if season.id == season_id and season.id_league == league_id
            ),
            None,
        )
        if season is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La temporada indicada no existe dentro de la liga.",
            )
        return season

    @staticmethod
    def _find_league_index(leagues: list[League], league_id: int) -> int:
        for index, league in enumerate(leagues):
            if league.id == league_id:
                return index
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La liga indicada no existe.",
        )

    @staticmethod
    def _find_season_index(seasons: list[Season], season_id: int) -> int:
        for index, season in enumerate(seasons):
            if season.id == season_id:
                return index
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La temporada indicada no existe.",
        )

    @staticmethod
    def _next_id(current_ids: list[int]) -> int:
        return (max(current_ids) + 1) if current_ids else 1

    @staticmethod
    def _find_team_index(teams: list[Team], team_id: int) -> int:
        for index, team in enumerate(teams):
            if team.id == team_id:
                return index
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El equipo indicado no existe.",
        )

    @staticmethod
    def _find_roster_entry_index(
        roster_entries: list[TeamRosterEntry],
        team_id: int,
        player_id: int,
        league_id: int,
        season_id: int,
    ) -> int:
        for index, entry in enumerate(roster_entries):
            if (
                entry.team_id == team_id
                and entry.id_player == player_id
                and entry.id_league == league_id
                and entry.id_season == season_id
            ):
                return index
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe ese jugador dentro del equipo para esa temporada.",
        )
