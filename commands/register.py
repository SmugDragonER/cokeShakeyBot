import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Awaitable, Callable

import logging

from discord import Client, Message

from models import Coach, Player, Team
from utils import get_dates_for_week, get_discord_timestamps_for_week, get_team_from_db


ACTIVE_REGISTRATIONS_FILE = Path("active_registrations.json")


@dataclass
class RegistrationSession:
    team: Team
    day_label: str
    channel_id: int
    signup_message_id: int
    # Reactions stored as a mapping of user ID to their reaction ("✅" or "❌")
    reactions: dict[int, str] = field(default_factory=dict)


def _team_from_payload(payload: dict) -> Team:
    return Team(
        name=payload["name"],
        main_players=[Player(**player) for player in payload.get("main_players", [])],
        sub_players=[Player(**player) for player in payload.get("sub_players", [])],
        coaches=[Coach(**coach) for coach in payload.get("coaches", [])],
        min_main_required=payload.get("min_main_required", 3),
    )


def _session_from_payload(payload: dict) -> RegistrationSession:
    return RegistrationSession(
        team=_team_from_payload(payload["team"]),
        day_label=payload["day_label"],
        channel_id=payload["channel_id"],
        signup_message_id=payload["signup_message_id"],
        reactions={int(user_id): emoji for user_id, emoji in payload.get("reactions", {}).items()},
    )


def _session_to_payload(session: RegistrationSession) -> dict:
    return {
        "team": asdict(session.team),
        "day_label": session.day_label,
        "channel_id": session.channel_id,
        "signup_message_id": session.signup_message_id,
        "reactions": {str(user_id): emoji for user_id, emoji in session.reactions.items()},
    }


def _load_active_registrations() -> dict[int, RegistrationSession]:
    if not ACTIVE_REGISTRATIONS_FILE.exists():
        return {}

    try:
        with ACTIVE_REGISTRATIONS_FILE.open("r", encoding="utf-8") as file:
            raw_data = json.load(file)
    except (OSError, json.JSONDecodeError):
        logging.warning("Could not load persisted registrations; starting with an empty session list.")
        return {}

    registrations: dict[int, RegistrationSession] = {}
    for message_id, payload in raw_data.items():
        try:
            registrations[int(message_id)] = _session_from_payload(payload)
        except (KeyError, TypeError, ValueError) as exc:
            logging.warning("Skipping invalid persisted registration %s: %s", message_id, exc)

    return registrations


def _save_active_registrations() -> None:
    if not ACTIVE_REGISTRATIONS:
        if ACTIVE_REGISTRATIONS_FILE.exists():
            ACTIVE_REGISTRATIONS_FILE.unlink()
        return

    payload = {str(message_id): _session_to_payload(session) for message_id, session in ACTIVE_REGISTRATIONS.items()}
    with ACTIVE_REGISTRATIONS_FILE.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def _remove_session(message_id: int) -> None:
    ACTIVE_REGISTRATIONS.pop(message_id, None)
    _save_active_registrations()


ACTIVE_REGISTRATIONS: dict[int, RegistrationSession] = _load_active_registrations()


def _player_account(player) -> str:
    return player.account.strip()


def _team_member_ids(team: Team) -> set[int]:
    member_ids = {player.discord_id for player in team.main_players}
    member_ids.update(player.discord_id for player in team.sub_players)
    return member_ids


async def _send_signup_message(
    client: Client,
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

    channel = client.get_channel(session.channel_id)
    if channel is None:
        channel = await client.fetch_channel(session.channel_id)

    await channel.send(header)
    await channel.send("\n".join(body_lines))


async def _check_reactions(client: Client, session: RegistrationSession) -> None:
    main_reactions = [session.reactions.get(player.discord_id) for player in session.team.main_players]
    approved_main = main_reactions.count("✅")
    denied_main = main_reactions.count("❌")

    sub_reactions = [session.reactions.get(player.discord_id) for player in session.team.sub_players]
    approved_subs = [reaction for reaction in sub_reactions if reaction == "✅"]

    total_main = len(session.team.main_players)

    if approved_main == total_main:
        await _send_signup_message(client, session, use_subs=False)
        _remove_session(session.signup_message_id)
        return

    if denied_main == 1 and approved_main == total_main - 1:
        if approved_subs:
            denied_player = next(
                (player for player in session.team.main_players if session.reactions.get(player.discord_id) == "❌"),
                None,
            )
            if denied_player:
                channel = client.get_channel(session.channel_id)
                if channel is None:
                    channel = await client.fetch_channel(session.channel_id)
                await channel.send(
                    f"{denied_player.name} can't play, playing with sub instead!"
                )
            await _send_signup_message(client, session, use_subs=True)
            _remove_session(session.signup_message_id)
        elif any(reaction is None for reaction in sub_reactions):
            logging.info("Waiting for sub player response")
        else:
            channel = client.get_channel(session.channel_id)
            if channel is None:
                channel = await client.fetch_channel(session.channel_id)
            await channel.send("Not enough players available for signup.")
            _remove_session(session.signup_message_id)
        return

    if denied_main >= 2:
        channel = client.get_channel(session.channel_id)
        if channel is None:
            channel = await client.fetch_channel(session.channel_id)
        await channel.send("Not enough main players available.")
        _remove_session(session.signup_message_id)
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
        content = f"Scrim sign-ups for {team.name} - {day_ts}"
        message = await send_message_function(channel_id, content)
        if message is None:
            logging.error("Could not send signup message")
            continue

        session = RegistrationSession(
            team=team,
            day_label=f"{day_label} ({day_ts} / {day_date})",
            channel_id=channel_id,
            signup_message_id=message.id,
        )
        ACTIVE_REGISTRATIONS[message.id] = session
        _save_active_registrations()
        await message.add_reaction("✅")
        await message.add_reaction("❌")


async def handle_reaction_add(message_id: int, user_id: int, emoji: str, client: Client) -> None:
    if client.user is None or user_id == client.user.id:
        return

    session = ACTIVE_REGISTRATIONS.get(message_id)
    if not session:
        return

    if user_id not in _team_member_ids(session.team):
        return

    session.reactions[user_id] = emoji
    _save_active_registrations()
    await _check_reactions(client, session)


async def on_raw_reaction_add(payload, client: Client) -> None:
    await handle_reaction_add(payload.message_id, payload.user_id, str(payload.emoji), client)