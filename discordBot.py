import logging
from discord import Intents, Client, Message, Reaction

from commands.help import handle_help
from commands.addTeam import addTeam as handle_addTeam
from commands.register import handle_register, on_raw_reaction_add
from commands.teamrank import handle_teamrank
from commands.update import handle_update
# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DiscordBot:
    def __init__(self, token: str):
        self.TOKEN = token

        intents = Intents.default()
        intents.message_content = True
        intents.reactions = True
        self.client = Client(intents=intents)

        self.client.event(self.on_ready)
        self.client.event(self.on_error)
        self.client.event(self.on_message)
        self.client.event(self.on_reaction_add)
        self.client.event(self.on_raw_reaction_add)
        self.client.event(self.on_disconnect)

    def run(self):
        self.client.run(self.TOKEN)

    async def send_message(self, channel_id: int, message_to_send: str):
        try:
            channel = self.client.get_channel(channel_id)
            if channel:
                return await channel.send(message_to_send)
            else:
                logging.warning("Channel ID was not found.")
        except (RuntimeError, ValueError, TypeError) as error:
            logging.error("Couldn't send message: %s", error)
        return None

    async def on_message(self, message: Message) -> None:
        if message.author == self.client.user:
            return

        user_message_str = message.content

        if user_message_str.startswith('!register'):
            await handle_register(self.send_message, message.channel.id, user_message_str)
            return
        
        if user_message_str.startswith('!addteam'):
            await handle_addTeam(self.send_message, message.channel.id, user_message_str)

        if user_message_str.startswith('!help'):
            logging.debug("Channel ID: %s", message.channel.id)
            await handle_help(self.send_message, message.channel.id)
            return

        if user_message_str.startswith('!update'):
            await handle_update(self.client, message, 0, 0, 0, 0)

        if user_message_str.startswith('!teamrank'):
            await handle_teamrank(self.send_message, message.channel.id)
            return

    async def on_reaction_add(self, reaction: Reaction, user) -> None:
        # Kept for compatibility with cached messages during the same runtime.
        from commands.register import handle_reaction_add

        if reaction.message is None or user is None:
            return
        await handle_reaction_add(reaction.message.id, user.id, str(reaction.emoji), self.client)

    async def on_raw_reaction_add(self, payload) -> None:
        await on_raw_reaction_add(payload, self.client)

    async def on_ready(self):
        logging.info("Logged in as %s", self.client.user)
        logging.info("Bot is ready and waiting for !addteam / !register commands")

    async def on_error(self, event_method, *_, **__):
        logging.error("Ein Fehler ist im Event '%s' aufgetreten.", event_method, exc_info=True)

    async def on_disconnect(self):
        logging.warning("Der Bot wurde vom Discord-Server getrennt.")
