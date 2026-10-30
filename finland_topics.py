"""Carefully scoped Finnish culture/science extras for KyselyTutor.

All facts here are curated background, not claims that the textbook says them.
The user-visible answer uses a *different* provenance badge from book answers.
No live internet search is performed by this module or by Claude.
"""
from __future__ import annotations
import re

STAT_NAMES = re.compile(
    r'\b(?:Seppo\s+Muston\w*|Mustos\w*|Muston\w*|Mustos\w*|Kimmo\s+Vehkal\w*|Vehkal\w*|'
    r'Lauri\s+Tarkkon\w*|Tarkkos\w*|Tarkkon\w*|Tarkkos\w*|Simo\s+Puntan\w*|Puntas\w*|Puntan\w*|Puntas\w*|'
    r'Survo(?:\s*R)?|Muste)\b', re.I)
STAT_TOPIC = re.compile(
    r'\b(?:Finnish\s+statistician\w*|Finland.s\s+statistician\w*|'
    r'statisticians?\s+(?:in|from|of)\s+Finland|'
    r'(?:history|pioneers?|people|figures?)\s+of\s+(?:Finnish\s+)?statistics|'
    r'suomalais\w*\s+tilastotieteilij\w*|tilastotieteilij\w*\s+Suom\w*|'
    r'tilastotieteen\s+(?:historia|pioneer\w*|vaikuttaj\w*)|'
    r'tilastotieteen\s+(?:tutkij\w*|professor\w*)|'
    r'Finnish\s+statistical\s+(?:research|computing)|'
    r'Suomen\s+tilastotiet\w*|tilastokeskus|statistics\s+Finland)\b', re.I)
HISTORY = re.compile(
    r'\b(?:Finnish\s+history|history\s+of\s+Finland|Finland.s\s+history|'
    r'histor(?:y|ical)\s+(?:of\s+)?(?:Helsinki|Turku|Lapland|Karelia)|'
    r'Suomen\s+historia\w*|Suomen\s+menneisy\w*|'
    r'(?:Suomen|Helsingin|Turun|Lapin|Karjalan)\s+historia\w*|'
    r'itsen[äa]isyy\w*|itsen[äa]isty\w*|independen\w*\s+(?:of|in)\s+Finland|Finland\s+become\s+independent|Finland\s+(?:became|is)\s+independent|Finland.s\s+independen\w*|'
    r'Finnish\s+independence|Winter\s+War|Continuation\s+War|'
    r'Finnish\s+Civil\s+War|(?:what\s+happened|events?)\s+in\s+(?:18(?:09)|19(?:17|18|39|40|41|44|95)|20(?:23))\s+in\s+Finland|talvisot\w*|jatkosot\w*|sis[äa]llissot\w*|'
    r'Grand\s+Duchy\s+of\s+Finland|Suomen\s+suuriruhtinaskun\w*|'
    r'Ruotsin\s+vallan\s+ai\w*|Ven[äa]j[äa]n\s+vallan\s+ai\w*|'
    r'Kalevala|Mikael\s+Agricola|Mannerheim|Svinhufvud|'
    r'Finland\s+join\w*\s+NATO|Suom\w*\s+Natoon)\b', re.I)
