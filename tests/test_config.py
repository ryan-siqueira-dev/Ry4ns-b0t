import unittest

from ry4ns_bot.config import ConfigurationError, load_settings


class LoadSettingsTests(unittest.TestCase):
    def test_requires_token(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, "DISCORD_TOKEN"):
            load_settings(env={})

    def test_trims_token_and_omits_missing_guild(self) -> None:
        settings = load_settings(env={"DISCORD_TOKEN": "  token-value  "})

        self.assertEqual(settings.discord_token, "token-value")
        self.assertIsNone(settings.discord_guild_id)

    def test_rejects_token_placeholder(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, "DISCORD_TOKEN"):
            load_settings(
                env={
                    "DISCORD_TOKEN": "replace_with_your_bot_token",
                }
            )

    def test_rejects_example_guild_placeholder(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, "DISCORD_GUILD_ID"):
            load_settings(
                env={
                    "DISCORD_TOKEN": "token-value",
                    "DISCORD_GUILD_ID": "replace_with_your_test_server_id",
                }
            )

    def test_allows_empty_guild_id(self) -> None:
        settings = load_settings(
            env={
                "DISCORD_TOKEN": "token-value",
                "DISCORD_GUILD_ID": "",
            }
        )

        self.assertIsNone(settings.discord_guild_id)

    def test_accepts_valid_guild_id(self) -> None:
        settings = load_settings(
            env={
                "DISCORD_TOKEN": "token-value",
                "DISCORD_GUILD_ID": "1234567890",
            }
        )

        self.assertEqual(settings.discord_guild_id, 1234567890)

    def test_rejects_invalid_guild_id(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, "DISCORD_GUILD_ID"):
            load_settings(
                env={
                    "DISCORD_TOKEN": "token-value",
                    "DISCORD_GUILD_ID": "abc",
                }
            )

    def test_rejects_non_positive_guild_id(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, "positive integer"):
            load_settings(
                env={
                    "DISCORD_TOKEN": "token-value",
                    "DISCORD_GUILD_ID": "0",
                }
            )


if __name__ == "__main__":
    unittest.main()
