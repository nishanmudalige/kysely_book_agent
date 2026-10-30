# KyselyTutor — read-aloud / Ääneenluku update

## Replace existing files on GitHub / Render

Use the update ZIP, extract its `kysely_book_agent` folder, and copy these files into the same relative paths in your existing repo:

- `app.py`
- `templates/index.html`
- `templates/reader.html`
- `static/app.js`
- `static/reader.js`
- `static/style.css`
- `static/reader.css`
- **NEW** `static/speech.js`
- **NEW** `static/speech.css`
- `README.md` (documentation update)

Then, from the root of your existing project:

```bash
git add app.py templates/index.html templates/reader.html static/app.js static/reader.js static/style.css static/reader.css static/speech.js static/speech.css README.md SPEECH_UPDATE.md
git commit -m "Add Finnish English read-aloud controls"
git push origin main
```

Render auto-deploys when automatic deployment is enabled. **No new environment variables, API keys or pip packages are required.**

## Using the reader

To listen to selected text from a PDF page, press **Show page text**, select the relevant passage, then press the floating **Read selection / Lue valittu** button. The image itself is not a selectable text layer. To listen without selecting, press **Read aloud** for the entire page, or **Read highlighted text** for source paragraphs linked from a tutor answer.

Use the player's rewind, previous/next sentence, play/resume, pause, stop, speed and voice options. Finnish/English are detected automatically; reply-language settings are not changed.

### Quality note

Voice quality varies by browser, OS and which system voices the visitor has installed. The app automatically prefers voices labelled enhanced/natural/neural, but cannot install voices or guarantee studio-quality synthesized speech. The voice menu permits explicit selection. No audio is produced by Claude itself.
