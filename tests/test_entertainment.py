import unittest

from ry4ns_bot.entertainment import ChoiceParseError, parse_choice_options


class ParseChoiceOptionsTests(unittest.TestCase):
    def test_parses_comma_separated_options(self) -> None:
        self.assertEqual(
            parse_choice_options("pizza, sushi, burger"),
            ["pizza", "sushi", "burger"],
        )

    def test_ignores_empty_options(self) -> None:
        self.assertEqual(
            parse_choice_options("pizza, , sushi, "),
            ["pizza", "sushi"],
        )

    def test_requires_at_least_two_options(self) -> None:
        with self.assertRaisesRegex(ChoiceParseError, "at least two"):
            parse_choice_options("pizza")

    def test_rejects_too_many_options(self) -> None:
        raw_options = ", ".join(str(index) for index in range(21))

        with self.assertRaisesRegex(ChoiceParseError, "at most 20"):
            parse_choice_options(raw_options)


if __name__ == "__main__":
    unittest.main()
