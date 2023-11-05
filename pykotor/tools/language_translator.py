from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from deep_translator import GoogleTranslator as GoogleTranslatorDeep
from deep_translator import MyMemoryTranslator, PonsTranslator

if TYPE_CHECKING:
    from pykotor.common.language import Language


# Supported Translators
class TranslationOption(IntEnum):
    # DL_TRANSLATE = 2  # this translator is LARGE and SLOW  # noqa: ERA001
    GOOGLE_TRANSLATE=0
    PONS_TRANSLATOR=1
    MY_MEMORY_TRANSLATOR=2
    DEEPL=3
    #TRANSLATE = 99  # has api limits  # noqa: ERA001

class Translator:
    def __init__(self, from_lang: Language, translation_option: TranslationOption=TranslationOption.GOOGLE_TRANSLATE) -> None:
        self.to_lang: Language

        self.from_lang: Language = from_lang
        self.translation_option: TranslationOption = translation_option

        self._translator = None
        self._initialized = False

    def initialize(self) -> None:
        if self.translation_option == TranslationOption.GOOGLE_TRANSLATE:
            self._translator = GoogleTranslatorDeep
        elif self.translation_option == TranslationOption.PONS_TRANSLATOR:
            self._translator = PonsTranslator
        elif self.translation_option == TranslationOption.MY_MEMORY_TRANSLATOR:
            self._translator = MyMemoryTranslator
        elif self.translation_option == TranslationOption.DEEPL:
            from pykotor.tools.deepl_scraper import deepl_tr
            class AbstractTranslator:
                def __init__(self):
                    self.translate = None
            self._translator = AbstractTranslator()  # type: ignore[assignment]
            self._translator.translate = deepl_tr  # type: ignore[attr-defined]
        # this translator is LARGE and SLOW
        #elif self.translation_option == TranslationOption.DL_TRANSLATE:  # noqa: ERA001, RUF100
        #    import dl_translate as dlt  # noqa: ERA001
        #    self._translator = dlt.TranslationModel()  # noqa: ERA001
        # has api limits
        #elif self.translation_option == TranslationOption.TRANSLATE:  # noqa: ERA001, RUF100
        #    from translate import Translator  # noqa: ERA001
        #    self._translator = Translator(to_lang=self.to_lang.get_language_code())  # noqa: ERA001
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

        def translate_main(chunk: str, option: TranslationOption) -> str:
            translated_chunk: str
            if option in (
                TranslationOption.GOOGLE_TRANSLATE,
                TranslationOption.PONS_TRANSLATOR,
                TranslationOption.MY_MEMORY_TRANSLATOR,
            ):
                translated_chunk = self._translator(source=from_lang_code, target=to_lang_code).translate(chunk.strip())  # type: ignore[misc, reportOptionalCall, reportGeneralTypeIssues, attr-defined]
            elif option == TranslationOption.DEEPL:
                translated_chunk = self._translator.translate(chunk.strip(), from_lang.name, to_lang.name)  # type: ignore[attr-defined, reportOptionalCall, reportGeneralTypeIssues]
            # this translator is LARGE and SLOW
            #elif option == TranslationOption.DL_TRANSLATE:  # noqa: ERA001, RUF100
            #    translated_chunk = self._translator.translate(chunk, source=from_lang.name, target=to_lang.name)  # type: ignore[attr-defined, union-attr]  # noqa: ERA001
            # has api limits
            #elif option == TranslationOption.TRANSLATE:  # noqa: ERA001, RUF100
            #    translated_text = self._translator.translate(chunk)  # type: ignore[attr-defined]  # noqa: ERA001
            else:
                raise ValueError("Invalid translation option selected")  # noqa: TRY003, EM101
            return translated_chunk

        def adjust_cutoff(chunk: str, chunks: list[str]) -> str:
            if len(chunk) == max_chunk_length and not text[len(chunk)].isspace():
                cut_off = chunk.rfind(" ")
                next_chunk = chunk[cut_off:] + (chunks[chunks.index(chunk) + 1] if len(chunks) > chunks.index(chunk) + 1 else "")
                chunk = chunk[:cut_off]
                if next_chunk:
                    chunks[chunks.index(chunk) + 1] = next_chunk
            return chunk

        max_chunk_length = 1024
        if self.translation_option == TranslationOption.MY_MEMORY_TRANSLATOR:
            max_chunk_length = 500

        # Break the text into appropriate chunks
        chunks: list[str] = chunk_text(text, max_chunk_length)
        chunk: str
        try:
            for chunk in chunks:
                # Ensure not cutting off in the middle of a word
                chunk = adjust_cutoff(chunk, chunks)  # noqa: PLW2901

                # Translate each chunk, and concatenate the results
                translated_text += translate_main(chunk, self.translation_option)
            return translated_text  # noqa: TRY300
        except Exception as e:  # noqa: BLE001
            # Log the exception, proceed to the next translation option
            print(f"Translation using preferred translator '{self.translation_option.name}' failed: {e!r}")

        failed_option: TranslationOption = self.translation_option
        for option in TranslationOption.__members__.values():
            if option == failed_option:
                continue
            try:
                # Select the appropriate translator based on the option
                self.translation_option = option
                self.initialize()
                translated_text = ""

                # Break the text into appropriate chunks
                chunks = chunk_text(text, max_chunk_length)
                for chunk in chunks:
                    # Ensure not cutting off in the middle of a word
                    chunk = adjust_cutoff(chunk, chunks)  # noqa: PLW2901

                    translated_text += translate_main(chunk, option)
                    if not translated_text.strip() and chunk.strip():
                        msg = "No text returned."
                        raise ValueError(msg)  # noqa: TRY301
                # If translation succeeds, break out of the loop
                break
            except Exception as e:  # noqa: BLE001
                # Log the exception, proceed to the next translation option
                print(f"Translation using '{option.name}' failed: {e!r}")
                continue

        if not translated_text:
            msg = "All translation services failed."
            raise RuntimeError(msg)

        return translated_text
