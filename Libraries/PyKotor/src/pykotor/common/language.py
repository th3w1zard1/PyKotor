"""This module holds classes relating to string localization."""

from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING, Any, Generator, cast, overload

if TYPE_CHECKING:
    from typing_extensions import Self


# BCP 47 language code
class Language(IntEnum):
    """Language IDs recognized by both the games.

    Found in the TalkTable header, and CExoLocStrings (LocalizedStrings) within GFFs.

    References:
    ----------
        vendor/reone/include/reone/resource/types.h (Language enum)
        vendor/xoreos-tools/src/common/types.h (Language ID definitions)
        vendor/KotOR.js/src/resource/ResourceTypes.ts (Language enum)
        vendor/KotOR-dotNET/AuroraFile.cs (Language enum)
        Note: Official releases support English, French, German, Italian, Spanish, Polish
              Custom language support added for localization beyond official releases
    """

    # UNSET = 0x7FFFFFFF  # noqa: ERA001

    # The following languages have official releases
    # cp-1252
    ENGLISH = 0
    FRENCH = 1
    GERMAN = 2
    ITALIAN = 3
    SPANISH = 4
    POLISH = 5  # cp-1250, only released for K1.

    # Western European languages (cp1252 / ISO-8859-1)
    DUTCH = 6
    PORTUGUESE = 7
    DANISH = 8
    NORWEGIAN = 9
    SWEDISH = 10
    FINNISH = 11
    ICELANDIC = 12
    IRISH = 13
    SCOTTISH_GAELIC = 14
    WELSH = 15
    BRETON = 16
    CORNISH = 17
    MANX = 18
    CATALAN = 19
    BASQUE = 20
    GALICIAN = 21
    AFRIKAANS = 22
    SWAHILI = 23
    INDONESIAN = 24
    LUXEMBOURGISH = 25
    FAROESE = 26
    FRISIAN = 27
    OCCITAN = 28
    LATIN = 29
    ESPERANTO = 30
    MALTESE = 31

    # Central/Eastern European languages (cp1250 / ISO-8859-2)
    CZECH = 32
    SLOVAK = 33
    HUNGARIAN = 34
    ROMANIAN = 35
    CROATIAN = 36
    SERBIAN_LATIN = 37
    SLOVENE = 38
    BOSNIAN = 39
    MONTENEGRIN = 40

    # Cyrillic languages (cp1251 / ISO-8859-5 / KOI8-R)
    RUSSIAN = 41
    UKRAINIAN = 42
    BELARUSIAN = 43
    BULGARIAN = 44
    MACEDONIAN = 45
    SERBIAN_CYRILLIC = 46

    # Greek (cp1253 / ISO-8859-7)
    GREEK = 47

    # Turkish (cp1254 / ISO-8859-9)
    TURKISH = 48
    AZERI_LATIN = 49
    UZBEK_LATIN = 50

    # Hebrew (cp1255 / ISO-8859-8)
    HEBREW = 51

    # Arabic (cp1256 / ISO-8859-6)
    ARABIC = 52
    PERSIAN = 53
    URDU = 54

    # Baltic languages (cp1257 / ISO-8859-13)
    ESTONIAN = 55
    LATVIAN = 56
    LITHUANIAN = 57

    # Vietnamese (cp1258)
    VIETNAMESE = 58

    # Thai (cp874 / ISO-8859-11 / TIS-620)
    THAI = 59

    # Celtic languages (ISO-8859-14)
    IRISH_GAELIC = 60  # Additional Celtic variant

    # Nordic languages (ISO-8859-10)
    GREENLANDIC = 61
    SAMI = 62

    # Additional languages with SBCS support
    ALBANIAN = 63
    ASTURIAN = 64
    GUARANI = 65
    IGBO = 66
    NAURUAN = 67
    YORUBA = 68
    TSWANA = 69

    # The following languages are supported in the GFF/TLK file formats, but are probably not encodable to 8-bit without significant loss of information
    # therefore are probably incompatible with KOTOR.
    KOREAN = 128
    CHINESE_TRADITIONAL = 129
    CHINESE_SIMPLIFIED = 130
    JAPANESE = 131

    UNSET = 0x7FFFFFFF

    @classmethod
    def _missing_(cls, value: Any) -> Language:
        if not isinstance(value, int):
            return NotImplemented

        if value != 0x7FFFFFFF:  # 0x7FFFFFFF is unset/disabled/unused
            print(f"Language integer not known: {value}")
        return Language.ENGLISH

    def is_8bit_encoding(self) -> bool:
        return self not in {
            Language.KOREAN,
            Language.JAPANESE,
            Language.CHINESE_SIMPLIFIED,
            Language.CHINESE_TRADITIONAL,
        }

    def get_encoding(self) -> str | None:
        """Gets the encoding for a given language.

        Args:
        ----
            self: {Language}: The language to get the encoding for

        Returns:
        -------
            encoding (str): The encoding for the given language

        Processing Logic:
        ----------------
            - Check if language is in list of Latin-based languages and return "cp1252" encoding
            - Check if language is in list of Cyrillic-based languages and return "cp1251" encoding
            - Check if language is in list of Central European languages and return "cp1250" encoding
            - Check individual languages and return their specific encodings.
        """
        # Western European languages (cp1252 / ISO-8859-1)
        if self in {
            Language.ENGLISH,
            Language.FRENCH,
            Language.GERMAN,
            Language.ITALIAN,
            Language.SPANISH,
            Language.DUTCH,
            Language.PORTUGUESE,
            Language.DANISH,
            Language.NORWEGIAN,
            Language.SWEDISH,
            Language.FINNISH,
            Language.ICELANDIC,
            Language.IRISH,
            Language.SCOTTISH_GAELIC,
            Language.WELSH,
            Language.BRETON,
            Language.CORNISH,
            Language.MANX,
            Language.CATALAN,
            Language.BASQUE,
            Language.GALICIAN,
            Language.AFRIKAANS,
            Language.SWAHILI,
            Language.INDONESIAN,
            Language.LUXEMBOURGISH,
            Language.FAROESE,
            Language.FRISIAN,
            Language.OCCITAN,
            Language.LATIN,
            Language.ESPERANTO,
            Language.MALTESE,
            Language.GREENLANDIC,
            Language.ALBANIAN,
            Language.ASTURIAN,
            Language.GUARANI,
            Language.IGBO,
            Language.NAURUAN,
            Language.YORUBA,
            Language.TSWANA,
        }:
            return "cp1252"

        # Central/Eastern European languages (cp1250 / ISO-8859-2)
        if self in {
            Language.POLISH,
            Language.CZECH,
            Language.SLOVAK,
            Language.HUNGARIAN,
            Language.ROMANIAN,
            Language.CROATIAN,
            Language.SERBIAN_LATIN,
            Language.SLOVENE,
            Language.BOSNIAN,
            Language.MONTENEGRIN,
        }:
            return "cp1250"

        # Cyrillic languages (cp1251 / ISO-8859-5)
        if self in {
            Language.RUSSIAN,
            Language.UKRAINIAN,
            Language.BELARUSIAN,
            Language.BULGARIAN,
            Language.MACEDONIAN,
            Language.SERBIAN_CYRILLIC,
        }:
            return "cp1251"

        # Greek (cp1253 / ISO-8859-7)
        if self == Language.GREEK:
            return "cp1253"

        # Turkish (cp1254 / ISO-8859-9)
        if self in {
            Language.TURKISH,
            Language.AZERI_LATIN,
            Language.UZBEK_LATIN,
        }:
            return "cp1254"

        # Hebrew (cp1255 / ISO-8859-8)
        if self == Language.HEBREW:
            return "cp1255"

        # Arabic (cp1256 / ISO-8859-6)
        if self in {
            Language.ARABIC,
            Language.PERSIAN,
            Language.URDU,
        }:
            return "cp1256"

        # Baltic languages (cp1257 / ISO-8859-13)
        if self in {
            Language.ESTONIAN,
            Language.LATVIAN,
            Language.LITHUANIAN,
        }:
            return "cp1257"

        # Vietnamese (cp1258)
        if self == Language.VIETNAMESE:
            return "cp1258"

        # Thai (cp874 / ISO-8859-11 / TIS-620)
        if self == Language.THAI:
            return "cp874"

        # Celtic languages (ISO-8859-14) - can use cp1252 as fallback
        if self == Language.IRISH_GAELIC:
            return "cp1252"  # ISO-8859-14 not widely supported, cp1252 is close

        # Nordic languages (ISO-8859-10) - can use cp1252 as fallback
        if self == Language.SAMI:
            return "cp1252"  # ISO-8859-10 not widely supported, cp1252 is close

        # The following languages/encodings may not be 8-bit and need additional information in order to be supported.
        if self == Language.KOREAN:
            return "cp949"
        if self == Language.CHINESE_TRADITIONAL:
            return "cp950"
        if self == Language.CHINESE_SIMPLIFIED:
            return "cp936"
        if self == Language.JAPANESE:
            return "cp932"
        msg = f"No encoding defined for language: {self.name}"
        raise ValueError(msg)

    def get_bcp47_code(self):
        lang_map = {
            # Official releases
            Language.ENGLISH: "en",
            Language.FRENCH: "fr",
            Language.GERMAN: "de",
            Language.ITALIAN: "it",
            Language.SPANISH: "es",
            Language.POLISH: "pl",
            # Western European
            Language.DUTCH: "nl",
            Language.PORTUGUESE: "pt",
            Language.DANISH: "da",
            Language.NORWEGIAN: "no",
            Language.SWEDISH: "sv",
            Language.FINNISH: "fi",
            Language.ICELANDIC: "is",
            Language.IRISH: "ga",
            Language.SCOTTISH_GAELIC: "gd",
            Language.WELSH: "cy",
            Language.BRETON: "br",
            Language.CORNISH: "kw",
            Language.MANX: "gv",
            Language.CATALAN: "ca",
            Language.BASQUE: "eu",
            Language.GALICIAN: "gl",
            Language.AFRIKAANS: "af",
            Language.SWAHILI: "sw",
            Language.INDONESIAN: "id",
            Language.LUXEMBOURGISH: "lb",
            Language.FAROESE: "fo",
            Language.FRISIAN: "fy",
            Language.OCCITAN: "oc",
            Language.LATIN: "la",
            Language.ESPERANTO: "eo",
            Language.MALTESE: "mt",
            # Central/Eastern European
            Language.CZECH: "cs",
            Language.SLOVAK: "sk",
            Language.HUNGARIAN: "hu",
            Language.ROMANIAN: "ro",
            Language.CROATIAN: "hr",
            Language.SERBIAN_LATIN: "sr-Latn",
            Language.SLOVENE: "sl",
            Language.BOSNIAN: "bs",
            Language.MONTENEGRIN: "cnr",
            # Cyrillic
            Language.RUSSIAN: "ru",
            Language.UKRAINIAN: "uk",
            Language.BELARUSIAN: "be",
            Language.BULGARIAN: "bg",
            Language.MACEDONIAN: "mk",
            Language.SERBIAN_CYRILLIC: "sr-Cyrl",
            # Greek
            Language.GREEK: "el",
            # Turkish
            Language.TURKISH: "tr",
            Language.AZERI_LATIN: "az",
            Language.UZBEK_LATIN: "uz-Latn",
            # Hebrew
            Language.HEBREW: "he",
            # Arabic
            Language.ARABIC: "ar",
            Language.PERSIAN: "fa",
            Language.URDU: "ur",
            # Baltic
            Language.ESTONIAN: "et",
            Language.LATVIAN: "lv",
            Language.LITHUANIAN: "lt",
            # Vietnamese
            Language.VIETNAMESE: "vi",
            # Thai
            Language.THAI: "th",
            # Celtic
            Language.IRISH_GAELIC: "ga",
            # Nordic
            Language.GREENLANDIC: "kl",
            Language.SAMI: "se",
            # Additional
            Language.ALBANIAN: "sq",
            Language.ASTURIAN: "ast",
            Language.GUARANI: "gn",
            Language.IGBO: "ig",
            Language.NAURUAN: "na",
            Language.YORUBA: "yo",
            Language.TSWANA: "tn",
            # Non-SBCS languages
            Language.KOREAN: "ko",
            Language.CHINESE_TRADITIONAL: "zh-TW",  # zh-Hant
            Language.CHINESE_SIMPLIFIED: "zh-CN",  # zh-Hans
            Language.JAPANESE: "ja",
        }
        return lang_map.get(self)


