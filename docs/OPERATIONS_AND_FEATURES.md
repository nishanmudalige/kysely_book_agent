# KyselyTutor — Features, architecture, operations and troubleshooting

**Version basis:** Consolidated as of 30 October 2026 from the current project and its previous reader, highlighting, language, labels, speech/Flo, hockey, and Finland-personality update notes. This is the companion to the project [README](../README.md), **not** a new patch that must be applied in feature-by-feature order.

## 1. Design and scope

The application is an **independent educational companion** for the open-access Finnish textbook *Kyselytutkimuksen mittarit ja menetelmät* by **Kimmo Vehkalahti**. The original book's 2019 University of Helsinki PDF, its author credit, DOI, publication details and CC BY 4.0 licence must remain visible. The Helsinki-inspired black, white and blue design does **not** imply university endorsement.

The primary task is source-grounded explanation and translation of the textbook. Adjacent statistics questions may be answered with clearly marked general AI knowledge; entirely unrelated questions are ordinarily declined. Explicitly supported *personality* exceptions—Finnish statisticians, Finnish history/geography and hockey—are allowed but always shown as **outside the textbook**.

## 2. Application components and data flow

1. `app.py` launches Flask and creates `BookIndex(data/book.pdf)` on startup.
2. `book_search.py` extracts PDF text with PyMuPDF and performs local, page-aware BM25-style retrieval. For English queries, Claude Haiku can help generate Finnish search terms, with an offline glossary fallback.
3. For ordinary academic answers, `app.py` sends the question, retrieved excerpts, candidate evidence passages and relevant recent conversation turns to Claude Sonnet using a structured JSON schema. Questions specifically about figures or tables can include a rendered PDF page image.
4. `verified_response()` checks source-page citations against the supplied excerpts and only links validated page numbers. `evidence_passages.py` selects real, page-specific Finnish source paragraphs to support the citations.
5. The browser displays coloured provenance labels. Valid book citations link to `/reader?page=NN` and can include `b=` paragraph IDs. The HTML reader fetches server-generated page PNGs and independent overlay coordinates.
6. Separately recognised hockey and Finland questions use special paths. They must not manufacture textbook citations or mark external biographical/historical facts as originating from the book.

### Important Python files

- **`app.py`:** routes, environment parsing, request classification, Anthropic calls, page rendering and evidence selection.
- **`book_search.py`:** textbook extraction, pages, chapters, search and language glossary.
- **`evidence_passages.py`:** real PDF paragraph IDs (`s0`, `s1`, etc.), source selection, and highlighting fallback.
- **`hockey.py`:** hockey routing, Jokerit preference, current-season Liiga standings fetch/validation, and dated Finnish NHL roster notes.
- **`finland_topics.py`:** optional topics, biographical/history/geography notes and conservative follow-up detection.
- **`static/app.js` / `static/style.css`:** chat, Markdown and citation links, topic colours, sample questions, language and theme settings.
- **`static/reader.js` / `static/reader.css`:** navigation, search, page images, evidence overlays, highlight toggles and reader preferences.
- **`static/speech.js` / `static/speech.css`:** read-aloud, selection handling, voice options and playback controls.

## 3. Provenance and response classification

| Backend category | User-facing meaning | Display colour |
|---|---|---|
| `book` | From the retrieved textbook excerpts, with validated PDF page references | Green |
| `mixed` | Book-based segment + separate related non-book segment | Green + orange |
| `related_outside` | Survey/statistics-adjacent, but not established by excerpts | Orange |
| `out_of_scope` | Not within the textbook or permitted side topics | Red |
| `statisticians` | Finnish statisticians / context, not assumed to be in book | Purple |
| `history` | Finnish history, outside-book knowledge | Blue |
| `geography` | Finnish geography, outside-book knowledge | Teal |
| `hockey` | Finnish hockey / NHL knowledge, outside-book knowledge | Slate blue |

The frontend uses different colours in light and dark mode. The application is designed to **avoid citing a book page for external knowledge**. The categories are provenance indicators, not quality certificates.

**Mixed answers:** A source-backed statistical explanation appears in green, while explanatory material not supported by retrieved book excerpts appears in orange. Do not blend the two without labels.

## 4. Language, translation and prompt examples

The **Reply language** setting defaults to **Automatic / Automaattinen**. Submitting questions does **not** change the dropdown. The user may explicitly choose Finnish or English. Selecting a translation task changes the *requested output for that task*, not the dropdown's stored selection.

