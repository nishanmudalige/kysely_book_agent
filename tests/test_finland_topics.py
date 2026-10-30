"""Pure offline tests for the Finland personality router and source notes.

Run: python -m unittest discover -s tests -p 'test_finland_topics.py' -v
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from finland_topics import finland_topic, finland_followup, FINLAND_REFERENCE, PERSONALITY_SYSTEM

class TestFinlandTopics(unittest.TestCase):
    def test_statistician_names_english_and_inflected_finnish(self):
        for q in ['Who is Seppo Mustonen?', 'Kerro Seppo Mustosesta',
                  'Who is Simo Puntanen?', 'Mikä on Lauri Tarkkosen merkitys?',
                  'Who influenced Kimmo Vehkalahti?', 'Who developed Survo?']:
            with self.subTest(q=q): self.assertEqual(finland_topic(q), 'statisticians')

    def test_finnish_statistical_history(self):
        for q in ['Who were important Finnish statisticians?',
                  'Kerro suomalaisista tilastotieteilijöistä',
                  'History of statistics in Finland']:
            with self.subTest(q=q): self.assertEqual(finland_topic(q), 'statisticians')

    def test_history_english_finnish(self):
        for q in ['Tell me about Finnish history', 'Kerro Suomen historiasta',
                  'When did Finland become independent?', 'Kerro Suomen itsenäistymisestä',
                  'Explain the Winter War', 'What happened in 1917 in Finland?',
                  'When did Helsinki become the capital?']:
            with self.subTest(q=q): self.assertEqual(finland_topic(q), 'history')

    def test_geography_english_finnish(self):
        for q in ['What is the geography of Finland?', 'What is Saimaa?',
                  'Missä on Lappi?', 'What is the biggest lake in Finland?',
                  'What is the capital of Finland?', 'Tell me about Rovaniemi',
                  'Suomen järvet ja saaristot', 'Where is Espoo?']:
            with self.subTest(q=q): self.assertEqual(finland_topic(q), 'geography')

    def test_does_not_hijack_book_questions(self):
        for q in ['What does the book say about Seppo Mustonen?',
                  'Mitä kirjassa sanotaan Tarkkosesta?',
                  'Who was mentioned on page 9?',
                  'According to the book, what is the role of Survo?']:
            with self.subTest(q=q): self.assertIsNone(finland_topic(q))

    def test_does_not_hijack_general_statistics_or_unrelated(self):
        for q in ['Explain linear regression', 'How is survey research conducted?',
                  'What does measurement reliability mean?', 'What is a histogram?',
                  'How do I calculate a p-value?', 'What is my favourite colour?',
                  'Best hockey team in Finland?', 'Who plays in the NHL?']:
            with self.subTest(q=q): self.assertIsNone(finland_topic(q))

    def test_conservative_topic_followups(self):
        self.assertEqual(finland_followup('What did he contribute?',
                                          'Who is Seppo Mustonen?'), 'statisticians')
        self.assertEqual(finland_followup('Milloin hän syntyi?',
                                          'Kerro Seppo Mustosesta'), 'statisticians')
        self.assertEqual(finland_followup('What happened there?',
                                          'Tell me about the Winter War'), 'history')
        self.assertEqual(finland_followup('Where is that?',
                                          'What is Saimaa?'), 'geography')
        self.assertIsNone(finland_followup('What is linear regression?',
                                           'Who is Seppo Mustonen?'))
        self.assertIsNone(finland_followup('What does the book say about him?',
                                           'Who is Seppo Mustonen?'))

    def test_reference_grounding(self):
        self.assertEqual(set(FINLAND_REFERENCE), {'statisticians', 'history', 'geography'})
        self.assertIn('Seppo Mustonen', FINLAND_REFERENCE['statisticians'])
        self.assertIn('Mustonen supervised', FINLAND_REFERENCE['statisticians'])
        self.assertIn('(/reader?page=9)', FINLAND_REFERENCE['statisticians'])
        self.assertIn('https://', FINLAND_REFERENCE['history'])
        self.assertIn('https://', FINLAND_REFERENCE['geography'])
        self.assertIn('not book excerpts', PERSONALITY_SYSTEM.lower())

if __name__ == '__main__': unittest.main()
