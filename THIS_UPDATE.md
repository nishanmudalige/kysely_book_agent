# KyselyTutor – Rotating suggestions and answer highlights

Changes compared with the previous universal-reader release:

- Four suggested questions form one horizontal row on desktop; on small screens, swipe or scroll horizontally to access all four.
- The app randomly chooses two Finnish and two English examples from a bank of 24 (12 per language). A local-storage record prevents a question from appearing in consecutive refreshes on the same browser.
- Claude's JSON responses can include concise **verbatim Finnish evidence phrases** for each cited PDF page. The server verifies these phrases against both the retrieved textbook excerpts and the *actual* PDF page. Unverified evidence is ignored.
- Cited page links open the custom `/reader` with the evidence phrases in the URL. The reader highlights those original words with translucent orange overlays and scrolls to them.
- **Hide highlights / Show highlights** toggles the overlay, retaining the preference in the reader. The highlight toggle appears only on pages for which highlights are available (including manual search).
- Original PDF download, English/Finnish answers, dark mode, contents toggle, access code, Claude configuration, and existing `/reader?page=NN` links are unchanged.

## Updating an existing deployment

Extract the update ZIP at the root of your existing repository, replacing the corresponding files. Then run:

```bash
git add app.py templates/index.html templates/reader.html static/app.js static/style.css static/reader.js static/reader.css tests/test_answer_highlights.py

git commit -m "Rotate sample questions and highlight textbook evidence"
git push origin main
```

Render should redeploy if automatic deployments are enabled. **Backend `app.py` must also be updated** because it requests and validates the highlight evidence from Claude. No new packages or environment variables are required.

## Notes

The highlight feature relies on Claude returning a short exact excerpt from the Finnish book. If Claude fails to supply a matching passage, the citation still opens the correct page **without an unverified orange highlight**. The reader never highlights text that was not found in the original PDF. Old chat messages or manually entered bare `/reader?page=N` URLs cannot reconstruct earlier answer evidence, but pages remain readable and searchable.

Test with:

```bash
python -m unittest discover -s tests -v
```
