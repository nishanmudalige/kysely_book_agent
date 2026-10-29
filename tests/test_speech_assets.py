"""Dependency-free checks for read-aloud interface integration."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class SpeechAssetsTest(unittest.TestCase):
    def test_both_pages_load_player(self):
        for page in ("index.html", "reader.html"):
            html = (ROOT / "templates" / page).read_text()
            for required in ('speech.js', 'speech.css', 'speech-player', 'speech-trigger',
                             'speech-play', 'speech-pause', 'speech-restart', 'speech-stop',
                             'speech-voice', 'speech-rate', 'speech-selection-action'):
                self.assertIn(required, html, (page, required))

    def test_player_exposes_lang_detection(self):
        code = (ROOT / 'static/speech.js').read_text()
        for required in ('detectLanguage', 'voiceschanged', 'SpeechSynthesisUtterance',
                         "'fi-FI'", "'en-US'", 'setSpeechText', 'readText'):
            self.assertIn(required, code)

    def test_reader_source_passage_playback(self):
        script = (ROOT / 'static/reader.js').read_text()
        backend = (ROOT / 'app.py').read_text()
        self.assertIn("$('reader-read-highlights')", script)
        self.assertIn('passage_texts', backend)
        self.assertIn('window.KyselySpeech?.readText', script)

    def test_reply_language_remains_independent(self):
        chat = (ROOT / 'static/app.js').read_text()
        self.assertIn("language: language.value", chat)
        self.assertNotIn("language.value = button.dataset.language", chat)


if __name__ == '__main__':
    unittest.main()
