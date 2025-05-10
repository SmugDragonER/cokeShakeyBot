from typing import Final
import os
from dotenv import load_dotenv
from discordBot import DiscordBot

# Load Token
load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

# Run the Bot
bot = DiscordBot(TOKEN)
bot.run()
