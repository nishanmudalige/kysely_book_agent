(() => {
  'use strict';
  const messages = document.getElementById('messages');
  const form = document.getElementById('ask-form');
  const questionInput = document.getElementById('question');
  const sendButton = document.getElementById('send');
  const language = document.getElementById('language');
  const translationMode = document.getElementById('translation-mode');
  const password = document.getElementById('password');
  const clear = document.getElementById('clear');
  const welcome = document.getElementById('welcome');
  const history = [];
  const tocToggle = document.getElementById('toc-toggle');
  const tocLabel = document.getElementById('toc-toggle-label');
  const tocPanel = document.getElementById('contents-panel');
  const grid = document.getElementById('main-grid');
  const TOC_STORAGE_KEY = 'kyselytutor_contents_open_v2';
  const themeToggle = document.getElementById('theme-toggle');
  const themeLabel = document.getElementById('theme-toggle-label');
  const THEME_STORAGE_KEY = 'kyselytutor_theme_v1';

  function applyTheme(mode, persist = true) {
    const dark = mode === 'dark';
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
    if (themeToggle) {
      themeToggle.setAttribute('aria-pressed', String(dark));
      const description = dark ? 'Switch to light mode' : 'Switch to dark mode';
      themeToggle.setAttribute('aria-label', description);
      themeToggle.title = description;
    }
    if (themeLabel) themeLabel.textContent = dark ? 'Light mode' : 'Dark mode';
    const themeMeta = document.querySelector('meta[name="theme-color"]');
    if (themeMeta) themeMeta.content = dark ? '#10171d' : '#ffffff';
    if (persist) {
      try { localStorage.setItem(THEME_STORAGE_KEY, dark ? 'dark' : 'light'); } catch (_) {}
    }
  }
  applyTheme(document.documentElement.dataset.theme, false);
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      applyTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark');
    });
  }


  function setContentsVisible(open, persist = true) {
    if (!tocPanel || !tocToggle || !grid) return;
    tocPanel.hidden = !open;
    grid.classList.toggle('contents-hidden', !open);
    tocToggle.setAttribute('aria-expanded', String(open));
    if (tocLabel) tocLabel.textContent = open ? 'Hide contents' : 'Show contents';
    if (persist) {
      try { localStorage.setItem(TOC_STORAGE_KEY, open ? 'yes' : 'no'); } catch (_) {}
    }
  }
  if (tocToggle && tocPanel) {
    let saved = null;
    try { saved = localStorage.getItem(TOC_STORAGE_KEY); } catch (_) {}
    const defaultOpen = !window.matchMedia('(max-width: 760px)').matches;
    setContentsVisible(saved === null ? defaultOpen : saved === 'yes', false);
    tocToggle.addEventListener('click', () => {
      setContentsVisible(tocPanel.hidden);
    });
  }

  const CATEGORY = {
    book: {en: 'From the textbook', fi: 'Kirjasta', css: ''},
    mixed: {en: 'From the textbook', fi: 'Kirjasta', css: ''},
    related_outside: {en: 'Related — outside the book', fi: 'Aiheeseen liittyvä — ei kirjasta', css: 'outside'},
    out_of_scope: {en: 'Outside the scope of this book', fi: 'Kirjan aihepiirin ulkopuolella', css: 'scope'}
  };

  function isFinnish(q) {
    if (language.value === 'fi') return true;
    if (language.value === 'en' || translationMode.value === 'en') return false;
    return /[äöå]/i.test(q) || /\b(mitä|miten|miksi|missä|milloin|selitä|kerro|voiko|mikä|onko|käännä|kirjassa|sivu)\b/i.test(q);
  }
  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }
  function scrollDown() { messages.scrollTop = messages.scrollHeight; }
  function renderMarkdown(text, sources) {
    // Server has already validated source-page numbers. Convert only known tags.
    const byPage = Object.fromEntries((sources || []).map(s => [String(s.page), s]));
    const sourceLinks = text.replace(/\[P(\d{1,3})\]/g, (full, n) => {
      return byPage[n] ? `[p. ${n}](${byPage[n].url})` : full;
    });
    if (!window.marked || !window.DOMPurify) {
      return el('p', '', sourceLinks);
    }
    const wrapper = el('div', 'markdown');
    wrapper.innerHTML = DOMPurify.sanitize(marked.parse(sourceLinks), {USE_PROFILES: {html: true}});
    wrapper.querySelectorAll('a').forEach(a => { a.target = '_blank'; a.rel = 'noopener noreferrer'; });
    return wrapper;
  }
  function addMessage(role, text) {
    if (welcome) welcome.style.display = 'none';
    const msg = el('article', `message ${role}`);
    msg.textContent = text;
    messages.appendChild(msg);
    scrollDown();
    return msg;
  }
  function addSection(parent, type, text, fi, sources) {
    if (!text || !text.trim()) return;
    const section = el('section', 'answer-section');
    const tag = CATEGORY[type];
    section.appendChild(el('div', `provenance ${tag.css}`, fi ? tag.fi : tag.en));
    if (type === 'related_outside' || type === 'mixed') {
      section.appendChild(el('p', 'provenance-note', fi
        ? 'Tämä lisätieto ei perustu oppikirjan sisältöön, vaan on tekoälyn yleistietoa.'
        : 'This information is not from the textbook; it is general AI knowledge, not a live web search.'));
    }
    section.appendChild(renderMarkdown(text, sources));
    parent.appendChild(section);
  }
  function renderAnswer(msg, data, fi) {
    msg.textContent = '';
    const result = data.category;
    if (data.book_answer) addSection(msg, 'book', data.book_answer, fi, data.sources);
    if (data.outside_answer) {
      const type = result === 'out_of_scope' ? 'out_of_scope' : 'related_outside';
      addSection(msg, type, data.outside_answer, fi, []);
    }
    if (data.sources && data.sources.length) {
      const container = el('div', 'sources');
      container.appendChild(el('span', 'sources-title', fi ? 'Kirjan sivut:' : 'Textbook pages:'));
      data.sources.forEach(s => {
        const a = el('a', 'page-link', `${fi ? 's.' : 'p.'} ${s.page} ↗`);
        a.href = s.url;
        a.title = (s.section || '') + (s.has_highlights ? (fi ? ' · Korostaa vastausta tukevan tekstin' : ' · Highlights supporting passages') : '');
        a.target = '_blank'; a.rel = 'noopener noreferrer';
        container.appendChild(a);
      });
      if (data.sources.some(s => s.has_highlights)) {
        container.appendChild(el('small', 'sources-hint', fi
          ? 'Oranssi korostus näyttää vastausta tukevan alkuperäisen tekstin. Korostuksen voi poistaa lukijassa.'
          : 'Orange highlights show supporting original text. You can switch highlights off in the reader.'));
      }
      msg.appendChild(container);
    }
    if (window.MathJax && window.MathJax.typesetPromise) {
      window.MathJax.typesetPromise([msg]).catch(() => {});
    }
    scrollDown();
  }
  async function sendQuestion() {
    const question = questionInput.value.trim();
    if (!question) return;
    if (password && !password.value.trim()) { password.focus(); return; }
    const fi = isFinnish(question);
    addMessage('user', question);
    questionInput.value = '';
    sendButton.disabled = true;
    sendButton.querySelector('span').textContent = fi ? 'Haetaan…' : 'Searching…';
    const placeholder = addMessage('bot loading', fi ? 'Etsin kirjasta ja muodostan vastausta…' : 'Searching the book and preparing an answer…');
    try {
      const response = await fetch('/api/ask', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({question, language: language.value,
          translation_mode: translationMode.value, password: password ? password.value : '',
          history: history.slice(-12)})
      });
      let data;
      try { data = await response.json(); } catch (_) { throw Error('The server did not return valid JSON.'); }
      if (!response.ok) throw Error(data.error || `Request failed: HTTP ${response.status}`);
      placeholder.className = 'message bot';
      renderAnswer(placeholder, data, fi);
      const answer = [data.book_answer, data.outside_answer].filter(Boolean).join('\n\n');
      history.push({role: 'user', content: question}, {role: 'assistant', content: answer});
    } catch (error) {
      placeholder.className = 'message bot error';
      placeholder.textContent = error.message;
    } finally {
      sendButton.disabled = false;
      sendButton.querySelector('span').textContent = 'Send';
      questionInput.focus();
    }
  }

  form.addEventListener('submit', event => { event.preventDefault(); sendQuestion(); });
  questionInput.addEventListener('keydown', event => {
    if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
      event.preventDefault(); form.requestSubmit();
    }
  });
  translationMode.addEventListener('change', () => {
    if (translationMode.value === 'en') language.value = 'en';
    if (translationMode.value === 'fi') language.value = 'fi';
  });
  clear.addEventListener('click', () => {
    history.length = 0;
    messages.querySelectorAll('.message').forEach(e => e.remove());
    if (welcome) welcome.style.display = '';
    questionInput.value = '';
    scrollDown(); questionInput.focus();
  });
  // A larger bilingual question bank. Each reload chooses exactly 2 FI + 2 EN.
  // Avoid showing any of the previous visit's examples when storage is available.
  const SAMPLE_KEY = 'kyselytutor_previous_samples_v1';
  const SAMPLE_QUESTIONS = {
    fi: [
      {id:'fi-validity', text:'Miten validiteetti ja reliabiliteetti eroavat toisistaan?', question:'Selitä validiteetin ja reliabiliteetin ero kirjan mukaan ja viittaa sivuihin.'},
      {id:'fi-factor', text:'Miten faktorianalyysiä käytetään kyselyaineiston tiivistämisessä?', question:'Miten faktorianalyysi auttaa kyselyaineiston tiivistämisessä? Viittaa kirjan sivuihin.'},
      {id:'fi-open', text:'Mikä ero on avoimilla ja suljetuilla kysymyksillä?', question:'Selitä avoimien ja suljettujen osioiden erot kirjassa ja anna sivuviitteet.'},
      {id:'fi-sample', text:'Mitä eroa on perusjoukolla ja otoksella?', question:'Mitä kirjassa sanotaan perusjoukosta ja otoksesta? Viittaa olennaisiin sivuihin.'},
      {id:'fi-likert', text:'Mitä mittauksen taso tarkoittaa kyselytutkimuksessa?', question:'Selitä mittauksen taso ja luokittelu- sekä järjestysasteikon erot kirjan perusteella.'},
      {id:'fi-operate', text:'Miksi käsitteet pitää operationalisoida?', question:'Selitä käsitteiden operationalisointi kirjan luvun 2.1 esimerkin avulla. Viittaa sivuihin.'},
      {id:'fi-scale', text:'Miten summamuuttuja muodostetaan?', question:'Miten summamuuttujia käytetään mitta-asteikon muodostamisessa? Etsi kohdat kirjasta.'},
      {id:'fi-regression', text:'Miten kirjassa tulkitaan regressioanalyysiä?', question:'Mitä kirjassa kerrotaan regressioanalyysin oletuksista ja tulkinnasta? Ilmoita sivut.'},
      {id:'fi-missing', text:'Miksi aineisto pitää esikäsitellä?', question:'Miten kirjassa perustellaan aineiston esikäsittelyn tarve? Etsi olennaiset sivut.'},
      {id:'fi-clustering', text:'Mitä medoidiryhmittely tarkoittaa?', question:'Selitä medoidiryhmittely kirjan luvun 6 mukaisesti ja viittaa sivuihin.'},
      {id:'fi-correspondence', text:'Mihin korrespondenssianalyysiä käytetään?', question:'Miten korrespondenssianalyysi kuvataan kirjan luvussa 7? Anna sivuviitteet.'},
      {id:'fi-diagnostics', text:'Miksi regressiodiagnostiikka on tärkeää?', question:'Selitä regressiodiagnostiikan merkitys ja jäännösvaihtelu kirjan mukaan.'}
    ],
    en: [
      {id:'en-items', text:'What is the difference between open and closed survey questions?', question:'Explain the difference between open-ended and closed-ended questionnaire items in the textbook, with page citations.'},
      {id:'en-translate', text:'Translate the explanation of operationalisation on page 18.', question:'Translate the textbook explanation of operationalising concepts on page 18 into English, citing the source.', translation:'en'},
      {id:'en-reliability', text:'How does the book distinguish validity from reliability?', question:'How does Vehkalahti distinguish validity and reliability? Use textbook page citations.'},
      {id:'en-dimensions', text:'What are dimensions and items in a questionnaire?', question:'Explain the relationship between dimensions, questionnaire items, and scales as presented in Chapter 2.'},
      {id:'en-sampling', text:'What do population and sample mean in survey research?', question:'What is the difference between a survey population and a sample according to the book?'},
      {id:'en-factor', text:'Why is factor analysis useful for survey data?', question:'Explain the purpose of factor analysis in summarising survey data, referring to the book.'},
      {id:'en-composite', text:'How are composite scores used in measurement scales?', question:'Explain how composite scores are used in the measurement-scale chapter. Give page references.'},
      {id:'en-regression', text:'What assumptions are discussed for regression analysis?', question:'Summarise the regression assumptions described in Chapter 5, with PDF page references.'},
      {id:'en-clean', text:'How should questionnaire data be prepared for analysis?', question:'What steps of data preparation does Chapter 3 discuss? Refer to the original pages.'},
      {id:'en-medoid', text:'What is medoid clustering?', question:'Explain medoid clustering using the textbook discussion in Chapter 6, with citations.'},
      {id:'en-discriminant', text:'What is discriminant analysis used for?', question:'Describe the role of discriminant analysis in visualising groups, based on Chapter 7.'},
      {id:'en-translate-reliability', text:'Translate the reliability explanation on page 41.', question:'Translate the original Finnish discussion of validity and reliability on page 41 into English.', translation:'en'}
    ]
  };
  function randomSample(pool, previousIds, count) {
    const fresh = pool.filter(item => !previousIds.includes(item.id));
    const candidates = fresh.length >= count ? fresh : pool;
    const shuffled = candidates.slice();
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled.slice(0, count);
  }
  function populateSuggestions() {
    const region = document.getElementById('suggestions');
    if (!region) return;
    let last = [];
    try {last = JSON.parse(localStorage.getItem(SAMPLE_KEY) || '[]');} catch (_) {}
    if (!Array.isArray(last)) last = [];
    const selected = [...randomSample(SAMPLE_QUESTIONS.fi, last, 2),
                      ...randomSample(SAMPLE_QUESTIONS.en, last, 2)];
    region.replaceChildren();
    selected.forEach(item => {
      const locale = item.id.slice(0, 2);
      const button = el('button', 'suggestion');
      button.type = 'button';
      button.dataset.question = item.question;
      button.dataset.language = locale;
      button.dataset.translation = item.translation || 'none';
      button.append(el('span', 'suggestion-lang', locale.toUpperCase()),
                    el('span', 'suggestion-copy', item.text),
                    el('span', 'suggestion-arrow', '↗'));
      region.appendChild(button);
    });
    try {localStorage.setItem(SAMPLE_KEY, JSON.stringify(selected.map(x => x.id)));} catch (_) {}
  }
  populateSuggestions();
  document.getElementById('suggestions')?.addEventListener('click', event => {
    const button = event.target.closest('button.suggestion');
    if (!button) return;
    questionInput.value = button.dataset.question || '';
    translationMode.value = button.dataset.translation || 'none';
    language.value = button.dataset.language || 'auto';
    // One-click questions respect the access-code prompt.
    if (password && !password.value.trim()) password.focus();
    else if (!sendButton.disabled) form.requestSubmit();
    else questionInput.focus();
  });
})();
