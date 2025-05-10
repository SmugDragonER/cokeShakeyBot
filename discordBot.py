import logging
from discord import Intents, Client, Message, Reaction
from erApi import get_highest_account, Smug, FDGood, Uvabu, Bobou, team_ranking
import json
from typing import  Optional

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        self.client.event(self.on_message)
        self.client.event(self.on_reaction_add)
        self.client.event(self.on_error)
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

    async def send_register_message(self, message: Message, user_message: str) -> None:
        response = user_message[10:]  # Remove the '!' and use the rest of the message as the response
        try:
            sent_message = await message.channel.send(response)
            await self.add_register_reactions(sent_message)
            await message.delete()  # Delete the original message
        except Exception as e:
            logging.error(e)

    async def on_message(self, message: Message) -> None:
        if message.author == self.client.user:
            return

        user_message = message.content
        channel = message.channel
        if user_message.startswith('!register'):
            await self.send_register_message(message, user_message)

        ## TODO: Update function
        if user_message.startswith('!update'):
            await self.update_signup_message(message)

        if user_message.startswith('!teamrank'):
            await self.send_message(channel.id, await self.send_team_ranking())

    async def add_register_reactions(self, message: Message) -> None:
        try:
            await message.add_reaction(self.approved_reaction_emoji)
            await message.add_reaction(self.deny_reaction_emoji)
        except Exception as e:
            logging.error(f"Couldn't add reactions: {e}")

    async def send_full_signup(self, message: Message, main_team: bool) -> None:
        try:
            highest_smug = get_highest_account(Smug)
            highest_uvabu = get_highest_account(Uvabu)
            highest_fdgood = get_highest_account(FDGood)
            highest_bobou = get_highest_account(Bobou)

            custom_message_full_roaster = (
                f"Scrim sign-ups for {self.reacted_message.content}\n with Sub"
                f"!register CatSlide\n"
                f"<@{self.smug_discord_id}> https://dak.gg/er/players/{highest_smug}\n"
                f"<@{self.uvabu_discord_id}> https://dak.gg/er/players/{highest_uvabu}\n"
                f"<@{self.fd_discord_id}> https://dak.gg/er/players/{highest_fdgood}\n"
                f"<@{self.bobou_discord_id}> https://dak.gg/er/players/{highest_bobou}"
            )

            custom_message_main_roaster = (
                f"Scrim sign-ups for {self.reacted_message.content} with main Players\n"
                f"!register CatSlide\n"
                f"<@{self.smug_discord_id}> https://dak.gg/er/players/{highest_smug}\n"
                f"<@{self.uvabu_discord_id}> https://dak.gg/er/players/{highest_uvabu}\n"
                f"<@{self.fd_discord_id}> https://dak.gg/er/players/{highest_fdgood}\n"
            )

            if main_team is True:
                logging.info("sending the main team")
                await(message.channel.send(custom_message_main_roaster))
            elif main_team is False:
                logging.info("sending the full team with sub")
                await(message.channel.send(custom_message_full_roaster))
            else:
                logging.error("You forgot to send a bool value with send_full_signup")
                return

        except Exception as e:
            logging.error(f"An error occurred: {e}")

    async def on_reaction_add(self, reaction: Reaction, user) -> Optional[str]:
        try:
            if reaction.message.author == self.client.user:
                if user != self.client.user:
                    self.reactions_dict[user.id] = str(reaction.emoji)
                    logging.info(f"Benutzer {user.id} hat mit {reaction.emoji} reagiert.")
                    logging.debug(f"Aktuelles reactions_dict: {self.reactions_dict}")

                    await self.check_reactions(reaction.message)
        except Exception as e:
            logging.error(f"An error occurred: {e}")


    async def check_reactions(self, message: Message) -> Optional[str]:
        """
            Überprüft die Anzahl der genehmigten und abgelehnten Reaktionen für das übergebene Nachricht-Objekt.

            Diese Methode analysiert die Reaktionen der Haupt- und Ersatzspieler auf eine Nachricht und führt
            entsprechende Aktionen basierend auf der Anzahl der genehmigten (✅) und abgelehnten (❌) Reaktionen aus.
        """

        try:
            # Reactions of Main Players
            main_team_reactions = [self.reactions_dict.get(player['discord_id']) for player in self.main_team]
            approved_main = main_team_reactions.count('✅')
            denied_main = main_team_reactions.count('❌')

            logging.info(f"Main-Team reactions: {main_team_reactions}")
            logging.info(f"Approved: {approved_main}, Denied: {denied_main}")

            # Reactions of Sub Players
            sub_team_reactions =[self.reactions_dict.get(player['discord_id']) for player in self.sub_team]
            sub_approved =[r for r in sub_team_reactions if r == '✅']

            if approved_main ==len(self.main_team):
                logging.info("All main players can play. Going into send_full_signup with true from check_reactions.")
                await self.send_full_signup(self.reacted_message,True)
                return None

            if denied_main == 1 and approved_main == len(self.main_team) - 1:
                if sub_approved:
                    logging.info("one main can not play but sub can! Going into send_full_signup with false from check_reactions.")
                    denied_player = next(
                        (player for player in self.main_team if self.reactions_dict.get(player['discord_id']) == '❌'),
                    )
                    await message.channel.send(f"{denied_player['name']} can't play, playing with Sub intead!")
                    await self.send_full_signup(self.reacted_message,False)
                elif any(r is None for r in sub_team_reactions):
                    logging.info("one main player can't, wait for sub")
                else:
                    logging.info("one main and sub player can't")
                return None

            if denied_main >=2:
                logging.info("2 or more main players can not play")
                return None
            logging.info("wait for more reactions")
        except  Exception as e:
            logging.error(f"an error occurred: {e}")

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
                    await(self.check_reactions(self.reacted_message))
                break

    async def on_error(self, event_method, *args, **kwargs):
        logging.error(f"Ein Fehler ist im Event '{event_method}' aufgetreten.", exc_info=True)

    async def on_disconnect(self):
        logging.warning("Der Bot wurde vom Discord-Server getrennt.")
