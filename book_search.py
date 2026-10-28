"""Local, page-aware Finnish textbook indexing (no database or embeddings required).

All page numbers here are 1-based PDF viewer numbers; for this particular
edition they also equal the printed book pages in the main text.
"""
from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from pathlib import Path

import fitz

# Section starts are transcribed from the ORIGINAL TABLE OF CONTENTS, pp. 3-5.
SECTIONS = [
    (7, 'Alkusanat / Preface'),
    (11, '1 Johdanto / Introduction'),
    (11, '1.1 Kyselytutkimus / Survey research'),
    (14, '1.2 Kirjan rakenne ja sisältö / Book structure'),
    (17, '2 Mittaus ja tiedonkeruu / Measurement and data collection'),
    (20, '2.2 Kyselylomake mittausvälineenä / Questionnaire as instrument'),
    (23, '2.2.2 Osiot ja mittarit / Items and instruments'),
    (24, '2.2.3 Avoimet ja suljetut osiot / Open and closed items'),
    (27, '2.3 Mittauksen taso / Levels of measurement'),
    (40, '2.4 Mittauksen luotettavuus / Measurement quality'),
    (41, '2.4.1 Validiteetti ja 2.4.2 Reliabiliteetti'),
    (42, '2.5 Tiedonkeruu / Data collection'),
    (43, '2.5.1 Perusjoukko ja otos / Population and sample'),
    (47, '2.6 Kyselylomake tiedonkeruuvälineenä'),
    (51, '3 Aineiston esikäsittely / Data preparation'),
    (52, '3.2 Yhden muuttujan tarkastelu / Univariate analysis'),
    (64, '3.3 Muunnokset / Transformations'),
    (67, '3.4 Kahden muuttujan tarkastelu / Bivariate analysis'),
    (81, '3.5 Muokkaukset / Data editing'),
    (87, '4 Aineiston tiivistäminen / Data summarisation'),
    (91, '4.2 Mittausmalli / Measurement model'),
    (93, '4.3 Faktorianalyysi / Factor analysis'),
    (100, '4.3.3 Mittausmallin rakennevaliditeetti'),
    (106, '4.4 Mitta-asteikko / Measurement scale'),
    (109, '4.4.1 Faktoripisteet / Factor scores'),
    (112, '4.4.2 Summamuuttujat / Composite scores'),
    (116, '4.4.3 Mitta-asteikon reliabiliteetti'),
    (121, '5 Havaintojen vertailu / Comparing observations'),
    (124, '5.2 Regressioanalyysi / Regression analysis'),
    (128, '5.2.2 Selittäjien valinta / Predictor selection'),
    (131, '5.2.3 Taustamuuttujat ja ennustevaliditeetti'),
    (134, '5.2.4 Luokitellut selittäjät / Categorical predictors'),
    (141, '5.3 Regressiodiagnostiikka / Regression diagnostics'),
    (151, '6 Aineiston ryhmittely / Clustering'),
    (159, '6.2 Moniulotteinen skaalaus / Multidimensional scaling'),
    (166, '6.3 Medoidiryhmittely / Medoid clustering'),
    (171, '7 Ryhmien visualisointi / Visualising groups'),
    (175, '7.2 Erotteluanalyysi / Discriminant analysis'),
    (183, '7.3 Korrespondenssianalyysi / Correspondence analysis'),
    (189, '7.3.3 Burtin matriisi'),
    (195, 'A Ohjelmistot ja dokumentointi / Software & documentation'),
    (196, 'A.1.1 Survo ja SPSS'),
    (202, 'A.1.3 Dokumentoiva työskentelytapa'),
    (211, 'Lähteet ja kirjallisuus / References'),
    (215, 'Kuvat, esimerkit, tulosteet ja taulukot'),
    (219, 'Hakemisto / Index'),
]

