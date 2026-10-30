# KyselyTutor

**Bilingual Finnish–English AI study companion for** *Kyselytutkimuksen mittarit ja menetelmät* **by Kimmo Vehkalahti**.

KyselyTutor is an independent Flask application powered by Anthropic Claude. It searches the original Finnish textbook, answers questions in Finnish or English, translates book passages, and opens citations in a custom cross-browser book reader. It also offers read-aloud controls and a small, clearly labelled Finnish-culture personality.

> **Textbook attribution:** © Kimmo Vehkalahti. The University of Helsinki published the open-access PDF in 2019; its content corresponds to the 2014 Finn Lectura printed edition. PDF ISBN 978-951-51-4981-7. [DOI: 10.31885/9789515149817](https://doi.org/10.31885/9789515149817). **The original textbook is licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)** and is included at `data/book.pdf`. Preserve its attribution and licence notice.
>
> **Independence:** KyselyTutor, its AI-generated explanations and translations, and its University of Helsinki–inspired colour scheme are **not affiliated with, authored, approved, or endorsed by** Kimmo Vehkalahti, the University of Helsinki, Finn Lectura, Jokerit, Liiga, or the NHL. The original textbook is not an official English translation.

## Features at a glance

- **Book-based help:** Finnish and English questions, local textbook retrieval, page citations, explanations of tables/figures when a page image is supplied to Claude, and unofficial Finnish-to-English translation.
- **Clear evidence labels:** green for **From the textbook**, orange for **Related — outside the textbook**, and red for genuinely unrelated questions. Mixed answers separate supported passages from supplementary AI knowledge.
- **Custom textbook reader:** opens at `/reader` rather than relying on a browser PDF plug-in; offers page links, search, contents, zoom, page text and a separate PDF download.
- **Supporting-text highlights:** translucent orange marks relevant original Finnish passages for cited answers. The reader can **Show/Hide highlights**; highlighting is relevant-context matching, not guaranteed sentence-level quotation alignment.
- **Read aloud:** selected answer or extracted book text, whole reader page, or highlighted evidence; automatic Finnish/English detection with playback controls. **Flo (fi-FI)** is preferred for Finnish *when offered by the browser*; English uses an English voice.
- **Accessible layout:** university-inspired black/white/blue palette, light/dark toggle, collapsible table of contents, larger fonts, and mobile layout.
- **Rotating questions:** four prompts displayed in a horizontal row (two Finnish, two English) chosen from a bank of 24; selection avoids the previous set.
- **Optional personality:** Finnish statisticians (especially Seppo Mustonen), Finnish history, geography, and hockey. The tutor's playful favourite is **Helsingin Jokerit**, but official Liiga standings take precedence for ranking questions.

**The textbook remains the primary purpose of this project.** Biography, history, geography, and hockey replies have separate non-book labels; they are not represented as textbook quotations.

For detailed feature behaviour, architecture, limitations, maintenance, and troubleshooting, see **[docs/OPERATIONS_AND_FEATURES.md](docs/OPERATIONS_AND_FEATURES.md)**.

## 1. Quick start: run locally (macOS)

Install Python 3.12 or another version compatible with `requirements.txt`. From Terminal, enter the extracted project root—the directory containing `app.py` and `requirements.txt`:

```bash
cd ~/Downloads/kysely_book_agent
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
open -e .env
```

Edit `.env` to provide your own Anthropic API key and, if desired, a shared access password:

```dotenv
ANTHROPIC_API_KEY=your-real-anthropic-api-key
ANTHROPIC_MODEL=claude-sonnet-5-5
ANTHROPIC_SEARCH_MODEL=claude-haiku-5-5
APP_PASSWORD=choose-a-password
FLASK_SECRET_KEY=choose-a-long-random-value
```

The model IDs are application defaults; your Anthropic account must have access to the configured models. API usage is billed separately from a Claude chat subscription. Keep `.env` out of Git.

Start the server:

```bash
python app.py
```

Open the following local addresses:

| Address | Purpose |
|---|---|
| `http://127.0.0.1:5000/` | Chat interface |
| `http://127.0.0.1:5000/reader?page=41` | Original book, page 41 |
| `http://127.0.0.1:5000/book/download` | Download the original PDF |
| `http://127.0.0.1:5000/health` | Basic service and index diagnostics |

To stop the server, press **Control+C**. On subsequent local runs, `source .venv/bin/activate` and `python app.py` are sufficient. The `flask` shell command is **not** needed.

## 2. Deploy with GitHub and Render

1. Create an empty GitHub repository (for example, `kysely-book-agent`) and commit the **contents** of the `kysely_book_agent` project directory. Keep `data/book.pdf`; do **not** commit `.env`, `.venv`, API keys, or passwords.
2. In [Render](https://dashboard.render.com/), choose **New → Blueprint**, connect the repository, and use the included `render.yaml`. The Blueprint requests a Python web service named `kysely-book-agent`; its exact public URL depends on Render.
3. Set `ANTHROPIC_API_KEY` and preferably `APP_PASSWORD` in Render's **Environment** settings. The Blueprint configures the model names and generates `FLASK_SECRET_KEY`.
4. Deploy; then visit `/`, `/health`, and `/reader?page=41` on the assigned Render URL. Check **Render → Logs** if startup or a Claude request fails.

For a manually created Render Web Service, use:

```text
Build command: pip install -r requirements.txt
Start command: gunicorn app:app --workers 2 --timeout 120 --bind 0.0.0.0:$PORT
```

**Important security/cost note:** A blank `APP_PASSWORD` permits anyone who can reach the URL to make billable Claude chat requests. The shared password is simple access gating, **not** full authentication, rate limiting, or institutional single sign-on. The original open-licensed book and reader are publicly accessible independently of chat protection. For substantial public usage, add rate limits, monitoring and stronger authentication.

### Subsequent code or documentation updates

From the existing cloned project, after replacing the relevant files:

```bash
git add README.md docs/OPERATIONS_AND_FEATURES.md
git commit -m "Consolidate KyselyTutor documentation"
git push origin main
```

Those commands update **documentation only**. To deploy changed application files instead, stage the files you actually changed; `git status` helps review them. Do not reapply old feature-update ZIPs to a newer version: they contain overlapping files and can undo later improvements. Auto-deploy, if enabled, normally rebuilds the service on a push.

## 3. Using KyselyTutor

**Reply language** defaults to **Automatic / Automaattinen** and stays there until the visitor explicitly changes it. Selecting an example question or translation task **does not alter** the reply-language dropdown. English and Finnish can be selected manually.

- **Ask about the book:** e.g. `Miten validiteetti ja reliabiliteetti eroavat toisistaan?` or `What does the book say about factor analysis?`. Click a source page link to open the cited page in the HTML reader.
- **Translate:** choose a translation task and request a specified page or passage. The answer is generated by Claude, not by the author of the book.
- **Read evidence:** citation links can contain identifiers such as `/reader?page=41&b=s0&b=s3`; these point to relevant Finnish paragraphs. Toggle orange marks on/off in the reader. Old `?h=` links remain supported.
- **Listen:** select text in an answer and use **Read selection**. In the reader, choose **Show page text** to select extractable text, **Read aloud** for the current page, or **Read highlighted text** for citation evidence.
- **Explore optional topics:** ask about Mustonen, Survo, Finnish history or geography, or the NHL/Jokerit. Such answers are labelled as supplementary knowledge, not textbook content.

## 4. Answer labels

| Colour | Label / meaning |
|---|---|
| Green | **From the textbook / Kirjasta:** supported by retrieved passages and cited pages. |
| Orange | **Related — outside the textbook:** relevant statistics/survey material not established by retrieved excerpts. |
| Purple | **Finnish statisticians:** external background, particularly Mustonen, Tarkkonen, Puntanen and Vehkalahti. |
| Blue | **Finnish history:** outside-book background. |
| Teal | **Finnish geography:** outside-book background. |
| Slate blue | **Hockey corner:** Jokerit, Liiga and Finnish NHL players; outside the book. |
| Red | **Not relevant to this textbook:** unrelated questions that do not fall within a supported personality category. |

A mixed academic answer may show a **green** section and a separate **orange** section. Topic colours help identify origin and scope; they are not a guarantee of factual accuracy.

## 5. Tests

After installing Python requirements and activating the virtual environment:

```bash
python -m unittest discover -s tests -v
```

If Node.js is installed, you may also run the Flo voice preference test:

```bash
node tests/test_default_flo_voice.cjs
```

Integration tests exercise reader routes, source links, retrieved passages, highlighting, and optional topic handling. They do **not** prove natural voice quality in each browser or verify live Claude responses. To test the full experience, make a real API request and inspect the cited PDF passages manually.

**Reminder:** Reader source URLs may contain an extra `&b=s0` (or multiple `b=` values) for evidence highlighting. Tests should validate the **`page` query parameter**, not require the URL to equal `/reader?page=41` exactly. The current package's `tests/test_reader.py` already accounts for this.

## 6. Project map

| File or directory | Role |
|---|---|
| `app.py` | Flask routes, Claude requests, validation and topic routing |
| `book_search.py` | Local PDF index, page-aware retrieval and bilingual search assistance |
| `evidence_passages.py` | Original-Finnish supporting-passage identification and selection |
| `finland_topics.py` | Finnish statisticians, history and geography reference notes/routing |
| `hockey.py` | Jokerit preference, Finnish NHL reference snapshot and Liiga standings lookup |
| `data/book.pdf` | Original CC BY 4.0 Finnish textbook |
| `templates/` | Main chat and custom reader HTML |
| `static/` | UI styles/scripts, PDF reader and browser read-aloud controls |
| `tests/` | Offline/backend tests plus optional JavaScript test |
| `.env.example` | Local secrets/configuration example |
| `render.yaml` | Render Blueprint settings |
| `docs/OPERATIONS_AND_FEATURES.md` | Feature, API, maintenance, privacy, and troubleshooting reference |

## 7. Important limitations

- Book-based replies depend on the **retrieved** passages, which may be incomplete; check the original source if a detail matters. An inability to retrieve a passage is not proof that the book lacks it.
- Orange highlights identify **relevant passages**, including those supporting paraphrases and translations. They need not coincide word-for-word with the answer and can miss some relevant text, particularly figures without extractable text.
- The reader renders the PDF as PNG pages; selecting text requires the separate **Show page text** view. Raw `/book/original.pdf` may still be handled as a download by some browsers; use `/reader` for consistent viewing.
- Voice quality and availability depend on OS/browser voices. **Flo** cannot be installed or guaranteed by the app; multilingual synthesis may vary by device.
- History/geography/statistician answers use preloaded contextual notes with Claude, **not** live browsing. Hockey has a specific attempt to fetch **official Liiga standings**, but the standings endpoint can be unavailable; no ranking should be fabricated.
- Information sent to Claude can include the user's question, recent chat context, retrieved book excerpts and sometimes a page image. Review Anthropic's API privacy terms and your own usage policy before publicly deploying.

For more detail, read **[docs/OPERATIONS_AND_FEATURES.md](docs/OPERATIONS_AND_FEATURES.md)**.
