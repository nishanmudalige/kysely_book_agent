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
      return byPage[n] ? `[p. ${n}](/book.pdf#page=${n})` : full;
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
        a.title = s.section || '';
        a.target = '_blank'; a.rel = 'noopener noreferrer';
        container.appendChild(a);
      });
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
  document.querySelectorAll('.suggestion').forEach(button => {
    button.addEventListener('click', () => {
      questionInput.value = button.dataset.question || '';
      if (button.dataset.translation) {
        translationMode.value = button.dataset.translation;
        language.value = button.dataset.translation;
      } else {
        translationMode.value = 'none'; language.value = 'auto';
      }
      questionInput.focus();
    });
  });
})();