CHAPTERS = [
    {'number': '1', 'fi': 'Johdanto', 'en': 'Introduction', 'page': 11},
    {'number': '2', 'fi': 'Mittaus ja tiedonkeruu', 'en': 'Measurement and data collection', 'page': 17},
    {'number': '3', 'fi': 'Aineiston esikäsittely', 'en': 'Data preparation', 'page': 51},
    {'number': '4', 'fi': 'Aineiston tiivistäminen', 'en': 'Data summarisation', 'page': 87},
    {'number': '5', 'fi': 'Havaintojen vertailu', 'en': 'Comparing observations', 'page': 121},
    {'number': '6', 'fi': 'Aineiston ryhmittely', 'en': 'Clustering', 'page': 151},
    {'number': '7', 'fi': 'Ryhmien visualisointi', 'en': 'Visualising groups', 'page': 171},
    {'number': 'A', 'fi': 'Ohjelmistot ja dokumentointi', 'en': 'Software and documentation', 'page': 195},
]

# Useful English-to-Finnish FALLBACKS if the query-expansion Claude call fails.
GLOSSARY = {
    'questionnaire': 'kyselylomake osio mittari',
    'survey research': 'kyselytutkimus', 'survey': 'kyselytutkimus',
    'sampling': 'otanta otos', 'population': 'perusjoukko',
    'sample': 'otos', 'nonresponse': 'kato vastauskato',
    'response rate': 'vastausprosentti',
    'reliability': 'reliabiliteetti luotettavuus',
    'validity': 'validiteetti', 'measurement': 'mittaus mittari',
    'measurement scale': 'mitta-asteikko', 'likert': 'likert',
    'factor analysis': 'faktorianalyysi', 'factor score': 'faktoripisteet',
    'cronbach': 'cronbach alfa', 'alpha': 'alfa',
    'composite score': 'summamuuttujat',
    'regression': 'regressioanalyysi', 'residual': 'jäännös',
    'diagnostics': 'regressiodiagnostiikka',
    'clustering': 'ryhmittely medoidiryhmittely',
    'medoid': 'medoidiryhmittely',
    'correspondence analysis': 'korrespondenssianalyysi',
    'discriminant analysis': 'erotteluanalyysi',
    'multidimensional scaling': 'moniulotteinen skaalaus',
    'standard deviation': 'keskihajonta', 'mean': 'keskiarvo',
    'median': 'mediaani', 'correlation': 'korrelaatio',
    'missing values': 'puuttuva tieto puuttuvat tiedot',
    'confidence interval': 'luottamusväli',
    'categorical': 'luokiteltu luokittelu', 'ordinal': 'järjestysasteikko',
    'survo': 'survo', 'spss': 'spss',
    'data cleaning': 'aineiston esikäsittely muokkaukset',
    'bar chart': 'pylväskuva', 'scatter plot': 'hajontakuva',
    'translation': 'käännös',
}

WORD_RE = re.compile(r"[^\W_]+(?:[-’'][^\W_]+)*", re.UNICODE)
STOPWORDS = set('a an and are as at be by can do for from how i in is it me of on or please the this to what when where which why with you your explain compare about book chapter translate page pages tell chapter what does say give minulle kuinka miten mikä mitä miksi missä missä on oli ovat että ja sekä se sen kirja kirjassa kirjasta kerro selitä sivu sivulla sivulta'.split())


def normalise(s: str) -> str:
    s = s.replace('\u00ad\n', '').replace('\u00ad', '')
    s = re.sub(r'(?<=\w)-\s*\n(?=\w)', '', s)  # Finnish line hyphenation
    s = re.sub(r'[ \t]+', ' ', s)
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s.strip()


def tokens(s: str) -> list[str]:
    words = [w for w in WORD_RE.findall(s.casefold()) if len(w) > 1 and w not in STOPWORDS]
    # Six-character prefixes are helpful for the highly inflected Finnish vocabulary.
    return words + ['stem:' + w[:6] for w in words if len(w) >= 7]


