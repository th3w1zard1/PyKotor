import unittest
from unittest.mock import Mock, patch
from pykotor.common.language import Language
from pykotor.tools.language_translator import Translator

class TestChunkParsing(unittest.TestCase):
    def setUp(self):
        # Mocking the translation API call, assuming it's an external service.
        # The YourTranslationClass and the actual method to be mocked should be replaced with the actual names.
        self.translator = Translator(Language.SPANISH)
        self.translator._initialized = True
        self.translator._translator = Mock()
        self.translator.to_lang = Language.ENGLISH
        self.translator.from_lang = Language.SPANISH

    def test_chunking_at_space(self):
        # Test that chunking occurs at space before the limit
        text = "This is a sample text that will be chunked."
        expected_chunks = ["This is a sample text ", "that will be chunked."]
        self.translator._translator.translate = Mock(side_effect=lambda x, src, dest: x)  # Mock translate function to return input
        result = self.translator.translate(text, to_lang=self.translator.to_lang, from_lang=self.translator.from_lang)
        self.translator._translator.translate.assert_has_calls([patch.call(chunk, src='es', dest='en') for chunk in expected_chunks], any_order=True)

    def test_chunking_at_sentence_end(self):
        # Test that chunking occurs at sentence end before the limit
        text = "This is a sentence. This is another sentence."
        expected_chunks = ["This is a sentence. ", "This is another sentence."]
        self.translator._translator.translate = Mock(side_effect=lambda x, src, dest: x)  # Mock translate function to return input
        result = self.translator.translate(text, to_lang=self.translator.to_lang, from_lang=self.translator.from_lang)
        self.translator._translator.translate.assert_has_calls([patch.call(chunk, src='es', dest='en') for chunk in expected_chunks], any_order=True)

    def test_chunking_with_long_word(self):
        # Test that chunking handles a very long word correctly
        text = "This is a sampletextthatwillbechunkedwithoutanyspaces"
        expected_chunks = ["This is a ", "sampletextthatwillbechunkedwithoutanyspaces"]
        self.translator._translator.translate = Mock(side_effect=lambda x, src, dest: x)  # Mock translate function to return input
        result = self.translator.translate(text, to_lang=self.translator.to_lang, from_lang=self.translator.from_lang)
        self.translator._translator.translate.assert_has_calls([patch.call(chunk, src='es', dest='en') for chunk in expected_chunks], any_order=True)

    def test_no_chunking_under_limit(self):
        # Test that no chunking occurs if text is under the limit
        text = "Short text."
        expected_chunks = [text]
        self.translator._translator.translate = Mock(side_effect=lambda x, src, dest: x)  # Mock translate function to return input
        result = self.translator.translate(text, to_lang=self.translator.to_lang, from_lang=self.translator.from_lang)
        self.translator._translator.translate.assert_called_once_with(text, src='es', dest='en')

    def test_chunking_preserves_punctuation(self):
        # Test that chunking preserves punctuation
        text = "Hello, world! This is a test."
        # Assuming the chunk size is 500, the text will not be chunked, so we expect it to be intact
        expected_chunks = [text]
        self.translator._translator.translate = Mock(side_effect=lambda x, src, dest: x)  # Mock translate function to return input
        result = self.translator.translate(text, to_lang=self.translator.to_lang, from_lang=self.translator.from_lang)
        self.translator._translator.translate.assert_called_once_with(text, src='es', dest='en')

if __name__ == '__main__':
    unittest.main()
