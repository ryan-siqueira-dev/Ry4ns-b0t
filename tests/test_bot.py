import unittest

from ry4ns_bot.bot import _clean_reason, create_bot, register_commands
from ry4ns_bot.config import Settings


class CleanReasonTests(unittest.TestCase):
    def test_trims_reason(self) -> None:
        self.assertEqual(_clean_reason("  spam  "), "spam")

    def test_converts_blank_reason_to_none(self) -> None:
        self.assertIsNone(_clean_reason("   "))


class BotRegistrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_registers_all_documented_commands(self) -> None:
        bot = create_bot(Settings(discord_token="test-token", discord_guild_id=123))

        try:
            register_commands(bot)
            command_names = {command.name for command in bot.tree.get_commands()}

            self.assertEqual(
                command_names,
                {
                    "8ball",
                    "avatar",
                    "ban",
                    "choose",
                    "clear",
                    "coinflip",
                    "kick",
                    "ping",
                    "roll",
                    "server",
                    "slowmode",
                    "timeout",
                    "untimeout",
                    "user",
                },
            )
        finally:
            await bot.close()


if __name__ == "__main__":
    unittest.main()
