"""Paragraph evidence highlights work for paraphrases/English translations."""
import unittest
from urllib.parse import urlparse, parse_qs

from app import app, BOOK_PATH, INDEX, verified_response
from evidence_passages import page_passages, offered_passages, selected_passages


class TestAnswerHighlights(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http = app.test_client()

    def test_semantic_support_no_exact_quote_needed(self):
        excerpts = [{'page': 41, 'section': 'Validity', 'text': INDEX.pages[41]}]
        offered = offered_passages(str(BOOK_PATH), excerpts)
        self.assertGreaterEqual(len(offered[41]), 4)
        result = verified_response({
            'category': 'book',
            'book_answer': 'Validity concerns whether the intended construct is measured. [P41]',
            'outside_answer': '', 'referenced_pages': [41],
            'supporting_passages': [{'page': 41, 'ids': ['s0', 's3']}],
            'evidence_highlights': []
        }, excerpts, 'en', offered)
        url = result['sources'][0]['url']
        self.assertTrue(result['sources'][0]['has_highlights'])
        self.assertEqual(parse_qs(urlparse(url).query)['b'], ['s0', 's3'])
        overlay = self.http.get('/api/book/highlights/41?b=s0&b=s3')
        self.assertEqual(overlay.status_code, 200)
        self.assertEqual(overlay.json['matched'], 2)
        self.assertGreater(len(overlay.json['boxes']), 8)
        self.assertTrue(all(0 <= box['x'] <= 100 for box in overlay.json['boxes']))

    def test_validity_and_reliability_separate_paragraphs(self):
        entries = page_passages(str(BOOK_PATH), 41)
        self.assertTrue(any('mitataanko sitä' in p['text'] for p in entries))
        self.assertTrue(any('mittausvirhettä' in p['text'] for p in entries))
        self.assertGreaterEqual(len(entries), 4)

    def test_wrong_page_and_unoffered_ids_are_rejected(self):
        excerpts = [{'page': 41, 'section': 'Validity', 'text': INDEX.pages[41]}]
        offered = offered_passages(str(BOOK_PATH), excerpts)
        selected = selected_passages([
            {'page': 41, 'ids': ['s10000', 's0']},
            {'page': 42, 'ids': ['s0']}
        ], {41}, offered)
        self.assertEqual(selected, {41: ['s0']})
        endpoint = self.http.get('/api/book/highlights/41?b=s10000')
        self.assertEqual(endpoint.json['boxes'], [])

    def test_unquoted_old_answer_link_gets_fuzzy_passage_highlighting(self):
        response = self.http.get('/api/book/highlights/41?h=' +
                                 'Tiiviisti+ilmaistuna+validiteetti+kertoo+mitataanko+sitä')
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.json['matched'], 0)

    def test_outside_book_answer_has_no_highlight_links(self):
        excerpts = [{'page': 41, 'text': INDEX.pages[41], 'section': 'Validity'}]
        answer = verified_response({'category': 'related_outside',
                                    'book_answer': 'Unverified [P41]',
                                    'outside_answer': 'Outside the book.',
                                    'referenced_pages': [41],
                                    'supporting_passages': [{'page': 41, 'ids': ['s0']}],
                                    'evidence_highlights': []}, excerpts, 'en')
        self.assertEqual(answer['sources'], [])

    def test_fallback_cited_page_without_model_ids(self):
        excerpts = [{'page': 41, 'text': INDEX.pages[41], 'section': 'Validity'}]
        answer = verified_response({'category': 'book', 'book_answer': 'Validity. [P41]',
                                    'outside_answer': '', 'referenced_pages': [41],
                                    'supporting_passages': [], 'evidence_highlights': []},
                                   excerpts, 'en', fallback_query='validity reliability')
        self.assertTrue(answer['sources'][0]['has_highlights'])

    def test_reader_toggle_and_orange_css_are_available(self):
        html = self.http.get('/reader?page=41').data.decode()
        self.assertIn('reader-highlight-toggle', html)
        self.assertIn('reader-highlights', html)
        js = self.http.get('/static/reader.js').data.decode()
        self.assertIn("params.append('b', id)", js)
        css = self.http.get('/static/reader.css').data.decode()
        self.assertIn('rgba(255, 151, 25', css)


if __name__ == '__main__':
    unittest.main()
