import logging
from discord import Intents, Client, Message, Reaction
from erApi import get_highest_account
import json

from commands.help import handle_help
from commands.register import (handle_register, add_register_reactions, send_full_signup, on_reaction_add,
                               check_reactions)
from commands.teamrank import handle_teamrank
from commands.update import handle_update
# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


async def extract_channel_id_from_message(message: Message):
    return message.channel.id


class DiscordBot:
    def __init__(self, token: str):
        self.TOKEN = token

        # load team
        with open('cokeShakeyTeam.json', 'r', encoding='utf-8') as f:
            config = json.load(f)

        self.main_team = config['main_team']
        self.sub_team = config['sub_team']

        self.reactions_dict = {}
        for player in self.main_team + self.sub_team:
            self.reactions_dict[player['discord_id']] = None

        # get IDs
        self.smug_discord_id = next(player['discord_id'] for player in self.main_team if player['name'] == 'Smug')
        self.fd_discord_id = next(player['discord_id'] for player in self.main_team if player['name'] == 'FDGood')
        self.uvabu_discord_id = next(player['discord_id'] for player in self.main_team if player['name'] == 'Uvabu')
        self.bobou_discord_id = next(player['discord_id'] for player in self.sub_team if player['name'] == 'Bobou')

        intents = Intents.default()
        intents.message_content = True
        intents.reactions = True
        self.client = Client(intents=intents)

        self.approved_reaction_emoji = '✅'
        self.deny_reaction_emoji = '❌'
        self.reacted_message = None

        self.client.event(self.on_ready)
        self.client.event(self.on_reaction_add)
        self.client.event(self.on_error)
        self.client.event(self.on_message)
        self.client.event(self.on_disconnect)

    def run(self):
        self.client.run(self.TOKEN)

    async def send_message(self, channel_id: int, message_to_send: str) -> None:
        try:
            channel = self.client.get_channel(channel_id)
            if channel:
                await channel.send(message_to_send)
            else:
                logging.warning("Channel ID was not found.")
        except Exception as e:
            logging.error(f"Couldn't send message: {e}")

    async def on_message(self, message: Message) -> None:
        if message.author == self.client.user:
            return

        user_message_str = message.content
        user_message = message

        if user_message_str.startswith('!register'):
            await handle_register(self.send_message,self.client, message.channel.id, user_message_str)
            return

        if user_message_str.startswith('!help'):
            logging.debug(f"Channel ID: {message.channel.id}")
            await handle_help(self.send_message, message.channel.id)
            return

        if user_message_str.startswith('!update'):
                await handle_update(self.client, user_message, self.smug_discord_id, self.uvabu_discord_id,
                                    self.fd_discord_id, self.bobou_discord_id)

        if user_message_str.startswith('!teamrank'):
            await handle_teamrank(self.send_message, message.channel.id)
            return

    async def add_register_reactions(self, message: Message) -> None:
        await add_register_reactions(message, self.approved_reaction_emoji, self.deny_reaction_emoji)

    async def send_full_signup(self, message: Message, main_team: bool) -> None:
        await send_full_signup(message, main_team, self.reacted_message, self.smug_discord_id, self.uvabu_discord_id,
                               self.fd_discord_id, self.bobou_discord_id, get_highest_account)

    async def on_reaction_add(self, reaction: Reaction, user) -> None:
        await on_reaction_add(reaction, user, self.client, self.reactions_dict, self.check_reactions)

    async def check_reactions(self, message: Message) -> None:
        await check_reactions(message, self.main_team, self.sub_team, self.reactions_dict, self.send_full_signup,
                              self.reacted_message)

    async def on_ready(self):
        logging.info(f'Logged in as {self.client.user}')
        channel = self.client.get_channel(1328537451068919838)
        if channel:
            async for message in channel.history(limit=10):
                if message.author == self.client.user:
                    self.reacted_message = message
                    if message.content.startswith('Scrim sign-ups for'):
                        return
                    for reaction in message.reactions:
                        async for user in reaction.users():
                            if user != self.client.user:  # Ignoriere den Bot selbst
                                self.reactions_dict[user.id] = str(reaction.emoji)
                                logging.info(f'Benutzer {user.id} hat mit {reaction.emoji} reagiert.')
                    logging.info("entering reacted_messages from on_ready")
                    await self.check_reactions(self.reacted_message)
                break

    async def on_error(self, event_method, *args, **kwargs):
        logging.error(f"Ein Fehler ist im Event '{event_method}' aufgetreten.", exc_info=True)

    async def on_disconnect(self):
        logging.warning("Der Bot wurde vom Discord-Server getrennt.")
