from dataclasses import dataclass, field
from datetime import datetime
from typing import Awaitable, Callable

import logging

from discord import Client, Message, Reaction

from models import Team
from utils import get_dates_for_week, get_discord_timestamps_for_week, get_team_from_db


@dataclass
class RegistrationSession:
    team: Team
    day_label: str
    signup_message: Message
    # Reactions stored as a mapping of user ID to their reaction ("✅" or "❌")
    reactions: dict[int, str] = field(default_factory=dict)


ACTIVE_REGISTRATIONS: dict[int, RegistrationSession] = {}


def _player_account(player) -> str:
    return player.account.strip()


def _team_member_ids(team: Team) -> set[int]:
    member_ids = {player.discord_id for player in team.main_players}
    member_ids.update(player.discord_id for player in team.sub_players)
    return member_ids


async def _send_signup_message(
    session: RegistrationSession,
    use_subs: bool = False,
) -> None:
    available_main = [
        player for player in session.team.main_players
        if session.reactions.get(player.discord_id) != "❌"
    ]

    players_to_register = available_main.copy()

    if use_subs:
        available_subs = [
            player for player in session.team.sub_players
            if session.reactions.get(player.discord_id) == "✅"
        ]
        players_to_register.extend(available_subs)

    roster_type = "with subs" if use_subs else "main roster"
    header = f"Scrim sign-ups for {session.team.name} - {session.day_label}\n{roster_type}"

    body_lines = [f"!register {session.team.name}"]
    for player in players_to_register:
        body_lines.append(
            f"<@{player.discord_id}> https://dak.gg/er/players/{_player_account(player)}"
        )

    await session.signup_message.channel.send(header)
    await session.signup_message.channel.send("\n".join(body_lines))


async def _check_reactions(session: RegistrationSession) -> None:
    main_reactions = [session.reactions.get(player.discord_id) for player in session.team.main_players]
    approved_main = main_reactions.count("✅")
    denied_main = main_reactions.count("❌")

    sub_reactions = [session.reactions.get(player.discord_id) for player in session.team.sub_players]
    approved_subs = [reaction for reaction in sub_reactions if reaction == "✅"]

    total_main = len(session.team.main_players)

    if approved_main == total_main:
        await _send_signup_message(session, use_subs=False)
        return

    if denied_main == 1 and approved_main == total_main - 1:
        if approved_subs:
            denied_player = next(
                (player for player in session.team.main_players if session.reactions.get(player.discord_id) == "❌"),
                None,
            )
            if denied_player:
                await session.signup_message.channel.send(
                    f"{denied_player.name} can't play, playing with sub instead!"
                )
            await _send_signup_message(session, use_subs=True)
        elif any(reaction is None for reaction in sub_reactions):
            logging.info("Waiting for sub player response")
        else:
            await session.signup_message.channel.send("Not enough players available for signup.")
        return

    if denied_main >= 2:
        await session.signup_message.channel.send("Not enough main players available.")
        return

    logging.info("Waiting for more reactions")


async def handle_register(
    send_message_function: Callable[[int, str], Awaitable[Message]],
    channel_id: int,
    user_message: str,
    command_prefix: str = "!register ",
) -> None:
    team_name = user_message[len(command_prefix):].strip()

    if not team_name:
        await send_message_function(channel_id, "❌ Bitte einen Teamnamen angeben. Beispiel: !register Teamname")
        return

    team = get_team_from_db(team_name)
    if not team:
        await send_message_function(channel_id, f"❌ Team {team_name} wurde in TinyDB nicht gefunden.")
        return

    now = datetime.now().isocalendar()
    dates = get_dates_for_week(now.year, now.week)
    discord_dates = get_discord_timestamps_for_week(now.year, now.week)

    for day_label, day_date in dates.items():
        day_ts = discord_dates[day_label]
        content = f"Scrim sign-ups for {team.name} - {day_label} ({day_ts} / {day_date})"
        message = await send_message_function(channel_id, content)
        if message is None:
            logging.error("Could not send signup message")
            continue

        session = RegistrationSession(
            team=team,
            day_label=f"{day_label} ({day_ts} / {day_date})",
            signup_message=message,
        )
        ACTIVE_REGISTRATIONS[message.id] = session
        await message.add_reaction("✅")
        await message.add_reaction("❌")


async def on_reaction_add(reaction: Reaction, user, client: Client) -> None:
    if user is None or user == client.user:
        return

    session = ACTIVE_REGISTRATIONS.get(reaction.message.id)
    if not session:
        return

    if user.id not in _team_member_ids(session.team):
        return

    session.reactions[user.id] = str(reaction.emoji)
    await _check_reactions(session)