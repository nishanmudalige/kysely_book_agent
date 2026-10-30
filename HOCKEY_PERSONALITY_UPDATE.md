# Hockey corner / Jääkiekkonurkka

This update adds a small, optional hockey personality without affecting the textbook tutor.

- Favourite Finnish hockey team: **Helsingin Jokerit**. This is a *playful preference*, not a claim about league quality.
- If asked which team is best or for Finnish league standings, KyselyTutor fetches the **official Liiga standings** from `https://liiga.fi/api/v2/standings/?season=2027` (the current season end year is computed automatically). It shows the top five, the leader and Jokerit's ranking when available, then mentions its favourite. A short per-process cache lasts up to ten minutes.
- If the official endpoint fails or its data cannot be verified, the tutor **does not guess** a ranking. It provides a link to the official standings instead.
- Questions about Finnish NHL players use Claude with a documented **October 2026 roster snapshot** and a link to the official NHL player directory. The agent cautions that teams, statistics and injuries can change. The live league standings are not used to make NHL claims.
- Hockey is **outside the textbook** and gets a dedicated orange label: Hockey corner / Jääkiekko. The green original-book labels and red unrelated-question warning remain unchanged.
- Replies use Finnish or English as requested, or detect the question language. The language dropdown remains under user control.

## Update existing GitHub / Render installation

Copy these into the existing project directory:

- `hockey.py` (new)
- `app.py` (modified)
- `static/app.js` (modified)
- `tests/test_hockey.py` (new)

Then run:

```bash
git add app.py hockey.py static/app.js tests/test_hockey.py
git commit -m "Add Jokerit hockey personality and official Liiga standings"
git push origin main
```

Run offline checks:

```bash
python -m unittest discover -s tests -v
```

No new Python dependencies, API credentials, or environment variables are required. General player questions continue to use your Claude API key. Official standings require outbound internet access on Render.

## Sources

- Liiga confirms Jokerit's 2026–27 top-tier licence: https://liiga.fi/fi/uutiset/jaakiekon-sm-liiga-oy-tiedottaa-jokerit-helsinki-oy-lle-on-myonnetty-liiga-lisenssi-kaudelle-2026-27
- Official standings: https://liiga.fi/fi/tilastot/joukkuetilastot/kausi?tilasto=sarjataulukko
- Liiga JSON endpoint documentation (fastRhockey): https://fastrhockey.sportsdataverse.org/reference/liiga_standings.html
- NHL players: https://www.nhl.com/players
- October 2026 Finnish NHL players snapshot: https://suomalaisetnhlssa.fi/pelaajat/

This is an independent tutor and is not affiliated with Jokerit, Liiga, NHL, the author of the textbook or the University of Helsinki.
