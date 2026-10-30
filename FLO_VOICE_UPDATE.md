# Default voice: Flo (Finnish, Finland)

The Read Aloud voice chooser defaults to **Flo (fi-FI)** when your browser makes that voice available. If your device does not offer Flo, the existing automatic choice remains active.

English sentences continue to use an English voice, even when Flo appears selected, to preserve English pronunciation. Any manual voice selection (including Automatic) is respected for the rest of the page session; it will not be replaced when the browser reloads its voice list.

## Install in an existing KyselyTutor repository

Replace `static/speech.js` with the file from this update, then:

```bash
git add static/speech.js
git commit -m "Set Flo as default Finnish reading voice"
git push origin main
```

No new Python packages, API keys or environment variables are required. To test locally, use `node tests/test_default_flo_voice.cjs` if Node.js is installed.
