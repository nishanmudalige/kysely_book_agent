"""Small, explicitly non-textbook hockey exception for KyselyTutor.

Official Liiga standings are requested live from Liiga's public JSON endpoint.
No rankings or current statistics are inferred when that endpoint is unavailable.
"""
from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
import time
import json
import re
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

STANDINGS_API = 'https://liiga.fi/api/v2/standings/'
STANDINGS_PAGE = 'https://liiga.fi/fi/tilastot/joukkuetilastot/kausi?tilasto=sarjataulukko&sarja=runkosarja'
NHL_PLAYERS_PAGE = 'https://www.nhl.com/players'

# A fixed, verifiable 2026-27 snapshot: don't claim it is a live roster.
# Clubs may change; for current details, the answer should direct readers to NHL.com.
NHL_SNAPSHOT = '''Finnish players and their NHL clubs at the start of the 2026–27 season
(as reported in October 2026; club assignments can change):
- Aleksander Barkov — Florida Panthers, centre and captain.
- Anton Lundell — Florida Panthers, centre.
- Sebastian Aho — Carolina Hurricanes, centre.
- Mikko Rantanen — Dallas Stars, winger.
- Miro Heiskanen — Dallas Stars, defenceman.
- Roope Hintz — Dallas Stars, centre.
- Juuse Saros — Nashville Predators, goaltender.
- Artturi Lehkonen — Colorado Avalanche, winger.
- Kaapo Kakko — Seattle Kraken, winger.
- Teuvo Teräväinen — Chicago Blackhawks, winger.
- Kevin Lankinen — Vancouver Canucks, goaltender.
- Mikael Granlund — Anaheim Ducks, forward.
For updated rosters/statistics use https://www.nhl.com/players .
Snapshot reference: https://suomalaisetnhlssa.fi/pelaajat/
'''

_HOCKEY_RE = re.compile(
    r'(?i)\b(?:hockey|ice\s+hockey|nhl|liiga|mestis|jokerit|jääkiek\w*|'
    r'kiekko\w*|kiekkoi\w*|sarjataulukk\w*|stanley\s+cup|'
    r'(?:finnish|suomalais\w*)\s+(?:nhl|hockey|ice\s+hockey)|'
    r'(?:favorite|favourite|paras|parha\w*|suosikki\w*)\s+(?:hockey\s+)?(?:team|joukkue\w*)|'
    r'Barkov|Rantanen|Heiskanen|Hintz|Saros|Lundell|Lehkonen|Granlund|Teräväinen|Aho)\b'
)
_STANDINGS_RE = re.compile(
    r'(?i)(?:\b(?:standings|league\s+table|league\s+leaders?|top\s+(?:team|club)|'
    r'best\s+(?:hockey\s+|ice\s+hockey\s+)?team|'
    r'first\s+place|who\s+is\s+(?:top|leading)|which\s+(?:hockey\s+)?team\s+is\s+(?:best|top)|'
    r'(?:which|what)\s+team\s+leads|(?:current\s+)?ranking\w*|\brank\b|\bposition\b)\b|'
    r'\b(?:sarjataulukk\w*|sarjatilanne|sarjajohtaja|kärki\w*|'
    r'paras\s+(?:jääkiekko\w*|liiga\w*|joukkue\w*|suomalainen\s+joukkue\w*)|'
    r'mikä\s+joukkue\s+(?:on\s+)?paras|kuka\s+johtaa\s+liigaa|'
    r'sijoitu\w*|monenten\w*|mikä.{0,55}jääkiekko.{0,55}paras)\b)'
)
_FAVOURITE_RE = re.compile(
    r'(?i)\b(?:favou?rite|fan\s+of|root\s+for|support|suosikki\w*|'
    r'kannata\w*|lempi\w*|fanitat\w*)\b'
)

