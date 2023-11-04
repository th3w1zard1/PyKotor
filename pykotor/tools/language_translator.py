from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
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
        translated_text: str = ""
        to_lang = to_lang or self.to_lang
        from_lang = from_lang or self.from_lang
        from_lang_code: str = from_lang.get_language_code()  # type: ignore[union-attr]
        to_lang_code: str = to_lang.get_language_code()  # type: ignore[union-attr]

        # Function to chunk the text into segments with a maximum of 500 characters
        def chunk_text(text: str, size):
            chunks = []
            while text:
                if len(text) <= size:
                    chunks.append(text)
                    break
                # Find the last complete word or sentence end within the size limit
                end = min(size, len(text))
                last_space = text.rfind(" ", 0, end)
                last_period = text.rfind(". ", 0, end)
                cut_off = max(last_space, last_period + 1) if last_period != -1 else last_space
                if cut_off == -1:  # In case there's a very long word
                    cut_off = size
                chunks.append(text[:cut_off])
                text = text[cut_off:].lstrip()  # Remove leading whitespace from next chunk
            return chunks

        # New function to remove and record punctuation and symbols
        def extract_and_index_punctuation(text: str):
            punctuation_indices = []
            clean_text = ""
            for index, character in enumerate(text):
                if character.isalnum() or character.isspace() or character in [".", ",", "!"]:
                    clean_text += character
                else:
                    punctuation_indices.append((index, character))
            return clean_text, punctuation_indices

        # New function to reintegrate punctuation and symbols
        def reintegrate_punctuation(translated_chunks, punctuation_indices):
            full_translation = "".join(translated_chunks)
            for index, symbol in reversed(punctuation_indices):
                full_translation = full_translation[:index] + symbol + full_translation[index:]
            return full_translation

        max_chunk_length = 1024
        if self.translation_option == TranslationOption.TRANSLATE:
            max_chunk_length = 500

        # Extract punctuation and symbols from the text and get their indices
        text_to_translate, punctuation_indices = extract_and_index_punctuation(text)

        # Break the text into appropriate chunks
        chunks = chunk_text(text_to_translate, max_chunk_length)

        translated_chunks: list[str] = []
        chunk: str
        for chunk in chunks:
            # Ensure not cutting off in the middle of a word
            if len(chunk) == max_chunk_length and not text[len(chunk)].isspace():
                cut_off = chunk.rfind(" ")
                next_chunk = chunk[cut_off:] + (chunks[chunks.index(chunk) + 1] if len(chunks) > chunks.index(chunk) + 1 else "")
                chunk = chunk[:cut_off]
                if next_chunk:
                    chunks[chunks.index(chunk) + 1] = next_chunk

            # Translate each chunk
            if self.translation_option == TranslationOption.GOOGLETRANS:
                translated_chunks.append(self._translator.translate(chunk, src=from_lang_code, dest=to_lang_code).text)  # type: ignore[attr-defined]
            elif self.translation_option == TranslationOption.LIBRE:
                if from_lang is None:
                    msg = "LibreTranslate requires a specified source language."
                    raise ValueError(msg)
                translated_chunks.append(self._translator.translate(chunk, source=from_lang_code, target=to_lang_code))  # type: ignore[attr-defined]
            elif self.translation_option == TranslationOption.DL_TRANSLATE:
                translated_chunks.append(self._translator.translate(chunk, source=from_lang.name, target=to_lang.name))  # type: ignore[attr-defined, union-attr]
            elif self.translation_option == TranslationOption.TRANSLATE:
                translated_chunks.append(self._translator.translate(chunk))  # type: ignore[attr-defined]
            else:
                msg = "Invalid translation option selected"
                raise ValueError(msg)

        # Reintegrate the punctuation and symbols
        # translated_text = reintegrate_punctuation(translated_chunks, punctuation_indices)  # type: ignore[reportGeneralTypeIssues]

        return " ".join(translated_chunks)
