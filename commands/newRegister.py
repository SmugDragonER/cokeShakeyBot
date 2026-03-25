import asyncio
import json
import logging
from models import Team, Player
from typing import Callable, Optional, Awaitable
from discord import Message, Reaction, Client



class RegistrationManager:
    def __init__(
        self,
        client: Client,
        team: Team,
        approved_emoji: str = "✅",
        denied_emoji: str = "❌"
    ):
        self.client = client
        self.team = team
        self.approved_emoji = approved_emoji
        self.denied_emoji = denied_emoji
        self.reactions: dict[int, str] = {} #TODO: check if int -> str makes any sense
        self.pending_message: Optional[Message] = None
        self.original_content: str = ""

    async def handle_register(
        self,
        send_message_function: Callable[[int, str], Awaitable[None]],
        channel_id: int,
        user_message: str,
        command_prefix: str = "!register "
    ) -> None:
        """Initiates the registration process by sending a message and adding reaction options."""
        response = user_message[len(command_prefix):]
        self.original_content = response
        logging.info(f"Starting registration for: {response}")

        try:
            await send_message_function(channel_id, response)
            self.pending_message = await self._get_last_bot_message(channel_id)
            await asyncio.sleep(0.5)
            await self._add_reactions(self.pending_message)
            logging.info("Registration message sent with reactions")
        except Exception as e:
            logging.error(f"Error in handle_register: {e}")

    async def _get_last_bot_message(self, channel_id: int) -> Optional[Message]:
        """Retrieves the most recent bot message in the channel."""
        try:
            channel = self.client.get_channel(channel_id)
            async for message in channel.history(limit=5):
                if message.author.bot:
                    return message
        except Exception as e:
            logging.error(f"Error in _get_last_bot_message: {e}")
        return None

    async def _add_reactions(self, message: Message) -> None:
        """Adds approval and denial reaction options to a message."""
        try:
            await message.add_reaction(self.approved_emoji)
            await message.add_reaction(self.denied_emoji)
        except Exception as e:
            logging.error(f"Couldn't add reactions: {e}")

    async def on_reaction_add(self, reaction: Reaction, user) -> None:
        """Handles when a user reacts to the registration message."""
        try:
            if user is None:
                logging.error("User is None. Skipping reaction handling.")
                return

            if reaction.message.author == self.client.user and user != self.client.user:
                # Only track reactions from team members
                all_player_ids = self._get_all_player_ids()
                if user.id in all_player_ids:
                    self.reactions[user.id] = str(reaction.emoji)
                    logging.info(f"Player {user.id} reacted with {reaction.emoji}")
                    logging.debug(f"Current reactions: {self.reactions}")
                    await self._check_reactions(reaction.message)

        except AttributeError as e:
            logging.error(f"AttributeError: {e}")
        except Exception as e:
            logging.error(f"An error occurred: {e}")

    def _get_all_player_ids(self) -> set[int]:
        """Returns all player discord IDs from both main and sub teams."""
        ids = {p.discord_id for p in self.team.main_players}
        ids.update(p.discord_id for p in self.team.sub_players)
        return ids

    async def _check_reactions(self, message: Message) -> None:
        """Evaluates reactions and determines if signup can proceed."""
        try:
            # Count main team reactions
            main_reactions = [self.reactions.get(p.discord_id) for p in self.team.main_players]
            approved_main = main_reactions.count(self.approved_emoji)
            denied_main = main_reactions.count(self.denied_emoji)

            logging.info(f"Main team reactions: {main_reactions}")
            logging.info(f"Approved: {approved_main}, Denied: {denied_main}")

            # Count sub team reactions
            sub_reactions = [self.reactions.get(p.discord_id) for p in self.team.sub_players]
            approved_subs = [r for r in sub_reactions if r == self.approved_emoji]

            total_main = len(self.team.main_players)

            # All main players approved
            if approved_main == total_main:
                logging.info("All main players can play")
                await self._send_signup(message, use_subs=False)
                return

            # One main denied, check if sub can fill in
            if denied_main == 1 and approved_main == total_main - 1:
                if approved_subs:
                    denied_player = next(
                        (p for p in self.team.main_players 
                         if self.reactions.get(p.discord_id) == self.denied_emoji),
                        None
                    )
                    if denied_player:
                        await message.channel.send(
                            f"{denied_player.name} can't play, playing with sub instead!"
                        )
                    logging.info("Using sub player")
                    await self._send_signup(message, use_subs=True)
                elif any(r is None for r in sub_reactions):
                    logging.info("Waiting for sub player response")
                else:
                    logging.info("Main and sub players unavailable")
                    await message.channel.send("Not enough players available for signup.")
                return

            # Too many denials
            if denied_main >= 2:
                logging.info("Too many main players unavailable")
                await message.channel.send("Not enough main players available.")
                return

            logging.info("Waiting for more reactions")

        except Exception as e:
            logging.error(f"An error occurred in check_reactions: {e}", exc_info=True)

    async def _send_signup(self, message: Message, use_subs: bool = False) -> None:
        """Sends the final signup message with player information."""
        try:
            # Determine which players to include
            available_main = [
                p for p in self.team.main_players
                if self.reactions.get(p.discord_id) != self.denied_emoji
            ]
            
            players_to_register = available_main.copy()
            
            if use_subs:
                # Add available subs to fill roster
                available_subs = [
                    p for p in self.team.sub_players
                    if self.reactions.get(p.discord_id) == self.approved_emoji
                ]
                players_to_register.extend(available_subs)

            # Build the signup message
            roster_type = "with subs" if use_subs else "main roster"
            header = f"Scrim sign-ups for {self.original_content}\n{roster_type}"

            body_lines = [f"!register {self.team.name}"]
            for player in players_to_register:
                highest_account = self.get_highest_account(player.accounts)
                body_lines.append(
                    f"<@{player.discord_id}> [dak.gg](https://dak.gg/er/players/{highest_account})"
                )

            await message.channel.send(header)
            await message.channel.send("\n".join(body_lines))
            logging.info(f"Signup sent for {len(players_to_register)} players")

        except Exception as e:
            logging.error(f"An error occurred in send_signup: {e}", exc_info=True)

    def reset(self) -> None:
        """Resets the reaction tracking for a new registration."""
        self.reactions.clear()
        self.pending_message = None
        self.original_content = ""


def load_team_from_json(filepath: str, team_name: str) -> Team:
    """Helper to load team data from a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    main_players = [
        Player(
            discord_id=p['discord_id'],
            name=p['name'],
            accounts=p.get('accounts', [])
        )
        for p in data.get('main_team', [])
    ]

    sub_players = [
        Player(
            discord_id=p['discord_id'],
            name=p['name'],
            accounts=p.get('accounts', [])
        )
        for p in data.get('sub_team', [])
    ]

    return Team(name=team_name, main_players=main_players, sub_players=sub_players)
