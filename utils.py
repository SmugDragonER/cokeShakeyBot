from discord import Message
from datetime import datetime, timedelta
from tinydb import TinyDB, Query
from models import Team, Player, Coach
from typing import Optional

async def extract_channel_id_from_message(message: Message):
    return message.channel.id


def get_dates_for_week(year: int, week: int) -> dict[str, str]:
    # Montag der Woche finden
    first_day_of_year = datetime(year, 1, 4) # ISO Standard
    start_of_week = first_day_of_year + timedelta(weeks=week-1)
    start_of_week -= timedelta(days=start_of_week.weekday())

    # Fr, Sa, So berechnen
    days = {
        "Freitag": (start_of_week + timedelta(days=4)).strftime("%d.%m.%Y"),
        "Samstag": (start_of_week + timedelta(days=5)).strftime("%d.%m.%Y"),
        "Sonntag": (start_of_week + timedelta(days=6)).strftime("%d.%m.%Y"),
    }
    return days

def get_team_from_db(team_name: str) -> Optional[Team]:
    db = TinyDB('scrim_teams.json')
    teams_table = db.table('teams')
    TQuery = Query()
    
    result = teams_table.get(TQuery.name == team_name)
    if not result:
        return None

    # Umwandlung von Dict zurück in Dataclasses
    return Team(
        name=result['name'],
        main_players=[
            Player(
                discord_id=p['discord_id'],
                name=p['name'],
                account=p.get('account', p.get('accounts', ''))
            )
            for p in result['main_players']
        ],
        sub_players=[
            Player(
                discord_id=p['discord_id'],
                name=p['name'],
                account=p.get('account', p.get('accounts', ''))
            )
            for p in result['sub_players']
        ],
        coaches=[Coach(**c) for c in result['coaches']]
    )