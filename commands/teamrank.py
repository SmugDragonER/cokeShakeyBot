import json
import logging
from erApi import get_user_rank


async def handle_teamrank(send_message_function, channel_id):
    logging.info("handling teamrank")
    with open('cokeShakeyTeam.json', 'r', encoding='utf8') as f:
        team_data = json.load(f)
        teamrank_message = process_teamrank(team_data)

        if teamrank_message:
            await send_message_function(channel_id, teamrank_message)


def process_teamrank(team_data: dict) -> str:
    teamrank_message = ""

    for player in team_data['main_team'] + team_data['sub_team']:
        player_name = player["name"]
        accounts = []

        for account in player['accounts']:
            mmr = get_user_rank(account)
            accounts.append({"account": account, "rank": mmr})  # Geschweifte Klammer geschlossen

        accounts = sorted(accounts, key=lambda account: account['rank'], reverse=True)

        teamrank_message += f"\n**{player_name}**\n"
        for idx, account in enumerate(accounts, start=1):
            teamrank_message += f" Nr {idx}: {account['rank']} - {account['account']}\n"

    return teamrank_message
