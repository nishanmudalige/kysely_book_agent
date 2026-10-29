"""New tests for validated textbook evidence highlights and reader links."""
import unittest
from urllib.parse import urlparse, parse_qs
from app import app, INDEX, verified_response, validated_evidence

QUOTE = 'Tiiviisti ilmaistuna validiteetti kertoo, mitataanko sitä, mitä piti'


class TestAnswerHighlights(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http = app.test_client()

    def test_valid_original_pdf_text_is_highlighted(self):
        original = [{'page': 41, 'section': 'Validiteetti', 'text': INDEX.pages[41]}]
        response = verified_response({
            'category': 'book', 'book_answer': 'Validity asks if the intended construct was measured. [P41]',
            'outside_answer': '', 'referenced_pages': [41],
            'evidence_highlights': [{'page': 41, 'quote': QUOTE}]}, original, 'en')
        self.assertEqual(response['sources'][0]['page'], 41)
        self.assertTrue(response['sources'][0]['has_highlights'])
        link = response['sources'][0]['url']
        self.assertEqual(parse_qs(urlparse(link).query)['h'], [QUOTE])
        rectangles = self.http.get('/api/book/highlights/41?h=' + parse_qs(urlparse(link).query)['h'][0].replace(' ', '+'))
        self.assertEqual(rectangles.status_code, 200)
        self.assertGreater(len(rectangles.json['boxes']), 0)
        self.assertEqual(rectangles.json['matched'], 1)

    def test_invented_evidence_is_never_highlighted(self):
        excerpts = [{'page': 41, 'text': INDEX.pages[41], 'section': 'Validiteetti'}]
        bad = validated_evidence([{'page': 41, 'quote': 'The book proves cats can write computer code.'}], {41}, excerpts)
        self.assertEqual(bad, {})

    def test_answer_evidence_must_be_on_cited_page_and_in_excerpt(self):
        excerpts = [{'page': 41, 'text': 'Validiteetti ja reliabiliteetti', 'section': 'Validiteetti'}]
        self.assertEqual(validated_evidence([{'page': 41, 'quote': QUOTE}], {41}, excerpts), {})
        self.assertEqual(validated_evidence([{'page': 40, 'quote': QUOTE}], {41}, excerpts), {})

    def test_outside_book_answer_has_no_highlight_links(self):
        excerpts = [{'page': 41, 'text': INDEX.pages[41], 'section': 'Validiteetti'}]
        answer = verified_response({'category': 'related_outside', 'book_answer': 'Misleading [P41]',
                                    'outside_answer': 'This is outside the book.',
                                    'referenced_pages': [41],
                                    'evidence_highlights': [{'page': 41, 'quote': QUOTE}]}, excerpts, 'en')
        self.assertEqual(answer['sources'], [])

    def test_reader_toggle_and_orange_css_are_available(self):
        html = self.http.get('/reader?page=41').data.decode()
        self.assertIn('reader-highlight-toggle', html)
        self.assertIn('reader-highlight-note', html)
        self.assertIn('reader-highlights', html)
        css = self.http.get('/static/reader.css').data.decode()
        self.assertIn('rgba(255, 151, 25', css)


if __name__ == '__main__':
    unittest.main()
