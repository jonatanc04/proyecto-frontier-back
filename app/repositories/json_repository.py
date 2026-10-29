import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.models.domain import (
    Character,
    League,
    Season,
    Team,
    TeamParticipation,
    TeamRosterEntry,
    TransferTransaction,
)


class JsonRepository:
    def __init__(self) -> None:
        self._data_dir = get_settings().data_dir

    @staticmethod
    def _ensure_list(value: Any) -> list[Any]:
        if isinstance(value, list):
            return value
        return [value]

    def _read_json_file(self, file_name: str) -> Any:
        return self._read_json_path(self._data_dir / file_name)

    def _write_json_file(self, file_name: str, data: Any) -> None:
        file_path = self._data_dir / file_name
        with file_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.write("\n")
        self._read_json_path.cache_clear()

    @staticmethod
    @lru_cache
    def _read_json_path(file_path: Path) -> Any:
        with file_path.open("r", encoding="utf-8-sig") as file:
            return json.load(file)

    def get_players(self) -> list[Character]:
        raw_players = self._ensure_list(self._read_json_file("inazuma_characters.json"))
        return [
            Character(
                id=player["id"],
                name=player["name"],
                nickname=player.get("nickname", ""),
                img=player.get("img", ""),
                gender=player.get("gender", ""),
                element=player.get("element", ""),
                position=player.get("position", ""),
                active=bool(player.get("active", False)),
            )
            for player in raw_players
        ]

    def get_teams(self) -> list[Team]:
        raw_teams = self._ensure_list(self._read_json_file("teams_data.json"))
        teams: list[Team] = []

        for team in raw_teams:
            participations = [
                TeamParticipation(
                    id_league=participation.get("id_league"),
                    id_season=participation.get("id_season"),
                )
                for participation in team.get("participations", [])
            ]
            teams.append(
                Team(
                    id=team["id"],
                    name=team.get("name", ""),
                    logo=team.get("logo", ""),
                    field=team.get("field", ""),
                    field_element=team.get("field_element", ""),
                    participations=participations,
                )
            )

        return teams

    def get_team_roster_entries(self) -> list[TeamRosterEntry]:
        raw_players = self._ensure_list(self._read_json_file("players_data.json"))
        return [
            TeamRosterEntry(
                team_id=player["team_id"],
                id_player=player["id_player"],
                id_league=player["id_league"],
                id_season=player["id_season"],
                average=player.get("average"),
                captain=player.get("captain", 0),
            )
            for player in raw_players
        ]

    def get_leagues(self) -> list[League]:
        raw_leagues = self._ensure_list(self._read_json_file("leagues_data.json"))
        return [League(id=league["id"], name=league["name"]) for league in raw_leagues]

    def get_seasons(self) -> list[Season]:
        raw_seasons = self._ensure_list(self._read_json_file("season_data.json"))
        return [
            Season(
                id=season["id"],
                name=season["name"],
                id_league=season["id_league"],
            )
            for season in raw_seasons
        ]

    def get_elements(self) -> dict[str, str]:
        return self._read_json_file("elements_img.json")

    def get_genders(self) -> dict[str, str]:
        return self._read_json_file("gender_img.json")

    def get_transfer_transactions(self) -> list[TransferTransaction]:
        raw_transactions = self._ensure_list(self._read_json_file("transactions_data.json"))
        return [
            TransferTransaction(
                id=transaction["id"],
                league_id=transaction["league_id"],
                season_id=transaction["season_id"],
                player_id=transaction["player_id"],
                from_team_id=transaction["from_team_id"],
                to_team_id=transaction["to_team_id"],
                transaction_type=transaction["transaction_type"],
                average=transaction.get("average"),
                captain=transaction.get("captain", 0),
                created_at=transaction["created_at"],
            )
            for transaction in raw_transactions
        ]

    def save_leagues(self, leagues: list[League]) -> None:
        self._write_json_file(
            "leagues_data.json",
            [{"id": league.id, "name": league.name} for league in leagues],
        )

    def save_seasons(self, seasons: list[Season]) -> None:
        self._write_json_file(
            "season_data.json",
            [
                {
                    "id": season.id,
                    "name": season.name,
                    "id_league": season.id_league,
                }
                for season in seasons
            ],
        )

    def save_teams(self, teams: list[Team]) -> None:
        self._write_json_file(
            "teams_data.json",
            [
                {
                    "id": team.id,
                    "name": team.name,
                    "logo": team.logo,
                    "field": team.field,
                    "field_element": team.field_element,
                    "participations": [
                        {
                            "id_league": participation.id_league,
                            "id_season": participation.id_season,
                        }
                        for participation in team.participations
                    ],
                }
                for team in teams
            ],
        )

    def save_team_roster_entries(self, entries: list[TeamRosterEntry]) -> None:
        self._write_json_file(
            "players_data.json",
            [
                {
                    "team_id": entry.team_id,
                    "id_player": entry.id_player,
                    "id_league": entry.id_league,
                    "id_season": entry.id_season,
                    "average": entry.average,
                    "captain": entry.captain,
                }
                for entry in entries
            ],
        )

    def save_transfer_transactions(self, transactions: list[TransferTransaction]) -> None:
        self._write_json_file(
            "transactions_data.json",
            [
                {
                    "id": transaction.id,
                    "league_id": transaction.league_id,
                    "season_id": transaction.season_id,
                    "player_id": transaction.player_id,
                    "from_team_id": transaction.from_team_id,
                    "to_team_id": transaction.to_team_id,
                    "transaction_type": transaction.transaction_type,
                    "average": transaction.average,
                    "captain": transaction.captain,
                    "created_at": transaction.created_at,
                }
                for transaction in transactions
            ],
        )
