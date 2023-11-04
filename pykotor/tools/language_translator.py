from __future__ import annotations

from enum import IntEnum

from pykotor.common.language import Language


# Supported Translators
class TranslationOption(IntEnum):
    GOOGLETRANS = 0
    LIBRE = 1
    DL_TRANSLATE = 2
    TRANSLATE = 3

class Translator:
    def __init__(self, from_lang: Language, translation_option: TranslationOption=TranslationOption.DL_TRANSLATE) -> None:
        self.to_lang = None
        self.from_lang = from_lang
        self.translation_option: TranslationOption = translation_option
        self._translator = None
        self._initialized = False

    def initialize(self) -> None:
        # Google Translate
        if self.translation_option == TranslationOption.GOOGLETRANS:
            from googletrans import Translator as GoogleTranslator
            self._translator = GoogleTranslator()
        # LibreTranslate
        elif self.translation_option == TranslationOption.LIBRE:
            from libretranslatepy import LibreTranslateAPI
            self._translator = LibreTranslateAPI("https://translate.argosopentech.com/")
        elif self.translation_option == TranslationOption.DL_TRANSLATE:
            import dl_translate as dlt
            self._translator = dlt.TranslationModel()
        elif self.translation_option == TranslationOption.TRANSLATE:
            from translate import Translator
            self._translator = Translator(to_lang=self.to_lang.get_language_code())
        else:
            msg = "Invalid translation option selected"
            raise ValueError(msg)
        self._initialized = True

    def translate(self, text: str, from_lang: Language | None = None, to_lang: Language | None = None) -> str:
        if not self._initialized:
            self.initialize()
        translated_text = text
        to_lang = to_lang or self.to_lang
        from_lang = (from_lang or self.from_lang)
        from_lang_code: str = from_lang.get_language_code()
        to_lang_code: str = to_lang.get_language_code()

        if self.translation_option == TranslationOption.GOOGLETRANS:
            translated_text = self._translator.translate(text, src=from_lang_code, dest=to_lang_code).text  # type: ignore[attr-defined]
        elif self.translation_option == TranslationOption.LIBRE:
            if from_lang is None:
                msg = "LibreTranslate requires a specified source language."
                raise ValueError(msg)
            translated_text = self._translator.translate(text, source=from_lang_code, target=to_lang_code)  # type: ignore[attr-defined]
        elif self.translation_option == TranslationOption.DL_TRANSLATE:
            translated_text = self._translator.translate(text, source=from_lang.name, target=to_lang.name)  # type: ignore[attr-defined, union-attr]
        elif self.translation_option == TranslationOption.TRANSLATE:
            translated_text = self._translator.translate(text)  # type: ignore[attr-defined]
        else:
            msg = "Invalid translation option selected"
            raise ValueError(msg)

        return translated_text  # type: ignore[reportGeneralTypeIssues]
