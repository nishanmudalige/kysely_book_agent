"""Offline checks for the optional non-textbook hockey personality and standings."""
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hockey import (
    hockey_intent, in_finnish, parse_standings, standings_answer,
    favourite_answer, official_standings, _load_standings_from_api,
)


def league_fixture():
    names = ['Lukko', 'SaiPa', 'Jukurit', 'Kärpät', 'Ilves', 'JYP', 'TPS',
             'Ässät', 'Tappara', 'K-Espoo', 'Pelicans', 'HIFK', 'KalPa',
             'HPK', 'Sport', 'Jokerit', 'KooKoo']
    return [{'tournament': 'runkosarja', 'ranking': i,
             'team': {'name': name}, 'games': 18, 'points': 44 - 2 * i}
            for i, name in enumerate(names, 1)]


class TestHockey(unittest.TestCase):
    def test_intent_english_and_finnish(self):
        self.assertEqual(hockey_intent('What is the best hockey team in Finland?'), 'standings')
        self.assertEqual(hockey_intent('Mikä on Suomen paras jääkiekkojoukkue?'), 'standings')
        self.assertEqual(hockey_intent('Who is your favourite hockey team?'), 'favourite')
        self.assertEqual(hockey_intent('Kerro suomalaisista NHL-pelaajista'), 'general')
        self.assertEqual(hockey_intent('Tell me about Mikko Rantanen'), 'general')
        self.assertIsNone(hockey_intent('What is measurement reliability?'))
        self.assertIsNone(hockey_intent('Explain linear regression'))

    def test_automatic_finnish_english(self):
        self.assertTrue(in_finnish('Mikä on Suomen paras jääkiekkojoukkue?', 'auto'))
        self.assertFalse(in_finnish('Best hockey team in Finland?', 'auto'))
        self.assertTrue(in_finnish('Best hockey team in Finland?', 'fi'))
        self.assertFalse(in_finnish('Mikä on suosikkijoukkueesi?', 'en'))

    def test_accept_standings_and_reject_ambiguous_or_stale(self):
        table = parse_standings({'runkosarja': league_fixture()})
        self.assertEqual(len(table), 17)
        self.assertEqual(table[0]['team'], 'Lukko')
        self.assertEqual(table[-2]['team'], 'Jokerit')
        self.assertEqual(parse_standings({'standings': [
            {'team': {'name': 'Jokerit'}, 'ranking': 1, 'points': 70, 'games': 24}]}), [])
        self.assertEqual(parse_standings({'standings': league_fixture() + [
            {'tournament':'playoffs', 'ranking': 1, 'team': 'Jokerit', 'points': 2, 'games': 2}]}), table)
        confusing = league_fixture() + [{**league_fixture()[0], 'points': 99}]
        self.assertEqual(parse_standings(confusing), [])

    def test_standings_answer_objective_then_favourite(self):
        ans = standings_answer('Who is the best?', False,
                               table=parse_standings(league_fixture()), season_end=2027)
        self.assertIn('**Lukko** leads', ans)
        self.assertIn('**Helsingin Jokerit**', ans)
        self.assertIn('Jokerit is **16th**', ans)
        self.assertIn('https://liiga.fi/', ans)
        self.assertLess(ans.index('**Lukko** leads'), ans.index('My favourite team'))
        fi = standings_answer('Kuka on paras?', True,
                              table=parse_standings(league_fixture()), season_end=2027)
        self.assertIn('Sarjaa johtaa **Lukko**', fi)
        self.assertIn('**Helsingin Jokerit**', fi)

    def test_no_fake_standings_on_failed_network(self):
        ans = standings_answer('Best?', False, table=[], season_end=2027)
        self.assertIn('could not verify', ans)
        self.assertNotIn('leads with', ans)
        self.assertIn('Helsingin Jokerit', ans)

    def test_real_source_network_request_mocked(self):
        class Reply:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, *args): return json.dumps({'standings': league_fixture()}).encode()
        _load_standings_from_api.cache_clear()
        with patch('hockey.urlopen', return_value=Reply()) as getter:
            table = official_standings(2027)
            self.assertEqual(table[0]['team'], 'Lukko')
            self.assertEqual(table[15]['team'], 'Jokerit')
            self.assertIn('season=2027', getter.call_args.args[0].full_url)
        _load_standings_from_api.cache_clear()

    def test_no_book_claims_in_hockey_favorite(self):
        for fi in (True, False):
            answer = favourite_answer(fi)
            self.assertIn('Helsingin Jokerit', answer)
            self.assertNotIn('[P', answer)


if __name__ == '__main__':
    unittest.main()
