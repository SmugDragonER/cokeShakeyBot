import logging
from discord import Intents, Client, Message, Reaction
from erApi import get_highest_account, Smug, FDGood, Uvabu, Bobou, team_ranking

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DiscordBot:
    def __init__(self, token: str):
        self.TOKEN = token


        self.main_team = [
            {"name": "Smug", "discord_id": 342049022812356611},
            {"name": "Uvabu", "discord_id": 452694750248828948},
            {"name": "FDGood", "discord_id": 242244489413001219},
        ]

        self.sub_team = [
            {"name": "Bobou", "discord_id": 127610213615271936},
        ]

        intents = Intents.default()
        intents.message_content = True
        intents.reactions = True
        self.client = Client(intents=intents)

        self.approved_reaction_count = 0
        self.approved_reaction_emoji = '✅'
        self.deny_reaction_count = 0
        self.deny_reaction_emoji = '❌'
        self.reacted_message = None
        self.last_bot_message = None

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

    async def send_full_signup(self, message: Message, approved_count: int) -> None:
        try:
            logging.info(f"Reactions dict: {self.reactions_dict}")

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

            if approved_count >= 4:
                logging.info("4 approved reactions erkannt. Sende Nachricht.")
                await self.send_message(custom_message_full_roaster)
            elif approved_count == 3:
                if self.bobou_discord_id not in self.reactions_dict:
                    logging.info("3 approved reactions erkannt, aber Bobou hat nicht reagiert. Sende Nachricht.")
                    await message.channel.send(custom_message_main_roaster)

                elif self.reactions_dict[self.bobou_discord_id] == self.deny_reaction_emoji:
                    logging.info("Bobou hat mit ❌ reagiert. Signing up with Main roaster.")
                    await message.channel.send(custom_message_main_roaster)
                elif self.reactions_dict[self.bobou_discord_id] == self.approved_reaction_emoji:
                    logging.info("Bobou hat mit ✅ reagiert. Signing up with Full roaster.")
                    if self.deny_reaction_count == 1:
                        logging.info("One person denyed and can not play")
                        await message.channel.send(custom_message_full_roaster)
                    else:
                        logging.info("Bobou hat reagiert, aber kein deny deshalb passier nichts")
                        return
                else:
                    logging.info("Warte auf eine Reaktion von Bobou.")
                    return
            else:
                logging.info("Nicht genügend genehmigte Reaktionen.")
                return

            if self.reacted_message:
                await self.reacted_message.delete()
                logging.info("Ursprüngliche Reaktionsnachricht wurde gelöscht.")
        except Exception as e:
            logging.error(f"An error occurred: {e}")

    async def on_reaction_add(self, reaction: Reaction, user) -> None:
        try:
            if reaction.message.author == self.client.user:
                if user != self.client.user:
                    self.reactions_dict[user.id] = str(reaction.emoji)
                    logging.info(f"Benutzer {user.id} hat mit {reaction.emoji} reagiert.")
                    logging.debug(f"Aktuelles reactions_dict: {self.reactions_dict}")

                    await self.check_approved_reaction_count(reaction.message)
        except Exception as e:
            logging.error(f"An error occurred: {e}")

    async def check_approved_reaction_count(self, message: Message) -> None:
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
            sub_denied =[r for r in sub_team_reactions if r == '❌']

            if approved_main ==len(self.main_team):
                logging.info("Alle Main Spieler können. Sende Main Sign up")
                await message.channel.send("Main Team!")
                return

            if denied_main == 1 and approved_main == len(self.main_team) - 1:
                if sub_approved:
                    await  message.channel.send("Full roster (mit Sub)")
                elif any(r is None for r in sub_team_reactions):
                    logging.info("one main player can't, wait for sub")
                else:
                    logging.info("one main and sub player can't")
                return

            if denied_main >=2:
                logging.info("2 or more main players can not play")
                return
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
                    break
                break

    async def on_error(self, event_method, *args, **kwargs):
        logging.error(f"Ein Fehler ist im Event '{event_method}' aufgetreten.", exc_info=True)

    async def on_disconnect(self):
        logging.warning("Der Bot wurde vom Discord-Server getrennt.")