GEOGRAPHY = re.compile(
    r'\b(?:Finnish\s+geograph\w*|geography\s+of\s+Finland|'
    r'Suomen\s+maantiet\w*|Suomen\s+luonto|'
    r'Finland.s\s+(?:largest|highest|longest|lakes?|islands?|regions?|borders?|capital|climate)|(?:largest|biggest|highest|longest|capital)\s+(?:\w+\s+){0,3}(?:of|in)\s+Finland|'
    r'(?:where\s+is|where\s+are|where\s+in\s+Finland\s+is)\s+(?:Finland|Helsinki|Turku|Tampere|Lapland|Rovaniemi|Saimaa|Karelia|Åland|Aland)|'
    r'(?:what|where)\s+is\s+(?:Lake\s+)?(?:Saimaa|Lapland|Åland|Aland|Halti)|'
    r'(?:lakes?|islands?|rivers?|archipelago|national\s+parks?|midnight\s+sun|polar\s+night|borders?|regions?)\s+(?:in|of)\s+Finland|'
    r'(?:Suomen|Suomessa|Suomesta)\s+(?:j[äa]rv\w*|saarist\w*|raj\w*|alue\w*|kaupunk\w*|ilmast\w*|korkein\w*|pisin\w*)|'
    r'(?:Saimaa|P[äa]ij[äa]nne|Inarij[äa]rvi|Ahvenanmaa|Lappi|Halti|Saaristomeri|Saaristo\w*|Kemijoki|Per[äa]meri)\b|(?:tell\s+me\s+about|kerro(?:\s+minulle)?|describe)\s+(?:Helsinki|Turku|Tampere|Rovaniemi|Lapland|Oulu|Karelia|Suomi|Finland|Ahvenanmaa)\b)', re.I)
CITY_WORD = re.compile(r'\b(?:Helsinki|Helsingin|Turku|Turun|Tampere|Tampereen|Espoo|Espoon|Vantaa|Vantaan|Oulu|Oulun|Jyväskylä|Joensuu|Kuopio|Rovaniemi|Rovaniemen|Vaasa|Porvoo)\b', re.I)
CITY_HISTORY_SIGNAL = re.compile(r'\b(?:history|historical|historically|founded|founding|become|became|past|capital|historia\w*|historialli\w*|perustett\w*|pääkaupung\w*)\b', re.I)
CITY_GEO_SIGNAL = re.compile(r'\b(?:where|located|location|population|climate|nearby|near|map|missä|sijaitse\w*|asukasluku|väkiluku|maantiet\w*|ilmasto)\b', re.I)
FINLAND_WORD = re.compile(r'\b(?:Finland|Finnish|Suomi|Suomen|Suomessa|Suomesta|suomalais\w*)\b', re.I)
HISTORY_SIGNAL = re.compile(r'\b(?:history|historical|founded|founding|war|independence|independent|centur\w*|historia\w*|sota|sodan|sodat|vuosi\w*|perustett\w*|menneisyys)\b', re.I)
GEOGRAPHY_SIGNAL = re.compile(r'\b(?:geograph\w*|where|located|distance|climate|city|cities|capital|border\w*|lake\w*|river\w*|forest\w*|mountain\w*|island\w*|region\w*|coast\w*|map|maantiet\w*|missä|sijaitse\w*|pääkaupunki|kaupunki\w*|j[äa]rv\w*|jok\w*|saar\w*|ilmast\w*|raja\w*|pinta-ala)\b', re.I)
BOOK_ANCHOR = re.compile(
    r'\b(?:textbook|book\s+(?:says|mentions|describes)|in\s+(?:the\s+)?book|'
    r'(?:page|chapter)\s+\d+|what\s+does\s+the\s+book\s+(?:say|mention|discuss)|according\s+to\s+the\s+book|kirjassa|kirjan\s+mukaan|kirja\s+(?:sanoo|mainitsee)|'
    r'(?:sivu|luku)\s+\d+|oppikirjassa|teoksessa)\b', re.I)


def finland_topic(question: str) -> str | None:
    """Return only a clearly signalled outside-textbook Finland topic.

    Do not redirect questions explicitly asking what the original book says:
    those go to the PDF-grounded tutor with its green source labels.
    Hockey is checked *before* this classifier by the application.
    """
    q = ' '.join(str(question).split())
    if BOOK_ANCHOR.search(q):
        return None
    if STAT_NAMES.search(q) or STAT_TOPIC.search(q):
        return 'statisticians'
    if HISTORY.search(q):
        return 'history'
    if GEOGRAPHY.search(q):
        return 'geography'
    if CITY_WORD.search(q) and CITY_HISTORY_SIGNAL.search(q):
        return 'history'
    if CITY_WORD.search(q) and CITY_GEO_SIGNAL.search(q):
        return 'geography'
    if FINLAND_WORD.search(q) and HISTORY_SIGNAL.search(q):
        return 'history'
    if FINLAND_WORD.search(q) and GEOGRAPHY_SIGNAL.search(q):
        return 'geography'
    return None


