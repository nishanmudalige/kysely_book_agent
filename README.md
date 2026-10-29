# KyselyTutor — bilingual Claude tutor for Kimmo Vehkalahti's textbook

**Textbook:** Kimmo Vehkalahti, *Kyselytutkimuksen mittarit ja menetelmät*. The PDF was published by the **University of Helsinki in 2019** and reproduces the **2014 Finn Lectura** printed edition.

**Author and copyright:** © **Kimmo Vehkalahti**. **Original book licence:** [Creative Commons Attribution 4.0 (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). [DOI: 10.31885/9789515149817](https://doi.org/10.31885/9789515149817). The original PDF is included in `data/book.pdf` under that licence. Keep the author's name, book title, publication details and licence notice intact when distributing this project.

> **Independent AI assistant:** KyselyTutor and any AI-generated translations or explanations are not produced, approved or endorsed by Kimmo Vehkalahti, Finn Lectura or the University of Helsinki.

KyselyTutor uses **Claude Sonnet 5.5** with structured JSON output to answer and translate, and optionally **Claude Haiku 5.5** to generate Finnish search keywords from English questions. It is deliberately modeled on the earlier `tilasto_book_agent_claude.zip` project: Flask, a Render deployment option, local searchable PDF text, clickable book citations, and a bilingual interface.

## What the agent does

- Understands **Finnish or English** questions, with **automatic, Finnish or English** answer-language selection.
- Answers *using the original book*, giving clickable **PDF page references** when supported by retrieved passages.
- Translates passages and requested pages of the Finnish book into **English**, preserving numerical and statistical meaning. These are unofficial, AI-generated translations.
- Accepts questions about *related* topics not substantiated by the textbook. They are explicitly labelled **“Related — outside the book / Aiheeseen liittyvä — ei kirjasta”** and identified as general AI knowledge, **not live web research**.
- Labels irrelevant questions **“Outside the scope of this book / Kirjan aihepiirin ulkopuolella”** and explains the boundary instead of pretending the book covers them.
- Separates book-supported and general-knowledge content into different sections when a response uses both.
- Includes a prominent link **“Open the textbook PDF / Avaa PDF”** and a chapter navigator.
- Can render PDF page images to Claude for questions explicitly about figures/tables (API vision usage may cost more).
- Optionally uses an `APP_PASSWORD` to protect billable Claude chat requests. The open-licensed PDF is publicly accessible even when the chat is password protected.

**Important page-number difference from the previous agent:** In this edition, the printed main-text page number **equals** the PDF viewer page number. A citation to p. 41 links to `/reader?page=41` (the cross-browser reader), **not** page 43.

**Retrieval details:** The backend extracts and indexes text with PyMuPDF and a lightweight local BM25 implementation (no vector database, external index or separate OpenAI key). An English question is translated to Finnish search terms using Claude Haiku, with an offline glossary fallback. In the absence of a supported match the agent should avoid making a textbook-specific assertion. BM25 can miss related passages: verify answers against the cited original pages.

## Files

| Path | Purpose |
|---|---|
| `app.py` | Flask routes, Claude API calls, language and answer-category handling, HTML textbook reader, citation checks |
| `book_search.py` | PDF text extraction, chapter information, bilingual glossary and local page-aware search |
| `data/book.pdf` | Original open-access textbook by Kimmo Vehkalahti, CC BY 4.0 |
| `templates/index.html` | Web interface, prominent title and attribution, chapter links |
| `static/style.css` | Responsive website styling |
| `static/app.js` | Browser chat controls, provenance labels, citation links, Markdown and math formatting |
| `.env.example` | Example environment variables; do not commit real API keys |
| `render.yaml` | Render Blueprint deployment settings |
| `tests/test_retrieval.py` | Source-PDF and local index tests |

## 1. Run locally on a Mac

1. Extract the ZIP. Open **Terminal** and change to the project folder. For example:

   ```bash
   cd ~/Downloads/kysely_book_agent
   ```

2. Create a Python virtual environment, activate it and install dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

3. Create your local `.env` file and edit it:

   ```bash
   cp .env.example .env
   open -e .env
   ```

4. Set `ANTHROPIC_API_KEY` to a **valid Anthropic API key** from the [Anthropic Console](https://console.anthropic.com/). A normal Claude web-chat subscription does *not* automatically include Claude API credits. The default model names are `claude-sonnet-5-5` and `claude-haiku-5-5`; make sure your account has access to both.

5. Set `APP_PASSWORD` to a password of your choosing, or leave it empty **only** if you intentionally want public chat access. For local use, either is fine.

6. Run:

   ```bash
   python app.py
   ```

7. Open **http://127.0.0.1:5000/**. The original textbook now opens in a **browser-independent HTML reader** at **http://127.0.0.1:5000/reader**. The separate PDF download is **http://127.0.0.1:5000/book/download**.

> If you see `zsh: command not found: flask`, you do not need to invoke the `flask` executable. Use `python app.py` after activating `.venv`.

## 2. Deploy to Render using GitHub

1. Create a new GitHub repository, such as **`kysely-book-agent`**, preferably private until you have tested it.
2. Upload the **contents inside** the extracted `kysely_book_agent` folder to the **root** of the repository. GitHub should show `app.py`, `book_search.py`, `render.yaml`, `requirements.txt`, `templates/`, `static/` and `data/book.pdf` at the root.
3. Never upload `.env`, your Claude API key or other passwords to GitHub. `.gitignore` is included for this reason.
4. Log in to [Render](https://dashboard.render.com/) and select **New → Blueprint**. Connect the new GitHub repository and approve the settings in `render.yaml`. (Alternatively, create **New → Web Service**, Python 3, build command `pip install -r requirements.txt`, start command `gunicorn app:app --workers 2 --timeout 120 --bind 0.0.0.0:$PORT`.)
5. In Render's Environment settings, set **`ANTHROPIC_API_KEY`** to the new valid key. The Blueprint already defines the default Claude model IDs.
6. Set **`APP_PASSWORD`** to a strong access code. This is especially important if the Render URL is public because *you* pay for other users' Claude API requests. Leaving it empty means **any visitor can use the chatbot**, and may incur API charges. The PDF remains freely available.
7. If using the Blueprint, `FLASK_SECRET_KEY` is generated for you automatically. The app does not currently require signed login sessions, but you may retain this value for future updates.
8. Let Render deploy the service. Check these URLs after the service is live:
   - `https://YOUR-SERVICE.onrender.com/` — main chat
   - `https://YOUR-SERVICE.onrender.com/health` — index and model diagnostics
   - `https://YOUR-SERVICE.onrender.com/reader` — accessible HTML textbook reader, with direct page links such as `?page=41`
9. If the first run fails, read **Render → Logs**. If your Claude key is later changed or revoked, set the updated `ANTHROPIC_API_KEY` in Render → Environment, then choose **Save, rebuild, and deploy** (or **Save and deploy** if dependencies haven't changed).

`render.yaml` requests the service name `kysely-book-agent`; the actual URL is assigned by Render and depends on availability. You may choose a different name in your Render service settings if needed. Setting a custom domain requires control of that domain and DNS configuration.

## 3. Test questions

| Language / Purpose | Example |
|---|---|
| Finnish — in book | `Mitä kirjassa kerrotaan validiteetista ja reliabiliteetista?` |
| English — in book | `Explain the measurement model and which chapter covers it.` |
| English — in book | `Where does Vehkalahti discuss factor analysis?` |
| Finnish — in book | `Mitä regressiodiagnostiikalla tarkoitetaan?` |
| Translation | Choose **Translate book text → English**, then ask `Translate page 41 into English.` |
| Figure | `Explain Figure 2.1 on page 21 in English.` |
| Related but outside | `How would I implement an online Qualtrics survey in 2026?` — should be marked related but *outside the retrieved book text*. |
| Clearly out of scope | `Who won yesterday's football game?` — should be labelled out of scope. |

Answers containing outside-of-book information are explicitly separated and labelled. In mixed answers, book facts have citations, while outside knowledge is clearly distinguished.

## 4. Settings

`.env` variables or Render Environment entries:

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | *(required)* | Anthropic API secret. Never put it in the browser or GitHub. |
| `ANTHROPIC_MODEL` | `claude-sonnet-5-5` | Model that writes the final answer. |
| `ANTHROPIC_SEARCH_MODEL` | `claude-haiku-5-5` | Model that converts English query terms to Finnish. |
| `APP_PASSWORD` | empty | Optional shared access code for chat; blank makes API usage public. |
| `TOP_K` | `9` | Number of short source passages sent to Claude. |
| `MAX_TOKENS` | `3000` | Maximum answer tokens (server bounds apply). |
| `BOOK_PATH` | `data/book.pdf` | Optional alternative path to the original book PDF. |

### Notes and limits

- Answers and translations from Claude may be inaccurate: always check the original source, especially formulas, statistical interpretation, and charts. AI-generated translations are **not an official published translation**.
- The PDF is searched locally and the selected excerpts (and occasionally a screenshot of one page) are sent to the Claude API. No independent live internet or scholarly literature search is enabled. Related material outside the book is presented as **model general knowledge**, explicitly labelled as such.
- Pages are rendered in Claude only when a question mentions a figure or table; numerical structures in plain extracted text can be imperfect.
- The app uses Anthropic `output_config.format` structured JSON, compatible with Sonnet 5.5 (which rejects forced tool choices). The app makes billable Claude API requests. Password protection is simple shared-password gating, not institutional SSO; for a larger public launch, add server-side rate limits, user authentication and budget safeguards.
- If the `data/book.pdf` file is missing or renamed, startup will fail: retain the supplied original file.
- Book structure is based on the 2019 PDF's table of contents; sections and page locations are matched to **that exact edition**.

## 5. Run local index tests

```bash
python -m unittest discover -s tests -v
```

They test page mapping, the author/copyright page, text extraction and representative retrieval. They do not call Anthropic. For a full application smoke test, use a real API key locally and confirm response category labels in the browser.

## Refreshed interface — October 2026

The interface now uses a simplified white/black layout with restrained blue accents,
following the University of Helsinki's general colour guidance. **This is not an
official University of Helsinki website or endorsed institutional branding.**

- Open/close the **Contents / Sisällys** chapter panel using **Show contents** or
  **Hide contents** immediately above the chat. The app remembers your preference
  in the browser; the panel starts closed on small screens unless a preference
  was already saved.
- Open the book with the prominent **Read textbook / Avaa kirja** button.
- The original author, **Kimmo Vehkalahti**, appears beneath the book title and
  in the attribution footer.
- Language and translation controls remain available above the message box;
  the source-vs-outside-book classification and direct page links are unchanged.

### Apply the update to an existing GitHub/Render deployment

If you already have an operational copy of KyselyTutor, you can replace **only**:

```
templates/index.html
static/style.css
static/app.js
```

Then run these commands from the existing repository directory:

```
git add templates/index.html static/style.css static/app.js
git commit -m "Simplify KyselyTutor interface and add contents toggle"
git push origin main
```

Render should redeploy when it receives the new commit (if auto-deploy is enabled).
You do not have to change the Anthropic API key, the backend code or the textbook.
Never commit `.env`, API credentials, `.venv` or `.git` directories inside a ZIP.

Original design inspiration: https://www.helsinki.fi/en/brand-book/colours

## Interface update: Helsinki homepage-inspired blue accents (October 2026)

The independent study interface adopts a white-dominant, black-and-blue visual style inspired by the University of Helsinki homepage and its [colour guidelines](https://www.helsinki.fi/en/brand-book/colours). It is not an official University of Helsinki website and does not use any university logo.

- A visible blue rule, book-title underline, author emphasis, PDF action, and blue chapter/chat accents provide more visual emphasis while keeping the overall interface spacious.
- The **Show contents / Hide contents** button toggles the PDF chapter navigation. The preference persists in the browser.
- Four **one-click sample questions**, two Finnish and two English, demonstrate core retrieval and translation features. Each button selects its language and sends the question immediately, except that a password-protected installation first asks for the access code.
- The interface is responsive to mobile screens.

To update an existing deployment without replacing the backend or the book, copy `templates/index.html`, `static/style.css`, and `static/app.js` from the UI-only ZIP into the same paths in the project's repository, then commit and push. No new environment variables or Python packages are required.

## Optional dark mode (October 2026)

Use the **Dark mode** button in the header to switch from the default light
Helsinki-inspired theme to a dark reading theme with blue highlights. In dark
mode, the same button reads **Light mode**. The selection is remembered in
that browser (`localStorage`); it does not affect the backend, Claude API,
other visitors, or their preferences. The contents toggle and four bilingual
example questions remain unchanged.

To add dark mode to an existing installation, replace only
`templates/index.html`, `static/style.css`, and `static/app.js` and push to GitHub.
There are no new dependencies or environment variables.


## New browser-independent textbook reader (October 2026)

### Why this change was made

Some browsers download an inline PDF instead of opening it, and their support
for `#page=41` and other PDF fragment links differs. KyselyTutor therefore
uses a **custom HTML reader** instead of a browser PDF plugin or remote PDF.js
script. Each of the original PDF's 223 pages is rendered as a high-resolution
**PNG on demand** by the server using the already-installed PyMuPDF library.
The reader has no external JavaScript dependencies. This makes it usable in
modern browsers that support standard HTML, JavaScript and PNG images.

- The prominent **Read textbook / Avaa kirja** button opens `/reader`.
- The AI's cited page links and chapter navigation now open `/reader?page=41`
  (where the page number varies). These are ordinary shareable HTML page URLs.
- Existing links using `/book.pdf#page=41` are supported: `/book.pdf` now serves
  the HTML reader and its JavaScript interprets the old `#page` fragment.
- Search the **original Finnish book** across all 223 pages, view page matches
  and highlighted search terms, and jump directly to a result.
- Use Previous/Next, direct page entry, zoom, fit width, and arrow keys.
- Use **Show page text** to select/copy extracted Finnish text (the image above
  retains the precise appearance of the original printed book).
- The reader respects the same persisted light/dark setting and contents-panel
  setting as the main KyselyTutor interface.
- The original PDF has **not been altered** and is available explicitly using
  the **Download PDF / Lataa** button at `/book/download`. If desired, the raw
  PDF may also be viewed/downloaded at `/book/original.pdf`, but that fallback
  still depends on the browser's PDF handling.

### Apply to an existing GitHub / Render deployment

This update **also changes Flask routes**. Replacing only the three former UI
files is insufficient. Copy the following files from the reader update ZIP
into the matching paths of your repository (keep your own `.env` untouched):

```text
app.py
templates/index.html
templates/reader.html    (new)
static/app.js
static/reader.css       (new)
static/reader.js        (new)
tests/test_reader.py    (new; optional test file)
```

Then in Terminal from your existing project directory:

```bash
git add app.py templates/index.html templates/reader.html static/app.js static/reader.css static/reader.js tests/test_reader.py
git commit -m "Add cross-browser textbook reader and reliable page links"
git push origin main
```

Render normally redeploys automatically if auto-deploy is enabled. No new
Claude API settings, Python packages, or environment variables are required.
If working locally, stop the old server and start it again using `python app.py`.

### Verification

Run `python -m unittest discover -s tests -v` from the project root.
Directly check `/reader?page=41`, `/reader?page=93`, `/reader?page=223`,
`/book.pdf#page=116`, `/api/book/search?q=validiteetti`, and `/book/download`.
Source text selection is an extracted-text view, not a perfect pixel-aligned
text overlay. Image quality depends on the device and zoom factor.

No remote PDF.js/CDN, iframe, or special browser PDF capabilities are required.
