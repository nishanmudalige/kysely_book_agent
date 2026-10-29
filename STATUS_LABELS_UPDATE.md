# KyselyTutor — three-colour response-source labels

The interface once again distinguishes the three source categories with coloured boxes:

- **Green: From the textbook / Kirjasta.** Answer supported by the retrieved textbook excerpts.
- **Orange: Related — outside the textbook / Aiheeseen liittyvä — ei kirjasta.** Useful related information that is not established by the retrieved textbook content.
- **Red: Not relevant to this textbook / Ei liity kirjan aihepiiriin.** Unrelated requests.

A mixed answer displays two labelled sections: green for sourced content, orange for general-knowledge additions.
The badges are styled for both light and dark mode. All existing PDF highlighting, bilingual interaction, random sample questions, and chapter navigation are preserved.

## Updating an existing Render deployment

Extract the update ZIP into the *root* of your existing local GitHub project folder so that the included `static/app.js` and `static/style.css` replace the existing files. No backend files need changing. Then run:

```bash
git add static/app.js static/style.css
git commit -m "Restore green orange red answer labels"
git push origin main
```

If Render has auto-deploy enabled, it will deploy the updated files. Hard-refresh the browser if cached styles remain.

## Tests

Checked the actual JavaScript response renderer in Chromium with mocked book, related, unrelated, and mixed responses; checked Finnish translations and computed badge colours in both light and dark mode. No live Claude API call was needed for this styling update.