FOLLOWUP_SIGNAL = re.compile(
    r'\b(?:he|him|his|she|her|they|their|there|that|those|this|these|it|its|'
    r'h[äa]n|h[äa]nen|siit[äa]|sen|t[äa]m[äa]|n[äa]m[äa]|niist[äa]|se)\b', re.I)

def finland_followup(question: str, previous_question: str) -> str | None:
    """Keep short pronoun-based follow-ups in an established Finland topic.

    Never infer topic merely because a previous question mentioned Finland;
    new standalone questions still use the normal textbook routing.
    """
    if len(question) > 180 or finland_topic(question) or BOOK_ANCHOR.search(question):
        return None
    if not FOLLOWUP_SIGNAL.search(question):
        return None
    return finland_topic(previous_question)


# Carefully verified fixed historical/background notes. Source URLs are given
# verbatim so readers can trace them. These are NOT dynamically retrieved.
FINLAND_REFERENCE = {
    'statisticians': '''
Kimmo Vehkalahti, the author of Kyselytutkimuksen mittarit ja menetelmät, is a
University of Helsinki social statistician specialising in measurement,
multivariate methods, statistical computing, and social data science.
Source: https://socialdatascience.helsinki.fi/faculty/kimmo-vehkalahti/

PRIORITISE SEPPO MUSTONEN in questions about Vehkalahti's mentors or influences:
- Professor Seppo Mustonen developed the Survo statistical-computing environment,
  with its earliest version in 1966; he also emphasised inventive, interactive
  computing and statistics teaching.
  University of Helsinki profile: https://www.helsinki.fi/fi/uutiset/matematiikka-ja-luonnontieteet/ollin-elinan-ja-survon-isa-tilastotieteilija-seppo-mustonen-kehitti-survo-tietokoneohjelman
- Vehkalahti HIMSELF writes that Mustonen substantially shaped the direction of
  his work in statistics: https://www.mv.helsinki.fi/home/kvehkala/maisteri.html
- Mustonen supervised Vehkalahti's doctoral dissertation, *Reliability of
  Measurement Scales* (2000): https://www.mv.helsinki.fi/home/kvehkala/publications.html
- Mustonen and Vehkalahti jointly authored the 1997 work *Survo as an
  environment for statistical research and teaching*:
  https://www.survo.fi/papers/ISI97.html
- On textbook page 9 Vehkalahti thanks Mustonen for valuable comments
  and for fulfilling several Survo-related wishes:
  [Book acknowledgements, p. 9](/reader?page=9).

LAURI TARKKONEN:
- His measurement-methods course influenced Vehkalahti's study of reliability.
  Vehkalahti explicitly credits the course in his personal account:
  https://www.mv.helsinki.fi/home/kvehkala/maisteri.html
- In the textbook's acknowledgements, Vehkalahti credits Tarkkonen with
  inspiring him to think about dimensions of the measurement framework:
  [Book acknowledgements, p. 9](/reader?page=9).
- Tarkkonen developed the framework discussed in chapter 5 of the book;
  do not imply every idea was solely his.

SIMO PUNTANEN:
- In the book's acknowledgements Vehkalahti thanks him for help with
  preparing and finishing publications: [Book acknowledgements, p. 9](/reader?page=9).
- Puntanen was one of Vehkalahti's doctoral opponents and collaborated with
  Vehkalahti and Tarkkonen on measurement-error research:
  https://www.mv.helsinki.fi/home/kvehkala/publications.html

Kimmo's text acknowledges many other people; do not claim that the three above
are an exhaustive list or rank personal relationships beyond the source evidence.
''',
    'history': '''
Reliable high-level history of Finland:
- Finland formed part of the Swedish realm before 1809, became an autonomous
  Grand Duchy in the Russian Empire in 1809, and gained independence in 1917.
- Parliament adopted the declaration of independence on 6 December 1917.
- The Finnish Civil War occurred in 1918; Finland became a republic in 1919.
- Finland fought the Winter War against the Soviet Union in 1939–1940, and
  the Continuation War in 1941–1944. Avoid simplistic or one-sided summaries.
- Finland joined the European Union in 1995 and NATO on 4 April 2023.
- For the history of statistical institutions in Finland: early Finnish
  population records in 1749; Finland's Statistical Office established in 1865.
Sources:
https://finland.fi/life-society/main-outlines-of-finnish-history/
https://stat.fi/en/about-us/get-to-know-statistics-finland/history-of-statistics-in-finland
https://www.nato.int/en/news-and-events/articles/news/2023/04/04/finland-joins-nato-as-31st-ally
These are background sources, not live current-event feeds.
''',
    'geography': '''
Reliable high-level Finnish geography:
- Finland is in northern Europe, with land borders with Sweden, Norway, and
  Russia; its coast lies along the Baltic Sea.
- Capital: Helsinki. Finnish and Swedish are national languages.
- Lake Saimaa in eastern Finland is the country's largest lake system.
- Other notable lakes: Päijänne and Inari. Finland has very many lakes,
  and the archipelago and Åland are prominent geographic features.
- Lapland is the northernmost region; long winter nights and summer
  midnight sun are important parts of life above the Arctic Circle.
- Highest point: Halti (1324 m); do not confuse the summit of Halti in
  Norway with Finland's highest point on the fell.
Sources:
https://finland.fi/facts-stats-and-info/finland-in-facts/
https://finland.fi/life-society/tapping-into-finnish-lakes/
https://toolbox.finland.fi/wp-content/uploads/sites/2/2021/07/finland-in-figures-2021.pdf
https://toolbox.finland.fi/life-society/finfo-facts-about-finland-2/attachment/finfo_facts_2025_en_aukeama_toolbox-2/
Do not invent real-time local travel conditions, opening times, or statistics.
''',
}

