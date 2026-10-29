# KyselyTutor: Relevant-paragraph highlighting update

This corrects inconsistent highlighting caused by requiring Claude to supply
an exact Finnish quote. It now highlights **all relevant paragraphs selected
by Claude** from real source passages instead of relying on substring matching.
Highlights work with Finnish explanations, English paraphrases, and translations.

The reader renders selected lines in transparent orange and continues to
provide a Show/Hide highlights control. It works with links like:

    /reader?page=41&b=s0&b=s3&b=s4

Old `?h=` links still use approximate paragraph matching. Out-of-book
answers continue to be clearly identified and have no book highlights.

## Existing GitHub/Render deployment

Extract the **update ZIP** into your repository root and replace the included
files. **Also copy the new file `evidence_passages.py` into the project root.**
Then run these commands from your project directory:

```bash
git add app.py evidence_passages.py static/app.js static/reader.js templates/reader.html tests/test_answer_highlights.py README.md THIS_UPDATE.md
git commit -m "Highlight relevant textbook paragraphs in reader"
git push origin main
```

Render should rebuild automatically if auto-deploy is enabled. No environment
variable, `requirements.txt`, PDF, or API key changes are needed. New answer
links will carry selected paragraph IDs. Previously rendered chat responses
cannot be retroactively rebuilt into the new format, but old `h=` links work.

## Verification

After installing dependencies locally, run:

```bash
python -m unittest discover -s tests -v
```

Then ask an English question about validity/reliability, click a citation to
page 41, and check that multiple related Finnish passages are orange. Toggle
Show/Hide. Repeat for a Finnish question about factor analysis (pages 93–96).

**Limitation:** These are model-selected relevant passages rather than exact
sentence alignment. If the model's evidence mapping is incomplete, a small
number of related paragraphs may still be missed; the fallback reduces, but
cannot completely eliminate, that possibility. Unextractable figures cannot
be text-highlighted.
