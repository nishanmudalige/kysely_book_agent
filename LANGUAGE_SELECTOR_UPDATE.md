# KyselyTutor: Reply-language selector correction

The Reply language selector now stays at **Automatic / Automaattinen** until the visitor explicitly changes it. Clicking Finnish or English sample questions and choosing a translation task no longer changes this setting. If a user explicitly selects English or Suomi, their preference remains selected after submitting any question.

Automatic response-language detection remains in the backend. Translation-task selections continue to tell Claude the requested translation language without changing the Reply language dropdown.

For an existing repository, copy `static/app.js` from the small update ZIP into the corresponding path, then run:

```bash
git add static/app.js
git commit -m "Keep reply language setting unchanged after prompts"
git push origin main
```

No Python dependencies, API keys, or Render environment variables need changing. For best results, hard-refresh the page after Render finishes redeploying so your browser does not use a cached JavaScript file.
