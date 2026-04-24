# Scrim Discord Bot

A Discord bot for managing scrim team signups. 

Better cheer for CRISPY CRITTERS!

## Features

- Dynamic team storage in TinyDB (`scrim_teams.json`)
- Team registration flow for Friday, Saturday, and Sunday
- Reaction-based attendance logic:
  - All main players approve -> main roster signup is posted
  - One main player declines + approved sub available -> sub roster signup is posted
  - Two or more main players decline -> not enough players message

## Project Structure

- `main.py`: Loads environment variables and starts the bot
- `discordBot.py`: Discord event wiring and command dispatch
- `commands/addTeam.py`: Parses and stores teams in TinyDB
- `commands/register.py`: Team registration sessions + reaction handling
- `utils.py`: Date helpers and TinyDB team loading
- `models.py`: Data models (`Team`, `Player`, `Coach`)

## Requirements

- Python 3.10+
- A Discord bot token

Install dependencies:

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root:

```env
DISCORD_TOKEN=your_discord_bot_token
API_KEY=your_er_api_key_optional
```

Notes:
- `DISCORD_TOKEN` is required to run the bot.
- `API_KEY` is currently only relevant for legacy ER-related commands (`!teamrank`, `!update`).

## Run the Bot

```bash
python main.py
```

## Commands

### `!addteam`
Adds or updates a team in TinyDB.

Expected multi-line format:

```text
!addteam TeamName
P: @MainPlayer1, MainName1, AccountName1
P: @MainPlayer2, MainName2, AccountName2
P: @MainPlayer3, MainName3, AccountName3
S: @SubPlayer1, SubName1, AccountNameSub
C: @Coach1, CoachName1
```

Rules:
- `P:` = main player
- `S:` = substitute player
- `C:` = coach
- At least 3 main players are required
- Each player has exactly one `account` string

### `!register <TeamName>`
Loads the team from TinyDB and creates signup messages for:
- Friday
- Saturday
- Sunday

Each message gets `✅` and `❌` reactions and is evaluated based on team member reactions.

### `!help`
Shows command help text.

### `!teamrank` and `!update`
Currently still legacy/ER-API based and not fully aligned with the new modular TinyDB flow.

## Data Storage

Teams are saved in TinyDB file:

- `scrim_teams.json`

The active registration sessions are kept in memory while the bot is running.

## Current Limitations

- `!teamrank` still reads from `cokeShakeyTeam.json` and expects old account structures.
- `!update` is still legacy and not yet adapted to dynamic TinyDB teams.
- Active registrations are in-memory only (not persisted across bot restarts).

## Development Notes

- The current model uses exactly one account per player (`account: str`).
- The modular workflow is `!addteam` -> TinyDB -> `!register <TeamName>`.
- AI was used to implement features in `commands/register.py` and to write most of this `README.md`
## License

No license file is currently included.
