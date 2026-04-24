import re
from models import Player, Coach, Team
from tinydb import TinyDB, Query
from dataclasses import asdict

def get_clean_id(mention_str: str) -> int:
    # Match digits inside <@...> or <@!...>
    match = re.search(r'<@!?([0-9]+)>', mention_str)
    return int(match.group(1)) if match else 0

async def addTeam(send_message_function, channel_id, user_message):
    lines = [l.strip() for l in user_message.split("\n") if l.strip()]
    if not lines: return

    team_name = lines[0].replace("!addteam ", "").strip()
    new_team = Team(name=team_name)

    for line in lines[1:]:
        prefix = line[:2].upper()
        content = line[2:].strip()

        if prefix == "C:":
            parts = content.split(",")
            mention = parts[0].strip()
            name = parts[1].strip() if len(parts) > 1 else ""

            user_id = get_clean_id(content)
            # Storing ID as the name per your request
            new_team.coaches.append(Coach(discord_id=user_id, name=name))

        elif prefix in ["P:", "S:"]:
            parts = content.split(",")
            mention = parts[0].strip()
            name = parts[1].strip() if len(parts) > 1 else ""
            acc_name = parts[2].strip() if len(parts) > 2 else "Unknown"

            user_id = get_clean_id(mention)
            player_obj = Player(
                discord_id=user_id, 
                name=name, # Name is now the ID string
                account=acc_name
            )

            if prefix == "P:":
                new_team.main_players.append(player_obj)
            else:
                new_team.sub_players.append(player_obj)

    # Validation
    if len(new_team.main_players) < new_team.min_main_required:
        await send_message_function(channel_id, f"❌ Error: {team_name} only has {len(new_team.main_players)}/{new_team.min_main_required} main players.")
        return

    # Save to TinyDB
    db = TinyDB('scrim_teams.json')
    teams_table = db.table('teams')
    TQuery = Query()
    
    # upsert: update if name exists, otherwise insert
    teams_table.upsert(asdict(new_team), TQuery.name == team_name)
    
    await send_message_function(channel_id, f"✅ Team **{team_name}** saved! (ID-based tracking active)")