PERSONALITY_SYSTEM = '''You are KyselyTutor, Kimmo Vehkalahti's Finnish-English
statistics textbook companion, with a SMALL, helpful Finnish-culture side.
This turn was explicitly classified as a Finland-related side topic. Its facts
are NOT proof that the textbook contains them.

Personality: informed, pleasant, gently witty only when it fits, respectful of
Finnish culture, slightly enthusiastic about Finnish statistical computing.
Know about Seppo Mustonen especially: recognise his central place in Survo,
statistical computing, and in Vehkalahti's own scholarly development. Avoid
fictional personal anecdotes or ungrounded statements about how someone feels.
The small hockey side has Jokerit as its playful favourite, but NEVER insert
Jokerit jokes into an unrelated statistics/history/geography answer.

The supplied reference notes are VERIFIED BACKGROUND MATERIAL assembled from
public sources; they are not book excerpts. Answer using these facts where
relevant, naturally cite the source URLs (as clickable Markdown links),
and if discussing the book's acknowledgements link the relevant /reader page.
For information beyond this reference set, label it as unverified general
knowledge or acknowledge uncertainty rather than inventing specifics.
Do not fabricate quotations, source URLs, affiliations, relationships,
statistics, or current events. No live internet has been queried by you.
If asked for live/current information, tell the user that the reference notes
are not a live feed and direct them to reliable up-to-date sources.

Answer in the language specifically requested, or else the user's question
language. Keep short queries concise, and do not output JSON or [Pnn] citations.
History and geography questions are within the tutor's OPTIONAL Finland context,
not unrelated questions; still distinguish them from the original textbook.
'''
