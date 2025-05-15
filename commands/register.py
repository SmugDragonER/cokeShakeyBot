import asyncio
import json
import logging
from discord import Message, Reaction
import asyncio

from erApi import get_highest_account


async def handle_register(send_message_function,client, channel_id: int, user_message: str) -> None:
    response = user_message[10:]  # Remove the '!' and use the rest of the message as the response
    logging.info("entered send_register_message")
    logging.info(response)
    try:
        await send_message_function(channel_id, response)
        sent_message = await get_last_bot_message(client, channel_id)
        await asyncio.sleep(0.5)
        await add_register_reactions(sent_message,"✅", "❌")
        logging.info("added reactions")
    except Exception as e:
        logging.error(f" Error in handle_register: {e}")

async def get_last_bot_message(client, channel_id: int) -> Message:
    try:
        channel = client.get_channel(channel_id)
        async for message in channel.history(limit=5):
            if message.author.bot:
                return message
    except Exception as e:
        logging.error(f" Error in get_last_bot_message: {e}")

async def add_register_reactions(message: Message, approved_reaction_emoji: str, deny_reaction_emoji: str) -> None:
    try:
        await message.add_reaction(approved_reaction_emoji)
        await asyncio.sleep(0.5)
        await message.add_reaction(deny_reaction_emoji)
    except Exception as e:
        logging.error(f"Couldn't add reactions: {e}")

async def send_full_signup(message: Message, main_team: bool, reacted_message: Message, smug_id: int, uvabu_id: int,
                           fdgood_id: int, bobou_id: int, get_highest_account_function) -> None:

    try:
        with open('cokeShakeyTeam.json', 'r', encoding='utf-8') as f:
            team_data = json.load(f)

        logging.info(f"Team data loaded: {team_data}")

        smug_accounts = next(
            (player['accounts'] for player in team_data['main_team'] if player['discord_id'] == smug_id),
            None
        )
        if smug_accounts is None:
            raise ValueError(f"No player found in main_team with discord_id {smug_id}")

        uvabu_accounts = next(player['accounts'] for player in team_data['main_team'] if player['discord_id'] == uvabu_id)
        fdgood_accounts = next(player['accounts'] for player in team_data['main_team'] if player['discord_id'] == fdgood_id)
        bobou_accounts = next(player['accounts'] for player in team_data['sub_team'] if player['discord_id'] == bobou_id)

        logging.info(f"Accounts found: smug={smug_accounts}, uvabu={uvabu_accounts}, fdgood={fdgood_accounts}, bobou={bobou_accounts}")

        highest_smug = get_highest_account(smug_accounts)
        highest_uvabu = get_highest_account(uvabu_accounts)
        highest_fdgood = get_highest_account(fdgood_accounts)
        highest_bobou = get_highest_account(bobou_accounts)

        logging.info(f"Highest accounts: smug={highest_smug}, uvabu={highest_uvabu}, fdgood={highest_fdgood}, bobou={highest_bobou}")

        custom_message_full_roaster_head = (
            f"Scrim sign-ups for {reacted_message.content}\n with Sub")
        custom_message_full_roaster_body = (
            f"!register CatSlide\n"
            f"<@{smug_id}> https://dak.gg/er/players/{highest_smug}\n"
            f"<@{uvabu_id}> https://dak.gg/er/players/{highest_uvabu}\n"
            f"<@{fdgood_id}> https://dak.gg/er/players/{highest_fdgood}\n"
            f"<@{bobou_id}> https://dak.gg/er/players/{highest_bobou}"
        )

        custom_message_main_roaster_head = (
            f"Scrim sign-ups for {reacted_message.content} with main Players\n")
        custom_message_main_roaster_body = (
            f"!register CatSlide\n"
            f"<@{smug_id}> https://dak.gg/er/players/{highest_smug}\n"
            f"<@{uvabu_id}> https://dak.gg/er/players/{highest_uvabu}\n"
            f"<@{fdgood_id}> https://dak.gg/er/players/{highest_fdgood}\n"
        )

        if main_team is True:
            logging.info("sending the main team")
            await message.channel.send(custom_message_main_roaster_head)
            await message.channel.send(custom_message_main_roaster_body)
        elif main_team is False:
            logging.info("sending the full team with sub")
            await message.channel.send(custom_message_full_roaster_head)
            await message.channel.send(custom_message_full_roaster_body)
        else:
            logging.error("You forgot to send a bool value with send_full_signup")
            return

    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)

async def on_reaction_add(reaction: Reaction, user, client, reactions_dict, check_reactions_function) -> None:
    try:
        if user is None:
            logging.error("User is None. Skipping reaction handling.")
            return

        if reaction.message.author == client.user and user != client.user:
            reactions_dict[user.id] = str(reaction.emoji)
            logging.info(f"Benutzer {user.id} hat mit {reaction.emoji} reagiert.")
            logging.debug(f"Aktuelles reactions_dict: {reactions_dict}")

            await check_reactions_function(reaction.message)

    except AttributeError as e:
        logging.error(f"AttributeError: {e}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

async def check_reactions(message: Message, main_team: list, sub_team: list, reactions_dict: dict, send_full_signup_function, reacted_message: Message) -> None:
    """
        Überprüft die Anzahl der genehmigten und abgelehnten Reaktionen für das übergebene Nachricht-Objekt.

        Diese Methode analysiert die Reaktionen der Haupt- und Ersatzspieler auf eine Nachricht und führt
        entsprechende Aktionen basierend auf der Anzahl der genehmigten (✅) und abgelehnten (❌) Reaktionen aus.
    """

    try:
        # Reactions of Main Players
        main_team_reactions = [reactions_dict.get(player['discord_id']) for player in main_team]
        approved_main = main_team_reactions.count('✅')
        denied_main = main_team_reactions.count('❌')

        logging.info(f"Main-Team reactions: {main_team_reactions}")
        logging.info(f"Approved: {approved_main}, Denied: {denied_main}")

        # Reactions of Sub Players
        sub_team_reactions =[reactions_dict.get(player['discord_id']) for player in sub_team]
        sub_approved =[r for r in sub_team_reactions if r == '✅']

        if approved_main ==len(main_team):
            logging.info("All main players can play. Going into send_full_signup with true from check_reactions.")
            await send_full_signup_function(
                message,
                True,
                reacted_message,
                main_team[0]['discord_id'],
                main_team[1]['discord_id'],
                main_team[2]['discord_id'],
                sub_team[0]['discord_id'],
                get_highest_account
            )
            return

        if denied_main == 1 and approved_main == len(main_team) - 1:
            if sub_approved:
                logging.info("one main can not play but sub can! Going into send_full_signup with false from check_reactions.")
                denied_player = next(
                    (player for player in main_team if reactions_dict.get(player['discord_id']) == '❌'), None
                )
                await message.channel.send(f"{denied_player['name']} can't play, playing with Sub instead!")
                await send_full_signup_function(
                    message,
                    False,
                    reacted_message,
                    main_team[0]['discord_id'],
                    main_team[1]['discord_id'],
                    main_team[2]['discord_id'],
                    sub_team[0]['discord_id'],
                    get_highest_account
                )
            elif any(r is None for r in sub_team_reactions):
                logging.info("one main player can't, wait for sub")
            else:
                logging.info("one main and sub player can't")
            return

        if denied_main >=2:
            logging.info("2 or more main players can not play")
            return None
        logging.info("wait for more reactions")
    except  Exception as e:
        logging.error(f"an error occurred: {e}")