def hockey_intent(question: str) -> str | None:
    """Return standings, favourite or general hockey; do not hijack survey questions."""
    q = ' '.join(question.split())
    if not _HOCKEY_RE.search(q):
        return None
    if _STANDINGS_RE.search(q):
        return 'standings'
    if _FAVOURITE_RE.search(q) and not re.search(r'(?i)\b(?:nhl\s+players?|pelaaj\w*)\b', q):
        return 'favourite'
    return 'general'


def in_finnish(question: str, requested_language: str) -> bool:
    if requested_language == 'fi':
        return True
    if requested_language == 'en':
        return False
    return bool(re.search(r'(?i)\b(?:mikä|mitä|kuka|ketkä|paras|suomessa|suomalais\w*|'
                          r'joukkue\w*|jääkiek\w*|kerro|kuinka|kumpi|miksi|onko)\b', question))


def current_season_end() -> int:
    today = datetime.now(ZoneInfo('Europe/Helsinki'))
    return today.year + (1 if today.month >= 8 else 0)


def standings_url(season_end: int) -> str:
    return f'{STANDINGS_PAGE}&kaudesta={season_end}&kauteen={season_end}'


def _integer(x):
    if isinstance(x, bool): return None
    try:
        v = int(x)
        return v if str(x).strip().lstrip('+-').isdigit() else None
    except (TypeError, ValueError): return None


def _name(value):
    if isinstance(value, str): return value.strip()
    if isinstance(value, dict):
        for key in ('name', 'teamName', 'team_name', 'displayName', 'shortName', 'slug'):
            text = value.get(key)
            if isinstance(text, str) and text.strip(): return text.strip()
    return ''


def parse_standings(data) -> list[dict]:
    """Accept the official JSON's nested tournament/team rows, reject ambiguous data.

    We only trust rows that explicitly contain rank, team and points, and a
    real-size unique league table. This prevents accidental standings made
    from other JSON arrays, rankings without season data, or stale guesses.
    """
    rows = []
    def walk(node, tournament=''):
        if isinstance(node, list):
            for x in node: walk(x, tournament)
        elif isinstance(node, dict):
            tour = node.get('tournament', node.get('serie', tournament))
            tour = str(tour).casefold() if tour else tournament
            n = _name(node.get('team', node.get('teamName', node.get('team_name'))))
            if not n:
                n = _name(node.get('name')) if 'ranking' in node else ''
            rank = _integer(node.get('ranking', node.get('rank', node.get('position'))))
            pts = _integer(node.get('points'))
            played = _integer(node.get('games', node.get('played')))
            if n and rank is not None and pts is not None and played is not None:
                if not tour or 'runkosarja' in tour or 'regular' in tour:
                    rows.append({'team': n, 'rank': rank, 'points': pts, 'games': played})
            for k, value in node.items():
                if isinstance(value, (dict, list)):
                    next_tour = 'runkosarja' if str(k).casefold() == 'runkosarja' else tour
                    walk(value, next_tour)
    walk(data)
    found = {}
    for row in rows:
        if row['rank'] < 1 or row['rank'] > 40 or row['points'] < 0 or row['games'] < 1:
            continue
        old = found.get(row['team'].casefold())
        if old and (old['points'],old['rank']) != (row['points'],row['rank']):
            # Ambiguous multiple tournaments/season in the payload. Refuse the table.
            return []
        found[row['team'].casefold()] = row
    result = sorted(found.values(), key=lambda r: r['rank'])
    if len(result) < 12 or len({r['rank'] for r in result}) != len(result):
        return []
    if result[0]['rank'] != 1:
        return []
    return result


@lru_cache(maxsize=3)
def _load_standings_from_api(season_end: int, time_bucket: int) -> list[dict]:
    """A 10-minute per-process cache avoids unnecessary requests."""
    req = Request(STANDINGS_API + '?season=' + str(season_end), headers={
        'Accept': 'application/json', 'User-Agent': 'KyselyTutor/1.0 (educational app)'})
    with urlopen(req, timeout=5) as response:
        if getattr(response, 'status', 200) != 200:
            return []
        raw = response.read(1_800_001)
    if len(raw) > 1_800_000: return []
    return parse_standings(json.loads(raw.decode('utf-8')))


