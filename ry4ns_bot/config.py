from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - only used before dependencies are installed
    def load_dotenv(*_args: object, **_kwargs: object) -> bool:
        return False


class ConfigurationError(RuntimeError):
    """Raised when required bot configuration is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    discord_token: str
    discord_guild_id: int | None


TOKEN_PLACEHOLDERS = {"replace_with_your_bot_token"}
GUILD_ID_PLACEHOLDERS = {"replace_with_your_test_server_id"}


def load_settings(
    env: Mapping[str, str] | None = None,
    env_file: str | os.PathLike[str] | None = ".env",
) -> Settings:
    if env is None:
        if env_file is not None:
            load_dotenv(Path(env_file))
        env = os.environ

    token = env.get("DISCORD_TOKEN", "").strip()
    if not token or token in TOKEN_PLACEHOLDERS:
        raise ConfigurationError("DISCORD_TOKEN is required.")

    guild_id = _parse_optional_positive_int(
        env.get("DISCORD_GUILD_ID", ""),
        "DISCORD_GUILD_ID",
    )

    return Settings(discord_token=token, discord_guild_id=guild_id)


def _parse_optional_positive_int(raw_value: str, name: str) -> int | None:
    value = raw_value.strip()
    if not value:
        return None

    if value in GUILD_ID_PLACEHOLDERS:
        raise ConfigurationError(f"{name} must be a positive integer or empty.")

    try:
        parsed = int(value)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be a positive integer.") from exc

    if parsed <= 0:
        raise ConfigurationError(f"{name} must be a positive integer.")

    return parsed
