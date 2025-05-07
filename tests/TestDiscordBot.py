import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from discordBot import DiscordBot
from erApi import get_highest_account, Smug, FDGood, Uvabu, Bobou

class TestDiscordBot(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot = DiscordBot("test_token")
        self.bot.client = MagicMock()

    async def test_send_message(self):
        channel_mock = MagicMock()
        self.bot.client.get_channel = MagicMock(return_value=channel_mock)
        await self.bot.send_message(12345, "Test Message")
        channel_mock.send.assert_called_once_with("Test Message")

    async def test_send_register_message(self):
        message_mock = MagicMock()
        message_mock.channel.send = AsyncMock()
        message_mock.delete = AsyncMock()
        await self.bot.send_register_message(message_mock, "!register Test")
        message_mock.channel.send.assert_called_once_with("Test")
        message_mock.delete.assert_called_once()

    async def test_on_message_register(self):
        message_mock = MagicMock()
        message_mock.content = "!register Test"
        message_mock.author = MagicMock()
        self.bot.client.user = MagicMock()
        message_mock.channel.send = AsyncMock()
        await self.bot.on_message(message_mock)
        message_mock.channel.send.assert_called()

    async def test_check_approved_reaction_count(self):
        message_mock = MagicMock()
        self.bot.reactions_dict = {
            1: "✅",
            2: "✅",
            3: "✅",
        }
        with patch.object(self.bot, "send_full_signup", new_callable=AsyncMock) as mock_send_full_signup:
            await self.bot.check_approved_reaction_count(message_mock)
            mock_send_full_signup.assert_called_once_with(message_mock, 3)

    async def test_on_reaction_add(self):
        reaction_mock = MagicMock()
        user_mock = MagicMock()
        reaction_mock.message.author = self.bot.client.user
        reaction_mock.emoji = "✅"
        user_mock.id = 123
        self.bot.reactions_dict = {}
        with patch.object(self.bot, "check_approved_reaction_count", new_callable=AsyncMock) as mock_check:
            await self.bot.on_reaction_add(reaction_mock, user_mock)
            self.assertEqual(self.bot.reactions_dict[123], "✅")
            mock_check.assert_called_once()

    async def test_send_full_signup_bobou_reacted_but_main_member_missing(self):
        message_mock = MagicMock()
        self.bot.reactions_dict = {
            self.bot.smug_discord_id: "✅",
            self.bot.uvabu_discord_id: "✅",
            self.bot.bobou_discord_id: "✅",  # Bobou hat reagiert
        }
        with patch.object(message_mock.channel, "send", new_callable=AsyncMock) as mock_send:
            await self.bot.send_full_signup(message_mock, approved_count=3)
            mock_send.assert_not_called()

    async def test_send_full_signup_bobou_reacted_and_main_member_denied(self):
        message_mock = MagicMock()
        message_mock.channel.send = AsyncMock()  # Sicherstellen, dass AsyncMock verwendet wird
        self.bot.reacted_message = AsyncMock()
        self.bot.reacted_message.content = "Test Content"

        # Reaktionen simulieren
        self.bot.reactions_dict = {
            self.bot.smug_discord_id: "✅",
            self.bot.fd_discord_id: "✅",
            self.bot.uvabu_discord_id: "❌",
            self.bot.bobou_discord_id: "✅",
        }

        # Deny-Reaktionen zählen
        self.bot.deny_reaction_count = sum(
            1 for reaction in self.bot.reactions_dict.values() if reaction == self.bot.deny_reaction_emoji
        )

        # Methode aufrufen
        await self.bot.send_full_signup(message_mock, approved_count=3)

        # Überprüfen, ob die Nachricht gesendet wurde
        message_mock.channel.send.assert_called_once_with(
            f"Scrim sign-ups for {self.bot.reacted_message.content} with Sub\n"
            f"!register CatSlide\n"
            f"<@{self.bot.smug_discord_id}> https://dak.gg/er/players/{get_highest_account(Smug)}\n"
            f"<@{self.bot.uvabu_discord_id}> https://dak.gg/er/players/{get_highest_account(Uvabu)}\n"
            f"<@{self.bot.fd_discord_id}> https://dak.gg/er/players/{get_highest_account(FDGood)}\n"
            f"<@{self.bot.bobou_discord_id}> https://dak.gg/er/players/{get_highest_account(Bobou)}"
        )

if __name__ == "__main__":
    unittest.main()