def glossary_expand(q: str) -> str:
    q = q.casefold()
    return ' '.join(v for k, v in GLOSSARY.items() if k in q)


def section_at(page: int) -> str:
    out = 'Front matter / Alkulehdet'
    for start, name in SECTIONS:
        if start <= page:
            out = name
        else:
            break
    return out


def explicit_pages(question: str, count: int) -> list[int]:
    """Printed-page and PDF-page numbers match. Supports 'p. 49' and 's. 49'."""
    pattern = re.compile(r'\b(?:pdf\s*)?(?:pages?|pp\.?|p\.|sivut?|sivuilla|sivulla|sivulta|s\.)\s*#?\s*(\d{1,3})(?:\s*[-–—]\s*(\d{1,3}))?', re.I)
    found = []
    for match in pattern.finditer(question):
        start = int(match.group(1))
        end = int(match.group(2) or start)
        if end < start or end - start > 1:  # stay within 2 pages per request
            continue
        for p in range(start, end + 1):
            if 1 <= p <= count and p not in found:
                found.append(p)
    return found[:2]


class BookIndex:
    def __init__(self, path: Path):
        self.path = Path(path)
        with fitz.open(str(path)) as document:
            self.page_count = len(document)
            self.pages = {i + 1: normalise(page.get_text(sort=True)) for i, page in enumerate(document)}
        self.chunks: list[dict] = []
        for page, content in self.pages.items():
            if page > 218 or not content:  # skip the alphabetical index; named pages stay accessible
                continue
            if page in (3, 4, 5, 6):  # TOC can bias search; chapters are indexed below
                continue
            start = 0
            while start < len(content):
                stop = min(start + 1550, len(content))
                if stop < len(content):
                    split = content.rfind('\n', start + 900, stop)
                    if split > start:
                        stop = split
                excerpt = content[start:stop].strip()
                if excerpt:
                    self.chunks.append({'page': page, 'section': section_at(page), 'text': excerpt})
                if stop >= len(content):
                    break
                start = max(stop - 180, start + 1)
        self.documents = [Counter(tokens(c['section'] + '\n' + c['text'])) for c in self.chunks]
        self.lengths = [sum(counter.values()) for counter in self.documents]
        self.average_length = sum(self.lengths) / max(len(self.lengths), 1)
        self.postings: dict[str, list[int]] = defaultdict(list)
        for i, bag in enumerate(self.documents):
            for word in bag:
                self.postings[word].append(i)

    def get_pages(self, page_numbers: list[int], max_chars: int = 6200) -> list[dict]:
        return [{'page': p, 'section': section_at(p), 'text': self.pages[p][:max_chars]}
                for p in page_numbers if self.pages.get(p)]

    def search(self, question: str, expansion: str = '', top_k: int = 9) -> list[dict]:
        query = set(tokens(question + ' ' + expansion + ' ' + glossary_expand(question)))
        if not query:
            return []
        scores: dict[int, float] = defaultdict(float)
        n = len(self.chunks)
        k1, b = 1.5, 0.75
        for w in query:
            candidates = self.postings.get(w, [])
            if not candidates:
                continue
            idf = math.log(1 + (n - len(candidates) + 0.5) / (len(candidates) + 0.5))
            for i in candidates:
                freq = self.documents[i][w]
                numerator = freq * (k1 + 1)
                denominator = freq + k1 * (1 - b + b * self.lengths[i] / self.average_length)
                scores[i] += idf * numerator / denominator
        ranked = sorted(scores, key=scores.get, reverse=True)
        results, seen = [], Counter()
        for i in ranked:
            if scores[i] <= 0:
                break
            chunk = self.chunks[i]
            if seen[chunk['page']] >= 2:
                continue
            results.append(chunk)
            seen[chunk['page']] += 1
            if len(results) >= top_k:
                break
        return results