A horizontally arranged row shows **four rotating examples** drawn from 12 Finnish and 12 English suggestions. The set contains two of each language and is selected anew on reload, avoiding the previous set in the same browser when storage is available. On narrow screens the row scrolls sideways. Clicking an example submits its question (after access-code handling if password protection is active); it does not silently override the user's reply-language choice.

**Translation limitations:** The original book is in Finnish; English renditions are AI-generated, not an authorised English edition. A whole-page translation requires that the appropriate complete page text was provided; otherwise the tutor should explain that only part was available. For longer material, use page-by-page requests.

## 5. Custom textbook reader and browser support

Use the **HTML reader**, not raw browser PDF embedding, as the normal route. PyMuPDF renders an original PDF page into a PNG on demand. This avoids browser plug-in differences and unreliable `#page=` handling.

Supported reader features:

- Visible book title and author attribution; chapter navigation, Show/Hide contents panel.
- `?page=41`–style deep links; Previous/Next, numeric page entry, left/right arrow keys, zoom and Fit width.
- Search across the original Finnish text and jump to matching pages.
- **Show page text** for copying or selecting extracted Finnish text separately from the page image.
- **Show/Hide highlights** and **Read highlighted text** when there are relevant citation passages.
- Shared light/dark theme preference and persisted contents/highlight toggles.
- Original-PDF Download button as a separate option.

### Reader URL reference

| Route / URL | Behaviour |
|---|---|
| `/reader` | Custom HTML reader, first page |
| `/reader?page=41` | Open page 41 |
| `/reader?page=41&b=s0&b=s3` | Open page 41 and request validated paragraph evidence overlays |
| `/book.pdf#page=41` | Legacy link handled by the reader JavaScript (the fragment is browser-side) |
| `/book/download` | Explicit download of original PDF |
| `/book/original.pdf` | Raw original PDF; rendering/download depends on browser |
| `/api/book/page/41.png?scale=2.5` | Server-rendered PNG page |
| `/api/book/text/41` | Extracted page text as JSON |
| `/api/book/search?q=validiteetti` | Matching pages/snippets as JSON |
| `/api/book/highlights/41?b=s0` | Coordinates and passage text for selected original-Finnish evidence |
| `/health` | Basic application/index metadata |

The 2019 edition has **223 PDF pages**. Its **printed page number aligns with the PDF page number** in the main text; do not add an offset for citations. Page links are *not* promises that every figure is extractable or searchable as text.

### What orange highlights mean

The agent does **not** need to quote a matching Finnish sentence. Candidate paragraphs are selected from the actual PDF page; Claude chooses supporting passage IDs to cover different claims, including an English paraphrase of Finnish material. The server validates those IDs and can use a relevant-paragraph fallback when IDs are absent. It then computes rectangles from the original page text and draws transparent orange overlays.

This is **supporting-context highlighting**, not exhaustive alignment. Unretrieved paragraphs, poorly extracted text, figures and scanned imagery may not highlight. The reader can display valid cited pages even when no highlight is found. Older `h=` quotation links retain approximate matching; newer answers use `b=` IDs. Old chat responses do not gain new evidence identifiers automatically—ask the question again.

**Testing note:** `&b=s0` is valid on a reader URL. Tests must parse `page=41` and tolerate evidence parameters; they must **not** assert that the complete URL is exactly `/reader?page=41`.

## 6. Read-aloud and bilingual voices

Text-to-speech uses the **browser Web Speech API** and available system/browser voices; Claude does not generate audio. No separate TTS API key is required.

**Available controls:** Play/Resume, Pause, Stop, Restart/Rewind, Previous sentence, Next sentence, playback speed (roughly **0.8×–1.5×**), and Automatic or manually selected voice.

**Where it works:**

- **Answer text:** Select text in the chat and press **Read selection / Lue valittu**, or use **Read aloud** for the latest answer.
- **Textbook page:** Choose **Show page text**, select text and use **Read selection**, or use **Read aloud** for the entire extracted page text.
- **Orange citation highlights:** Use **Read highlighted text** to hear the identified Finnish passages without manually selecting them.

**Default voice behaviour:** If a browser exposes the **Flo** Finnish voice as `fi-FI`, it becomes the default preferred Finnish voice. English sentences should still use an English voice, even when Flo is selected in the menu. A user's explicit voice choice is respected for the current session. If Flo is unavailable, the browser's alternatives are used. Some browser/OS voice engines may rely on their own services; sound quality and playback behaviour are device-dependent. The main chat's Reply language selection remains independent.

