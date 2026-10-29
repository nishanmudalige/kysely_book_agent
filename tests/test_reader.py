"""Integration tests for the plugin-independent textbook reader."""
import io
import json
import unittest

import fitz
from app import app, INDEX, verified_response


class TestReader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()

    def test_reader_is_html_not_inline_pdf(self):
        for route in ['/reader?page=41', '/book.pdf']:
            response = self.client.get(route)
            self.assertEqual(response.status_code, 200)
            self.assertIn('text/html', response.content_type)
            self.assertIn(b'Kimmo Vehkalahti', response.data)

    def test_reader_home_and_chapter_links(self):
        response = self.client.get('/')
        self.assertIn(b'href="/reader"', response.data)
        self.assertIn(b'href="/reader?page=87"', response.data)
        self.assertNotIn(b'/book.pdf#page=', response.data)

    def test_png_pages_are_correct_and_valid(self):
        for page in [1, 41, 93, 223]:
            response = self.client.get(f'/api/book/page/{page}.png?scale=2')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.mimetype, 'image/png')
            self.assertTrue(response.data.startswith(b'\x89PNG\r\n\x1a\n'))
            self.assertEqual(len(fitz.Pixmap(response.data).samples) > 0, True)

    def test_page_bounds(self):
        self.assertEqual(self.client.get('/api/book/page/0.png').status_code, 404)
        self.assertEqual(self.client.get('/api/book/page/224.png').status_code, 404)
        self.assertEqual(self.client.get('/api/book/page/41.png?scale=10').status_code, 400)
        self.assertEqual(self.client.get('/api/book/page/41.png?scale=nan').status_code, 400)
        self.assertEqual(self.client.get('/api/book/text/224').status_code, 404)

    def test_page_text(self):
        response = self.client.get('/api/book/text/41')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Validiteetti', response.json['text'])

    def test_search_finnish(self):
        response = self.client.get('/api/book/search?q=validiteetti')
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.json['count'], 0)
        self.assertTrue(any(x['page'] == 41 for x in response.json['results']))

    def test_search_escaping(self):
        response = self.client.get('/api/book/search?q=%3Cscript%3E')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json['results'], list)

    def test_page_highlights(self):
        response = self.client.get('/api/book/highlights/41?q=Validiteetti')
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json['boxes']), 0)
        for box in response.json['boxes']:
            for axis in ('x', 'y', 'w', 'h'):
                self.assertGreaterEqual(box[axis], 0)
                self.assertLessEqual(box[axis], 100)

    def test_raw_pdf_download_route(self):
        response = self.client.get('/book/download')
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response.headers.get('Content-Disposition', ''))
        self.assertTrue(response.data.startswith(b'%PDF-'))

    def test_claude_sources_link_to_html_reader(self):
        result = verified_response({'category': 'book', 'book_answer': 'Source [P41].',
                                    'referenced_pages': [41]},
                                   [{'page': 41, 'text': 'Validiteetti', 'section': '2.4.1'}], 'en')
        self.assertEqual(result['sources'][0]['url'], '/reader?page=41')


if __name__ == '__main__':
    unittest.main()