class Gender(IntEnum):
    """Gender IDs recognized by both the games in regards to string localization."""

    MALE = 0  # or neutral
    FEMALE = 1


class IntKeyDict(dict):
    """This purely exists because something is setting the data with string key numbers incorrectly. This is a HACK:."""
    def __setitem__(self, key, value):
        if not isinstance(key, int):
            try:
                key = int(key)
            except ValueError as e:
                raise ValueError("Keys of the _substrings dictionary must be integers") from e
        super().__setitem__(key, value)


class LocalizedString:
    """Localized strings are a way of the game handling strings that need to be catered to a specific language or gender.

    This is achieved through either referencing a entry in the 'dialog.tlk' or by directly providing strings for each
    language.

    Attributes:
    ----------
        stringref: An index into the 'dialog.tlk' file. If this value is -1 the game will use the stored substrings.
    """

    def __init__(
        self,
        stringref: int,
        substrings: dict[int, str] | None = None,
    ):
        self.stringref: int = stringref
        self._substrings_internal: IntKeyDict = IntKeyDict() if substrings is None else IntKeyDict(substrings)

    @property
    def _substrings(self) -> dict[int, str]:
        """Property getter for the _substrings_internal dictionary."""
        return self._substrings_internal

    @_substrings.setter
    def _substrings(self, value: dict[int, str]):
        """Property setter for the _substrings_internal dictionary, ensuring keys are integers."""
        if value is not None:
            new_dict = IntKeyDict()
            for key, val in value.items():
                new_dict[key] = val
            self._substrings_internal = new_dict
        else:
            self._substrings_internal = IntKeyDict()

    def __iter__(self) -> Generator[tuple[Language, Gender, str], Any, None]:
        """Iterates through the list of substrings. Yields a tuple containing (language, gender, text)."""
        for substring_id, text in self._substrings.items():
            language, gender = LocalizedString.substring_pair(substring_id)
            yield language, gender, text

    def __len__(self):
        """Returns the number of substrings."""
        return len(self._substrings)

    def __hash__(self):
        return hash(self.stringref)

    def __str__(self):
        """If the stringref is valid, it will return it as a string. Otherwise it will return one of the substrings,
        prioritizing the english substring if it exists. If no substring exists and the stringref is invalid, "-1" is
        returned.
        """
        if self.stringref >= 0:
            return str(self.stringref)
        if self.exists(Language.ENGLISH, Gender.MALE):
            return str(self.get(Language.ENGLISH, Gender.MALE))
        # language either unset or not english.
        for _language, _gender, text in self:
            return text
        return "-1"

    def __eq__(self, other) -> bool:  # noqa: ANN001
        if self is other:
            return True
        if not isinstance(other, LocalizedString):
            return NotImplemented
        if other.stringref != self.stringref:
            return False
        return other._substrings == self._substrings

    def to_dict(self) -> dict[str, Any]:
        return {
            "stringref": self.stringref,
            "substrings": self._substrings
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        localized_string = cls(stringref=data.get("stringref", -1))
        localized_string._substrings = cast("dict[int, str]", data.get("substrings", {}))
        return localized_string

    @classmethod
    def from_invalid(cls) -> Self:
        return cls(-1)

    @classmethod
    def from_english(cls, text: str) -> Self:
        """Returns a new localizedstring object with a english substring.

        Args:
        ----
            text: the text for the english substring.

        Returns:
        -------
            a new localizedstring object.
        """
        locstring: Self = cls(-1)
        locstring.set_data(Language.ENGLISH, Gender.MALE, text)
        return locstring

    @overload
    @staticmethod
    def substring_id(language: Language, gender: Gender) -> int: ...
    @overload
    @staticmethod
    def substring_id(language: int, gender: int) -> int: ...
    @staticmethod
    def substring_id(language: Language | int, gender: Gender | int) -> int:
        """Returns the ID for the language gender pair.

        Supports both enum and integer arguments for backward compatibility.

        Args:
        ----
            language: The language (Language enum or int).
            gender: The gender (Gender enum or int).

        Returns:
        -------
            The substring ID.
        """
        # Handle integer arguments by converting to enums
        if isinstance(language, int):
            language_enum = Language(language)
        else:
            language_enum = language

        if isinstance(gender, int):
            gender_enum = Gender(gender)
        else:
            gender_enum = gender

        return (language_enum * 2) + gender_enum

    @staticmethod
    def substring_pair(substring_id: int | str) -> tuple[Language, Gender]:
        """Returns a tuple containing the Language and Gender for a given substring ID.

        Args:
        ----
            substring_id: The ID of the substring

        Returns:
        -------
            tuple: A tuple containing (Language, Gender)

        Processing Logic:
        ----------------
            - Divide the substring_id by 2 to get the Language id
            - Take the remainder of substring_id % 2 to get the Gender id
            - Return a tuple with the Language and Gender enum instances.
        """
        if not isinstance(substring_id, int):
            substring_id = int(substring_id)
        language = Language(substring_id // 2)
        gender = Gender(substring_id % 2)
        return language, gender

    @overload
    def set_data(self, language: Language, gender: Gender, string: str) -> None: ...
    @overload
    def set_data(self, language: int, gender: int, string: str) -> None: ...
    def set_data(
        self,
        language: Language | int,
        gender: Gender | int,
        string: str,
    ) -> None:
        """Sets the text of the substring with the corresponding language/gender pair.

        Supports both enum and integer arguments for backward compatibility.
        Can be called as:
        - set_data(Language.ENGLISH, Gender.MALE, "text") - enum arguments
        - set_data(0, 0, "text") - integer arguments

        Note: The substring is created if it does not exist.

        Args:
        ----
            language: The language (Language enum or int).
            gender: The gender (Gender enum or int).
            string: The new text for the new substring.
        """
        # Handle integer arguments by converting to enums
        if isinstance(language, int):
            language_enum = Language(language)
        else:
            language_enum = language

        if isinstance(gender, int):
            gender_enum = Gender(gender)
        else:
            gender_enum = gender

        substring_id: int = LocalizedString.substring_id(language_enum, gender_enum)
        self._substrings[substring_id] = string

    def set_string(self, substring_id: int | str, string: str) -> None:
        """Backward-compatible alias that uses numeric substring ids (language*2 + gender)."""
        language, gender = LocalizedString.substring_pair(int(substring_id))
        self.set_data(language, gender, string)

    @overload
    def get(self, language: Language, gender: Gender, *, use_fallback: bool = False) -> str | None: ...
    @overload
    def get(self, language: int, gender: int, *, use_fallback: bool = False) -> str | None: ...
    @overload
    def get(self, language: int, *, use_fallback: bool = False) -> str | None: ...
    def get(
        self,
        language: Language | int,
        gender: Gender | int | None = None,
        *,
        use_fallback: bool = False,
    ) -> str | None:
        """Gets the substring text with the corresponding language/gender pair.

        Supports both enum and integer arguments for backward compatibility.
        Can be called as:
        - get(Language.ENGLISH, Gender.MALE) - enum arguments
        - get(0, 0) - integer arguments
        - get(0) - single integer (gender defaults to 0/MALE)

        Args:
        ----
            language: The language (Language enum or int).
            gender: The gender (Gender enum or int).
                If None and language is int, defaults to Gender.MALE (0) for backward compatibility with get(0).

        Returns:
        -------
            The text of the substring if a matching pair is found, otherwise returns None.
        """
        # Handle integer arguments by converting to enums
        if isinstance(language, int):
            language_enum = Language(language)
        else:
            language_enum = language

        if gender is None:
            # Default to MALE if gender not provided (for backward compatibility with get(0))
            gender_enum = Gender.MALE
        elif isinstance(gender, int):
            gender_enum = Gender(gender)
        else:
            gender_enum = gender

        substring_id: int = LocalizedString.substring_id(language_enum, gender_enum)
        return self._substrings.get(substring_id, next(iter(self._substrings.values()), None) if use_fallback else None)

    @overload
    def remove(self, language: Language, gender: Gender) -> None: ...
    @overload
    def remove(self, language: int, gender: int) -> None: ...
    def remove(
        self,
        language: Language | int,
        gender: Gender | int,
    ) -> None:
        """Removes the existing substring with the respective language/gender pair if it exists.

        Supports both enum and integer arguments for backward compatibility.
        Can be called as:
        - remove(Language.ENGLISH, Gender.MALE) - enum arguments
        - remove(0, 0) - integer arguments

        Note: No error is thrown if it does not find a corresponding pair.

        Args:
        ----
            language: The language (Language enum or int).
            gender: The gender (Gender enum or int).
        """
        # Handle integer arguments by converting to enums
        if isinstance(language, int):
            language_enum = Language(language)
        else:
            language_enum = language

        if isinstance(gender, int):
            gender_enum = Gender(gender)
        else:
            gender_enum = gender

        substring_id: int = LocalizedString.substring_id(language_enum, gender_enum)
        self._substrings.pop(substring_id)

    @overload
    def exists(self, language: Language, gender: Gender) -> bool: ...
    @overload
    def exists(self, language: int, gender: int) -> bool: ...
    def exists(
        self,
        language: Language | int,
        gender: Gender | int,
    ) -> bool:
        """Returns whether or not a substring exists with the respective language/gender pair.

        Supports both enum and integer arguments for backward compatibility.
        Can be called as:
        - exists(Language.ENGLISH, Gender.MALE) - enum arguments
        - exists(0, 0) - integer arguments

        Args:
        ----
            language: The language (Language enum or int).
            gender: The gender (Gender enum or int).

        Returns:
        -------
            True if the corresponding substring exists.
        """
        # Handle integer arguments by converting to enums
        if isinstance(language, int):
            language_enum = Language(language)
        else:
            language_enum = language

        if isinstance(gender, int):
            gender_enum = Gender(gender)
        else:
            gender_enum = gender

        substring_id: int = LocalizedString.substring_id(language_enum, gender_enum)
        return substring_id in self._substrings