**Caution:** Text displayed as a PDF page image is **not directly selectable**; use the separate extracted-text view. Automatic language detection may be imperfect for very short, mixed-language selections. Test actual pronunciation on each intended OS/browser.

## 7. Finland-related personality

These topics add personality while remaining optional and **outside the main survey-methodology textbook**.

### Finnish statisticians (purple)

The supplemental notes emphasise **Seppo Mustonen**, his work on **Survo**, and his scholarly connection with **Kimmo Vehkalahti**. Other individuals include **Lauri Tarkkonen** and **Simo Puntanen**, who are also acknowledged in the textbook. The textbook's acknowledgements (p. 9) support claims that those individuals are thanked; external biographies, educational histories, or influence should be traced to separately identified notes and references, **not inferred from that acknowledgement alone**. `finland_topics.py` contains the background notes and referenced links.

For ordinary questions specifically asking **what the textbook says** about measurement, Survo, the measurement framework or its cited authors, prefer the textbook retrieval flow. For biographies and wider Finnish statistical history, use the non-book label.

### Finnish history (blue) and geography (teal)

History coverage includes Swedish and Russian rule, independence, the Civil War, Winter and Continuation Wars and later milestones. Geography includes cities, lakes, Lapland, Åland, islands, climate and regions. These topics are generated from Claude plus **preloaded, source-referenced notes**; the application does **not** perform a live web search for current history/geography facts. Treat changing figures and news as unverified without an external check.

### Hockey (slate blue)

The agent's playful favourite is **Helsingin Jokerit**, not necessarily the highest-ranked Liiga team. When asked for the **best team** or **current Finnish league table**, it attempts to fetch **official Liiga standings**, shows the leader/top five and Jokerit's position when verified, and then mentions its preference. If the official endpoint fails or data cannot be validated, it links to the official standings **without inventing rankings**.

- Official table: <https://liiga.fi/fi/tilastot/joukkuetilastot/kausi?tilasto=sarjataulukko>
- JSON endpoint used by the app: `https://liiga.fi/api/v2/standings/?season=YYYY` (where YYYY is season end year).
- A short **ten-minute per-process cache** reduces API requests; data may lag accordingly.
- For Finnish NHL player questions, Claude receives a **dated October 2026 roster snapshot** and can direct users to <https://www.nhl.com/players>. It is **not** a live NHL player-statistics integration.

The optional cultural personality should **not** interrupt academic explanations with unsolicited hockey jokes.

## 8. Configuration and security

Configure a local `.env` based on `.env.example` or set the same variables in Render Environment:

| Key | Default / role |
|---|---|
| `ANTHROPIC_API_KEY` | **Required for Claude requests**; never commit it |
| `ANTHROPIC_MODEL` | `claude-sonnet-5-5` unless overridden |
| `ANTHROPIC_SEARCH_MODEL` | `claude-haiku-5-5` unless overridden |
| `APP_PASSWORD` | Empty by default; set a strong shared chat password before public deployment |
| `FLASK_SECRET_KEY` | Blueprint generates a value; local `.env.example` has a placeholder |
| `TOP_K` | `9` requested excerpts; the server constrains the permitted range |
| `MAX_TOKENS` | `3000` final-answer token budget; the server constrains the permitted range |
| `BOOK_PATH` | Defaults to `data/book.pdf` under the project directory |
| `PORT` | Defaults to `5000` for local Flask; provided by Render in production |

The app sends the latest user question and recent chat turns, **retrieved textbook excerpts**, and sometimes a screenshot-like page image to the **Anthropic API**. Reader and PDF downloads are served separately without Claude. Shared-password protection is not a user-management system. There is no database of conversations in this codebase; host access logs and third-party data handling remain separate considerations. Do not claim the app offers institutional data security by default.

If the Anthropic key is revoked, change it in both the appropriate local `.env` and Render Environment as applicable, then redeploy/restart. Do not put API secrets in frontend code, Git history or printed documentation. Track Claude usage and billing independently.

## 9. Install, update, test and troubleshoot

### Fresh installation

Follow the root README. The essential steps are `python3 -m venv .venv`, `source .venv/bin/activate`, `python -m pip install -r requirements.txt`, configure `.env`, then `python app.py`. The Render Blueprint is at `render.yaml`.

### Updating from an earlier KyselyTutor version

