import pytest
from unittest.mock import AsyncMock
from commands.register import send_full_signup, add_register_reactions


@pytest.mark.asyncio
async def test_send_full_signup():
    sent_message = AsyncMock()
    reacted_message = AsyncMock()
    reacted_message.content = "Test Scrims"
    smug_id = 1234567
    uvabu_id = 12345678
    fdgood_id = 123456789
    bobou_id = 1234567890

    def mock_get_highest_account(player_name):
        return f"MockedAccount_{player_name}"

    await send_full_signup(
        sent_message,
        main_team=True,
        reacted_message=reacted_message,
        smug_id=smug_id,
        uvabu_id=uvabu_id,
        fdgood_id=fdgood_id,
        bobou_id=bobou_id,
        get_highest_account=mock_get_highest_account
    )

    sent_message.channel.send.assert_any_call(
        f"Scrim sign-ups for {reacted_message.content} with main Players\n"
    )
    sent_message.channel.send.assert_any_call(
        f"!register CatSlide\n"
        f"<@{smug_id}> https://dak.gg/er/players/MockedAccount_Smug\n"
        f"<@{uvabu_id}> https://dak.gg/er/players/MockedAccount_Uvabu\n"
        f"<@{fdgood_id}> https://dak.gg/er/players/MockedAccount_FDGood\n"
    )

@pytest.mark.asyncio
async def test_send_full_signup_with_sub():
    sent_message = AsyncMock()
    reacted_message = AsyncMock()
    reacted_message.content = "Test Scrims"
    smug_id = 1234567
    uvabu_id = 12345678
    fdgood_id = 123456789
    bobou_id = 1234567890

    def mock_get_highest_account(player_name):
        return f"MockedAccount_{player_name}"

    await send_full_signup(
        sent_message,
        main_team=False,
        reacted_message=reacted_message,
        smug_id=smug_id,
        uvabu_id=uvabu_id,
        fdgood_id=fdgood_id,
        bobou_id=bobou_id,
        get_highest_account=mock_get_highest_account
    )

    sent_message.channel.send.assert_any_call(
        f"Scrim sign-ups for {reacted_message.content}\n with Sub"
    )

    sent_message.channel.send.assert_any_call(
        f"!register CatSlide\n"
        f"<@{smug_id}> https://dak.gg/er/players/MockedAccount_Smug\n"
        f"<@{uvabu_id}> https://dak.gg/er/players/MockedAccount_Uvabu\n"
        f"<@{fdgood_id}> https://dak.gg/er/players/MockedAccount_FDGood\n"
        f"<@{bobou_id}> https://dak.gg/er/players/MockedAccount_Bobou"
    )

@pytest.mark.asyncio
async def test_add_register_reactions():
    sent_message = AsyncMock()
    approved_reaction_emoji = "✅"
    deny_reaction_emoji = "❌"

    await add_register_reactions(sent_message, approved_reaction_emoji, deny_reaction_emoji)

    sent_message.add_reaction.assert_any_call(approved_reaction_emoji)
    sent_message.add_reaction.assert_any_call(deny_reaction_emoji)