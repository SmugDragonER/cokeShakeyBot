import logging

async def handle_help(send_message_function, channel_id: int) -> None:
    logging.info("entered send_help_message")
    help_message = (f"These are the commands you can use:\n\n"
                    f"**!register [your text goes here]**\n"
                    f"bot will copy your message and add reactions to it\n\n"
                    f"**!update**\n"
                    f"NOT TESTED, Bot will update final signup messages with the highest MMR account of every player\n\n"
                    f"**!teamrank**\n"
                    f"bot will send the rank of every teammembers account, sorted from highest to lowest\n\n")
    await send_message_function(channel_id, help_message)
    return
