from discord import Message
import logging
 

async def handle_update(
	client,
	user_message: Message,
	smug_id: int,
	uvabu_id: int,
	fdgood_id: int,
	bobou_id: int,
) -> None:
	"""Temporary update command placeholder.

	The old update flow relied on hardcoded players and ER API lookups.
	This command now responds safely until the modular TinyDB-based
	update flow is implemented.
	"""
	_ = (client, smug_id, uvabu_id, fdgood_id, bobou_id)
	logging.info("Update command called, but modular update flow is not implemented yet.")
	await user_message.channel.send(
		"Update is currently disabled while the command is being migrated to the modular team system."
	)


# async def handle_update(client, user_message: Message,smug_id: int, uvabu_id: int,
#                            fdgood_id: int, bobou_id: int):
#     old_message_channel_id = await extract_channel_id_from_message(user_message)
#     old_message = await get_last_bot_message(client, old_message_channel_id)

#     if old_message:
#         newline_count = old_message.content.count("\n")
#         if newline_count == 4:
#             highest_smug = get_highest_account("Smug")
#             highest_uvabu = get_highest_account("Uvabu")
#             highest_fdgood = get_highest_account("FDGood")

#             custom_message_main_roaster_body = (
#                 f"!register CatSlide\n"
#                 f"<@{smug_id}> https://dak.gg/er/players/{highest_smug}\n"
#                 f"<@{uvabu_id}> https://dak.gg/er/players/{highest_uvabu}\n"
#                 f"<@{fdgood_id}> https://dak.gg/er/players/{highest_fdgood}\n"
#             )
#             await old_message.edit(content=custom_message_main_roaster_body)

#         elif newline_count == 5:

#             highest_smug = get_highest_account("Smug")
#             highest_uvabu = get_highest_account("Uvabu")
#             highest_fdgood = get_highest_account("FDGood")
#             highest_bobou = get_highest_account("Bobou")

#             custom_message_full_roaster_body = (
#                 f"!register CatSlide\n"
#                 f"<@{smug_id}> https://dak.gg/er/players/{highest_smug}\n"
#                 f"<@{uvabu_id}> https://dak.gg/er/players/{highest_uvabu}\n"
#                 f"<@{fdgood_id}> https://dak.gg/er/players/{highest_fdgood}\n"
#                 f"<@{bobou_id}> https://dak.gg/er/players/{highest_bobou}"
#             )

#             await old_message.edit(content=custom_message_full_roaster_body)

#         else:
#             logging.error("Error in the handle_update function")
