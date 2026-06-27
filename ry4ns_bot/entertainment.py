from __future__ import annotations

MAX_CHOICE_OPTIONS = 20


class ChoiceParseError(ValueError):
    """Raised when the choose command receives invalid options."""


def parse_choice_options(raw_options: str) -> list[str]:
    options = [option.strip() for option in raw_options.split(",") if option.strip()]

    if len(options) < 2:
        raise ChoiceParseError("Provide at least two options separated by commas.")

    if len(options) > MAX_CHOICE_OPTIONS:
        raise ChoiceParseError(f"Provide at most {MAX_CHOICE_OPTIONS} options.")

    return options
