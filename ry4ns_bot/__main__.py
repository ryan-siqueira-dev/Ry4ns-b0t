from .bot import create_bot
from .config import ConfigurationError, load_settings


def main() -> None:
    try:
        settings = load_settings()
    except ConfigurationError as exc:
        raise SystemExit(f"Configuration error: {exc}") from exc

    bot = create_bot(settings)
    bot.run(settings.discord_token)


if __name__ == "__main__":
    main()
