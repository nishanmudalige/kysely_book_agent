import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from book_search import BookIndex, explicit_pages, glossary_expand, section_at


class TextbookTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.book = BookIndex(ROOT / 'data' / 'book.pdf')

    def test_book_identity(self):
        self.assertEqual(self.book.page_count, 223)
        self.assertIn('Kimmo Vehkalahti', self.book.pages[1])
        self.assertIn('Kyselytutkimuksen', self.book.pages[1])

    def test_attribution_and_licence(self):
        self.assertIn('CC BY', self.book.pages[2])
        self.assertIn('Helsingin yliopiston', self.book.pages[2])

    def test_page_link_matches_printed_page(self):
        self.assertIn('2.4.1', self.book.pages[41])
        self.assertEqual(explicit_pages('Translate page 41 into English', self.book.page_count), [41])
        self.assertEqual(explicit_pages('pp. 41-42', self.book.page_count), [41, 42])
        self.assertEqual(explicit_pages('Mitä sanotaan sivulla 116?', self.book.page_count), [116])

    def test_no_out_of_bounds_page_links(self):
        self.assertEqual(explicit_pages('page 500', self.book.page_count), [])

    def test_finnish_retrieval(self):
        matches = self.book.search('Mitä validiteetti tarkoittaa?')
        self.assertIn(41, [m['page'] for m in matches[:3]])

    def test_english_retrieval(self):
        matches = self.book.search('Explain factor analysis', glossary_expand('factor analysis'))
        self.assertTrue(any(93 <= m['page'] <= 101 for m in matches[:5]))

    def test_section_map(self):
        self.assertIn('Regressiodiagnostiikka', section_at(143))
        self.assertIn('Kyselytutkimus', section_at(12))


if __name__ == '__main__':
    unittest.main()