def official_standings(season_end: int | None = None) -> list[dict]:
    """Get the league's live official data, never substitute a hardcoded table."""
    try:
        return _load_standings_from_api(season_end or current_season_end(), int(time.time() // 600))
    except (OSError, ValueError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError):
        return []


def favourite_answer(fi: bool) -> str:
    return ('Suosikkijoukkueeni on **Helsingin Jokerit**! 🏒 '
            'Tämä on vain KyselyTutorin leikkimielinen mieltymys, ei tilastoihin perustuva arvio.'
            if fi else
            'My favourite team is **Helsingin Jokerit**! 🏒 '
            'That is KyselyTutor’s playful preference, not an objective league ranking.')


def standings_answer(question: str, fi: bool, table: list[dict] | None = None,
                     season_end: int | None = None) -> str:
    end = season_end or current_season_end()
    start = end - 1
    url = standings_url(end)
    rankings = official_standings(end) if table is None else table
    if rankings:
        leader = rankings[0]
        jokerit = next((row for row in rankings if 'jokerit' in row['team'].casefold()), None)
        if fi:
            body = (f'**Liigan virallinen sarjataulukko, kausi {start}–{end} (runkosarja):**\n\n'
                    '| Sija | Joukkue | Ottelut | Pisteet |\n|---:|---|---:|---:|\n')
        else:
            body = (f'**Official Finnish Liiga standings, {start}–{end} regular season:**\n\n'
                    '| Rank | Team | Games | Points |\n|---:|---|---:|---:|\n')
        for row in rankings[:5]:
            body += f"| {row['rank']} | {row['team']} | {row['games']} | {row['points']} |\n"
        body += ('\n' + (f"Sarjaa johtaa **{leader['team']}** ({leader['points']} pistettä). "
                         if fi else
                         f"**{leader['team']}** leads with {leader['points']} points. "))
        if jokerit:
            body += (f"Jokerit on sijalla **{jokerit['rank']}** ({jokerit['points']} pistettä)."
                     if fi else
                     f"Jokerit is **{jokerit['rank']}th** with {jokerit['points']} points.")
        body += f'\n\n[{"Liigan virallinen sarjataulukko" if fi else "Official Liiga standings"}]({url})'
    else:
        body = (
            f'En saanut juuri nyt vahvistettua ajantasaista sarjataulukkoa Liigan palvelusta, '
            f'joten en väitä minkään joukkueen johtavan. Tarkista **[Liigan virallinen sarjataulukko]({url})**.'
            if fi else
            f'I could not verify the latest Liiga standings from the official service, '
            f'so I will not guess which team leads. Check the **[official Liiga standings]({url})**.'
        )
    return body + '\n\n' + favourite_answer(fi)


HOCKEY_SYSTEM = '''You are KyselyTutor, a warm and factual Finnish-English tutor
whose main focus is Kimmo Vehkalahti's statistics textbook. This conversation
is a small explicitly *non-textbook* hockey corner.
- For hockey, be knowledgeable, friendly and a tiny bit playful, never over-the-top.
- Your favourite Finnish team is Helsingin Jokerit; describe it as a playful
  preference, NOT the best-ranked team. In 2026–27 Jokerit compete in Liiga.
- Never pass off hockey claims as textbook citations or textbook knowledge.
- Answer in the language explicitly requested, otherwise use the question's language.
- Use the 2026–27 roster snapshot supplied for context, but identify it as a
  snapshot, not live data; real player clubs and stats can change.
- Do not invent current results, player transfers, injuries, stats, or standings.
  Give verifiable NHL.com and Liiga links when those details matter.
- If asked who is the best team / current table, defer to official Liiga
  standings; only data fetched directly from Liiga may be called current.
- All other non-hockey off-topic questions should still be treated as outside
  the textbook by the main system, not routed here.
- Keep succinct for short questions. Use Markdown.
'''