**Prefer a complete current version** over layering older patch ZIPs. Earlier feature updates changed overlapping files (particularly `app.py`, `static/app.js`, and `static/style.css`), and applying them out of chronological order can undo later features. Back up your customized files before replacing them, inspect with `git diff`, and use `git status` before committing.

If you are **only consolidating documentation**, replace `README.md` and add `docs/OPERATIONS_AND_FEATURES.md`. There is **no required application-code change**.

```bash
git add README.md docs/OPERATIONS_AND_FEATURES.md
git commit -m "Consolidate KyselyTutor documentation"
git push origin main
```

For future code modifications, stage the files actually changed, and do not commit `.env`, `.venv`, or other secrets. Render auto-deploys on pushes only if it is configured to do so.

### Tests and manual verification

```bash
source .venv/bin/activate
python -m unittest discover -s tests -v
node tests/test_default_flo_voice.cjs  # optional; requires Node.js
```

Suggested smoke checks: `/health`, `/reader?page=41`, `/reader?page=93`, `/book/download`, sample questions in both languages, a book answer with green citation labels and orange reader highlights, dark mode, Show/Hide contents, speech controls, and the separate Finnish-statistician/history/geography/hockey modes. Live standings need outbound internet. Natural audio and real Claude outputs need manual testing.

| Symptom | Checks / resolution |
|---|---|
| `zsh: command not found: flask` | Use `python app.py`; activate `.venv` and install requirements. |
| `ModuleNotFoundError` | Verify the active virtual environment and run `python -m pip install -r requirements.txt`. |
| Claude authentication or model error | Check `ANTHROPIC_API_KEY`, model availability, account credits and Render logs. |
| Readers download PDF rather than show a page | Link to `/reader?page=N`, not `/book/original.pdf`; `/book/download` intentionally downloads. |
| A citation has `&b=s0` | This is an evidence selector, **not** a broken URL. Update tests to parse the `page` argument. |
| Some supporting paragraphs not highlighted | Passage mapping is approximate; regenerate a fresh answer, use the Show/Hide toggle, and check PDF text extractability. |
| Language dropdown switches after a sample | An old `static/app.js` was deployed or cached; use the current file, redeploy and hard-refresh. |
| Flo absent or voice robotic | Browser/OS voice missing or low-quality; try a different installed voice. |
| Liiga table unavailable | The official endpoint may be down, changed or blocked. Show a link; do not guess rankings. |
| CSS/JavaScript changes not visible | Check Render deployment and perform a hard refresh to bypass cached assets. |
| Reader slow on a page | Server renders PNGs on demand; inspect Render logs, memory/CPU and request load. |

## 10. Consolidated change history

The previous one-feature update files are summarised here so they do not need to remain scattered in the repository:

| Earlier update | Retained behaviour in current project |
|---|---|
| Helsinki-inspired UI + dark mode | Blue accents, readable layout, mobile support, remembered theme and contents panel |
| Browser-independent reader | HTML/PNG viewer, dependable page URLs, PDF download, search and zoom |
| Rotating questions | One horizontal row; 2 Finnish + 2 English from 24; avoids immediate repetition |
| Relevant-paragraph highlighting | Validated `b=` passage IDs, orange evidence overlays, toggle and fallback for paraphrases |
| Three-colour source labels | Green book, orange related outside, red unrelated; mixed answers separated |
| Reply-language correction | Automatic stays selected unless the visitor explicitly changes it |
| Read-aloud + Flo | Speech controls, Finnish/English detection and preferred Flo Finnish voice when available |
| Hockey corner | Jokerit preference, conditional official Liiga standings and dated Finnish NHL snapshot |
| Finnish statisticians/history/geography | Additional topic routing and purple/blue/teal labels |
| Reader-test correction | Tests accept valid citation evidence selectors such as `&b=s0` |

### Attribution and external references

- Book: Kimmo Vehkalahti, *Kyselytutkimuksen mittarit ja menetelmät*, open-access PDF (2019), DOI <https://doi.org/10.31885/9789515149817>; original text CC BY 4.0.
- Design reference (inspiration only): <https://www.helsinki.fi/en/brand-book/colours>.
- Finnish-statistician and historical/geographic citations: see the referenced notes in `finland_topics.py`.
- Official Liiga standings: <https://liiga.fi/fi/tilastot/joukkuetilastot/kausi?tilasto=sarjataulukko>.
- NHL player directory: <https://www.nhl.com/players>.

**No endorsement or affiliation is implied by these links.**
