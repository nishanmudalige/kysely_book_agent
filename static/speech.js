/* KyselyTutor read-aloud player. Uses the browser's own Web Speech API.
   Text and selection stay in the visitor's browser: no cloud speech API/key.
   Read-aloud is intentionally independent of the Claude answer language setting. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const panel = $('speech-player');
  if (!panel) return;
  const synth = ('speechSynthesis' in window) ? window.speechSynthesis : null;
  const supported = Boolean(synth && 'SpeechSynthesisUtterance' in window);
  const trigger = $('speech-trigger');
  const float = $('speech-selection-action');
  const preview = $('speech-preview');
  const progress = $('speech-progress');
  const detected = $('speech-detected');
  const notice = $('speech-notice');
  const voiceList = $('speech-voice');
  const rate = $('speech-rate');
  const playButton = $('speech-play');
  const pauseButton = $('speech-pause');
  const backButton = $('speech-back');
  const nextButton = $('speech-next');
  const restartButton = $('speech-restart');
  const stopButton = $('speech-stop');
  const closeButton = $('speech-close');
  const reader = Boolean(document.body.classList.contains('reader-body'));
  let selectedText = '';
  let text = '';
  let sentences = [];
  let index = 0;
  let token = 0;
  let playing = false;
  let paused = false;
  let voices = [];
  let requestedLanguage = reader ? 'fi' : 'en';
  let autoVoice = true;
  let selectionDelay = null;

  const FINNISH_WORDS = new Set('ja on ovat oli olivat että se tämä nämä myös mutta kuin missä mikä mitä miten miksi milloin voiko voidaan jos jota jotka jonka tämä siitä sillä koska sekä esimerkiksi kirjan kirja kirjassa kysely kyselytutkimus aineisto aineiston muuttuja mittari mittaus menetelmä tutkimus tutkija vastaaja usein siihen niistä ei voi olla ole ovat tehdään näin siis näiden niiden voidaan'.split(' '));
  const ENGLISH_WORDS = new Set('the and is are was were of to in on for with from which this these those that as by an a how what why when where explain survey questionnaire questions book measurement data analysis method researcher sample validity reliability can be does not also example should between they their'.split(' '));
  const chunks = str => (str.toLocaleLowerCase().match(/[a-zà-öø-ÿ]+/gu) || []);
  // Scoring uses common grammatical words, Finnish inflections and diacritics;
  // short ambiguous excerpts inherit the selected area's language.
  function detectLanguage(input, fallback = reader ? 'fi' : 'en') {
    const words = chunks(input || '');
    if (!words.length) return fallback;
    let fi = 0, en = 0;
    for (const w of words) {
      if (FINNISH_WORDS.has(w)) fi += 3;
      if (ENGLISH_WORDS.has(w)) en += 3;
      if (/[äö]/u.test(w)) fi += 2;
      if (w.length > 6 && /(ssa|ssä|sta|stä|lla|llä|lle|ksi|minen|misen|ttava|tävä|tutkimuksessa|aineistossa)$/u.test(w)) fi += 1.4;
      if (w.length > 5 && /(tion|ment|ness|ally|able|ing)$/u.test(w)) en += .6;
    }
    if (Math.abs(fi - en) < 1.5) return fallback;
    return fi > en ? 'fi' : 'en';
  }
  const nameFor = lang => lang === 'fi' ? 'Finnish / Suomi' : 'English';
  const clean = s => (s || '').replace(/[\u200b-\u200d\ufeff]/g, '').replace(/\s+/g, ' ').trim();
  const wordCount = s => (s.match(/\S+/g) || []).length;

  // Long utterances can silently stop in some browsers. Split into short pieces
  // while keeping sentence boundaries and avoiding empty chunks.
  function sentenceParts(input) {
    const normalized = (input || '').replace(/\r\n?/g, '\n').replace(/\n{2,}/g, '. ').trim();
    let units;
    if (typeof Intl !== 'undefined' && Intl.Segmenter) {
      try { units = [...new Intl.Segmenter(undefined, {granularity:'sentence'}).segment(normalized)].map(s => s.segment); } catch (_) {}
    }
    if (!units) units = normalized.split(/(?<=[.!?])\s+|\n+/u);
    const result = [];
    for (let segment of units) {
      segment = clean(segment);
      if (!segment) continue;
      while (segment.length > 245) {
        let split = segment.lastIndexOf(' ', 220);
        if (split < 80) split = 220;
        result.push(segment.slice(0, split).trim());
        segment = segment.slice(split).trim();
      }
      if (segment) result.push(segment);
    }
    return result;
  }

  function quality(voice, lang) {
    const name = voice.name || '';
    const locale = (voice.lang || '').toLowerCase();
    if (!locale.startsWith(lang)) return -1000;
    let score = 10;
    if (locale.startsWith(lang === 'fi' ? 'fi-fi' : 'en-us')) score += 2;
    if (/neural|natural|premium|enhanced|siri|eloquence|high quality|google/i.test(name)) score += 8;
    if (/compact|low quality|eSpeak/i.test(name)) score -= 7;
    if (voice.localService) score += 1;
    if (voice.default) score += 2;
    return score;
  }
  function voiceFor(lang) {
    const available = voices.filter(v => (v.lang || '').toLowerCase().startsWith(lang));
    const preferred = voiceList.value;
    if (!autoVoice && preferred) {
      const match = available.find(v => v.voiceURI === preferred);
      if (match) return match;
    }
    return available.sort((a,b)=>quality(b,lang)-quality(a,lang))[0] || null;
  }
  function loadVoices() {
    if (!supported) return;
    voices = synth.getVoices() || [];
    const previous = voiceList.value;
    voiceList.replaceChildren();
    const auto = document.createElement('option');
    auto.value = ''; auto.textContent = 'Automatic — best available';
    voiceList.appendChild(auto);
    voices.filter(v => /^(fi|en)(-|$)/i.test(v.lang || '')).sort((a,b) => {
      const x = (a.lang || '') + a.name, y = (b.lang || '') + b.name;
      return x.localeCompare(y);
    }).forEach(v => {
      const option = document.createElement('option');
      option.value = v.voiceURI;
      option.textContent = `${v.name} (${v.lang})`;
      voiceList.appendChild(option);
    });
    if (previous && [...voiceList.options].some(o => o.value === previous)) voiceList.value = previous;
    else if (autoVoice) voiceList.value = '';
    updateVoiceWarning();
  }
  function updateVoiceWarning() {
    if (!supported) {
      notice.textContent = 'Read aloud is not supported in this browser. Try an up-to-date Safari, Chrome, Edge, or Firefox.';
      return;
    }
    const locale = requestedLanguage;
    const found = voices.some(v => (v.lang || '').toLowerCase().startsWith(locale));
    notice.textContent = voices.length && !found
      ? `No ${nameFor(locale)} voice is installed or exposed by this browser. Pronunciation may be inaccurate. Add a ${locale === 'fi' ? 'Finnish' : 'English'} system voice for better results.`
      : 'Speech uses voices available on your device. Naturalness depends on the browser and installed voices.';
  }

  function displayState() {
    const enabled = sentences.length > 0;
    [backButton, nextButton, restartButton, stopButton].forEach(b => b.disabled = !enabled);
    playButton.disabled = !supported || (!enabled && !selectedText);
    pauseButton.disabled = !playing || paused;
    progress.textContent = !enabled ? 'Ready to read selected text' :
      `${Math.min(index + 1, sentences.length)} / ${sentences.length} · ${paused ? 'Paused' : playing ? 'Reading' : 'Ready'}`;
  }
  function halt(clearQueue = false) {
    token += 1;
    playing = false; paused = false;
    if (supported) synth.cancel();
    if (clearQueue) { sentences = []; index = 0; text = ''; }
    displayState();
  }
  function doSpeak() {
    if (!supported) { displayState(); return; }
    if (index >= sentences.length) { playing = false; paused = false; index = 0; displayState(); return; }
    const speakToken = token;
    const segment = sentences[index];
    const lang = detectLanguage(segment, requestedLanguage);
    detected.textContent = `Detected: ${nameFor(lang)}`;
    const utterance = new SpeechSynthesisUtterance(segment);
    utterance.lang = lang === 'fi' ? 'fi-FI' : 'en-US';
    const voice = voiceFor(lang);
    if (voice) utterance.voice = voice;
    utterance.rate = Number(rate.value) || 1;
    utterance.pitch = 1;
    utterance.onend = () => {
      if (speakToken !== token) return;
      index += 1;
      if (index < sentences.length) doSpeak();
      else { playing = false; paused = false; index = 0; displayState(); }
    };
    utterance.onerror = ev => {
      if (speakToken !== token) return;
      if (ev.error === 'canceled' || ev.error === 'interrupted') return;
      playing = false; paused = false;
      notice.textContent = `Speech playback failed (${ev.error || 'unknown error'}). Try another voice in the voice menu.`;
      displayState();
    };
    playing = true;
    paused = false;
    displayState();
    try { synth.speak(utterance); }
    catch (error) { playing = false; notice.textContent = 'The browser could not start speech playback.'; displayState(); }
  }
  function jump(target) {
    if (!sentences.length) return;
    halt();
    index = Math.max(0, Math.min(sentences.length - 1, target));
    doSpeak();
  }
  function setSpeechText(input, fallbackLang) {
    const next = clean(input).slice(0, 20000);
    if (!next) return false;
    halt();
    text = next;
    sentences = sentenceParts(next);
    index = 0;
    requestedLanguage = detectLanguage(next, fallbackLang || (reader ? 'fi' : 'en'));
    detected.textContent = `Detected: ${nameFor(requestedLanguage)}`;
    preview.textContent = `${wordCount(text)} words · ${text.slice(0, 205)}${text.length > 205 ? '…' : ''}`;
    updateVoiceWarning();
    displayState();
    return sentences.length > 0;
  }
  function showPanel() {
    panel.hidden = false;
    trigger?.setAttribute('aria-expanded', 'true');
  }
  function hideFloating() { if (float) float.hidden = true; }
  function currentSelection() {
    const selection = window.getSelection?.();
    if (!selection || selection.isCollapsed || selection.rangeCount === 0) return null;
    const r = selection.getRangeAt(0);
    const host = (r.commonAncestorContainer.nodeType === Node.TEXT_NODE ? r.commonAncestorContainer.parentElement : r.commonAncestorContainer);
    if (!host?.closest?.(reader ? '#reader-text-content' : '.message .markdown, .message.user')) return null;
    const chosen = clean(selection.toString());
    if (chosen.length < 2) return null;
    return {text: chosen.slice(0, 20000), rect: r.getBoundingClientRect(), host};
  }
  function saveSelection() {
    const selection = currentSelection();
    if (!selection) { hideFloating(); return; }
    selectedText = selection.text;
    const fallbackLang = reader ? 'fi' : (selection.host.closest('[lang]')?.lang || 'en');
    requestedLanguage = detectLanguage(selectedText, fallbackLang);
    const r = selection.rect;
    if (float && r.width) {
      float.hidden = false;
      float.style.left = `${Math.min(window.innerWidth - 175, Math.max(8, r.left + (r.width / 2) - 77))}px`;
      float.style.top = `${r.bottom + 54 < window.innerHeight ? r.bottom + 8 : Math.max(8, r.top - 44)}px`;
    }
    updateVoiceWarning();
  }
  document.addEventListener('selectionchange', () => {
    clearTimeout(selectionDelay);
    selectionDelay = setTimeout(saveSelection, 80);
  });
  document.addEventListener('pointerup', () => setTimeout(saveSelection, 30));
  document.addEventListener('keyup', e => {if (e.key.startsWith('Arrow') || e.key === 'Shift') saveSelection();});
  window.addEventListener('scroll', hideFloating, true);
  document.addEventListener('pointerdown', event => {
    if (!event.target.closest('#speech-player, #speech-trigger, #speech-selection-action')) {
      hideFloating();
      selectedText = ''; // Do not read a stale selection after clicking elsewhere.
    }
  });

  async function fallbackText() {
    if (!reader) {
      const bots = [...document.querySelectorAll('.message.bot:not(.loading):not(.error)')];
      const last = bots.at(-1);
      if (!last) return null;
      const sections = [...last.querySelectorAll('.answer-section .markdown')];
      const text = sections.map(s => s.innerText || s.textContent).join('\n\n').trim();
      return {text, lang: last.lang || 'en'};
    }
    const page = Number($('reader-page')?.value) || 1;
    const existing = $('reader-text-content')?.textContent;
    if (existing && existing.trim() && !/could not|no selectable/i.test(existing)) return {text:existing, lang:'fi'};
    const response = await fetch(`/api/book/text/${page}`);
    if (!response.ok) throw Error('Unable to load the page text.');
    const data = await response.json();
    return {text: data.text || '', lang:'fi'};
  }
  async function read(preferSelection = false) {
    showPanel();
    const chosen = currentSelection()?.text || selectedText;
    let target = null;
    // A selection always takes precedence, including when pressing the main read button.
    if (chosen) target = {text: chosen, lang: detectLanguage(chosen, reader ? 'fi' : 'en')};
    else {
      notice.textContent = 'Preparing text…';
      try {target = await fallbackText();}
      catch (error) {notice.textContent = error.message; return;}
    }
    if (!target?.text?.trim()) {
      notice.textContent = reader
        ? 'This page has no extractable text. Select a different page or use Show page text.'
        : 'Select a passage in the answer, or ask KyselyTutor a question first.';
      return;
    }
    if (setSpeechText(target.text, target.lang)) doSpeak();
    hideFloating();
  }
  function play() {
    if (!supported) return;
    if (playing && paused) {
      try {synth.resume();paused = false;displayState();} catch(_){}
      return;
    }
    if (playing) return;
    if (sentences.length) { doSpeak(); return; }
    read();
  }
  trigger?.addEventListener('click', () => { read(); });
  if (float) {
    float.addEventListener('pointerdown', event => event.preventDefault());
    float.addEventListener('click', () => read(true));
  }
  playButton.addEventListener('click', play);
  pauseButton.addEventListener('click', () => { if (playing && !paused) {synth.pause();paused=true;displayState();} });
  backButton.addEventListener('click', () => jump(index - 1));
  nextButton.addEventListener('click', () => jump(index + 1));
  restartButton.addEventListener('click', () => jump(0));
  stopButton.addEventListener('click', () => {halt();index=0;displayState();});
  closeButton.addEventListener('click', () => {halt();panel.hidden=true;trigger?.setAttribute('aria-expanded','false');});
  rate.addEventListener('change', () => { if (playing) jump(index); });
  voiceList.addEventListener('change', () => {autoVoice = !voiceList.value;if (playing) jump(index);});
  window.addEventListener('pagehide', () => halt());
  document.addEventListener('kysely:pagechange', () => {
    halt(true);selectedText='';hideFloating();
    preview.textContent='Select text, or use Read aloud to listen to the current page.';
  });
  if (!supported) {
    [trigger, playButton].forEach(b => {if (b) b.disabled=true;});
  } else {
    loadVoices();
    if (synth.addEventListener) synth.addEventListener('voiceschanged', loadVoices);
    else synth.onvoiceschanged = loadVoices;
  }
  displayState();
  window.KyselySpeech = {
    detectLanguage, sentenceParts, stop:()=>halt(true),
    readText: (content, fallback = 'fi') => {
      showPanel();
      if (setSpeechText(content, fallback)) doSpeak();
      else notice.textContent = 'No text is available to read.';
    }
  };
})();
