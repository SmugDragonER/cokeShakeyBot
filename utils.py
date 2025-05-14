from discord import Message

async def extract_channel_id_from_message(message: Message):
    return message.channel.id