import pytest
from unittest.mock import AsyncMock
from commands.help import handle_help


@pytest.mark.asyncio
async def test_help():
    mock_send_message = AsyncMock()

    channel_id = 123456789

    await handle_help(mock_send_message, channel_id)

    mock_send_message.assert_called_once_with(channel_id,
                    f"These are the commands you can use:\n\n"
                    f"**!register [your text goes here]**\n"
                    f"bot will copy your message and add reactions to it\n\n"
                    f"**!update**\n"
                    f"CURRENTLY NOT WORKING, bot will update final signup messages with the highest MMR account of every player\n\n"
                    f"**!teamrank**\n"
                    f"bot will send the rank of every teammembers account, sorted from highest to lowest\n\n")
