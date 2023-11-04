"""This module holds classes relating to string localization."""
from __future__ import annotations

from enum import IntEnum
from typing import Any


class Language(IntEnum):
    """Language IDs recognized by both the games."""

    ENGLISH = 0
    FRENCH = 1
    GERMAN = 2
    ITALIAN = 3
    SPANISH = 4
    POLISH = 5

    @staticmethod
    def _missing_(value: int) -> IntEnum:
        if value != 0x7FFFFFFF:  # unused?
            print(f"Missing language int {value}")
        return Language.ENGLISH

    def get_language_code(self):
        if self == Language.ENGLISH:
            return "en"
        if self == Language.FRENCH:
            return "fr"
        if self == Language.GERMAN:
            return "de"
        if self == Language.ITALIAN:
            return "it"
        if self == Language.SPANISH:
            return "es"
        if self == Language.POLISH:
            return "pl"

        return None  # or raise an error


class Gender(IntEnum):
    """Gender IDs recognized by both the games in regards to string localization."""

    MALE = 0  # or neutral
    FEMALE = 1


class LocalizedString:
    """Localized strings are a way of the game handling strings that need to be catered to a specific language or gender.

    This is achieved through either referencing a entry in the 'dialog.tlk' or by directly providing strings for each
    language.

    Attributes
    ----------
        stringref: An index into the 'dialog.tlk' file. If this value is -1 the game will use the stored substrings.
    """

    def __init__(self, stringref: int):
        self.stringref: int = stringref
        self._substrings: dict[int, str] = {}

    def __iter__(self):
        """Iterates through the list of substrings. Yields a tuple containing [language, gender, text]."""
        for substring_id, text in self._substrings.items():
            language, gender = LocalizedString.substring_pair(substring_id)
            yield language, gender, text

    def __len__(self):
        """Returns the number of substrings."""
        return len(self._substrings)

    def __str__(self):
        """If the stringref is valid, it will return it as a string. Otherwise it will return one of the substrings,
        prioritizing the english substring if it exists. If no substring exists and the stringref is invalid, "-1" is
        returned.
        """
        if self.stringref >= 0:
            return str(self.stringref)
        if self.exists(Language.ENGLISH, Gender.MALE):
            return str(self.get(Language.ENGLISH, Gender.MALE))
        for _language, _gender, text in self:
            return text
        return "-1"

    def __eq__(self, other: str | Any) -> bool:
        if not isinstance(other, LocalizedString):
            return False
        if other.stringref != self.stringref:
            return False
        return other._substrings == self._substrings

    def __hash__(self):
        return hash(self.stringref)

    @staticmethod
    def from_invalid() -> LocalizedString:
        return LocalizedString(-1)

    @staticmethod
    def from_english(text: str) -> LocalizedString:
        """Returns a new localizedstring object with a english substring.

        Args:
        ----
            text: the text for the english substring.

        Returns:
        -------
            a new localizedstring object.
        """
        locstring = LocalizedString(-1)
        locstring.set_data(Language.ENGLISH, Gender.MALE, text)
        return locstring

    @staticmethod
    def substring_id(language: Language, gender: Gender) -> int:
        """Returns the ID for the language gender pair.

        Args:
        ----
            language: The language.
            gender: The gender.

        Returns:
        -------
            The substring ID.
        """
        return (language * 2) + gender

    @staticmethod
    def substring_pair(substring_id: int) -> tuple[Language, Gender]:
        """Returns the language gender pair from a substring ID.

        Args:
        ----
            substring_id: The substring ID.

        Returns:
        -------
            A tuple organized as (language, gender).
        """
        language = Language(substring_id // 2)
        gender = Gender(substring_id % 2)
        return language, gender

    def set_data(self, language: Language, gender: Gender, string: str) -> None:
        """Sets the text of the substring with the corresponding language/gender pair. The substring is created if it does
        not exist.

        Args:
        ----
            language: The language.
            gender: The gender.
            string: The new text for the new substring.
        """
        substring_id = LocalizedString.substring_id(language, gender)
        self._substrings[substring_id] = string

    def get(self, language: Language, gender: Gender) -> str | None:
        """Gets the substring text with the corresponding language/gender pair.

        Args:
        ----
            language: The language.
            gender: The gender.

        Returns:
        -------
            The text of the substring if a matching pair is found, otherwise returns None.
        """
        substring_id = LocalizedString.substring_id(language, gender)
        return self._substrings[substring_id] if substring_id in self._substrings else None

    def remove(self, language: Language, gender: Gender) -> None:
        """Removes the existing substring with the respective language/gender pair if it exists. No error is thrown if it
        does not find a corresponding pair.

        Args:
        ----
            language: The language.
            gender: The gender.
        """
        substring_id = LocalizedString.substring_id(language, gender)
        self._substrings.pop(substring_id)

    def exists(self, language: Language, gender: Gender) -> bool:
        """Returns whether or not a substring exists with the respective language/gender pair.

        Args:
        ----
            language: The language.
            gender: The gender.

        Returns:
        -------
            True if the corresponding substring exists.
        """
        substring_id = LocalizedString.substring_id(language, gender)
        return substring_id in self._substrings
