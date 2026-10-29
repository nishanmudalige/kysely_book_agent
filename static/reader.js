/* A self-contained HTML/PNG book reader. No browser PDF support or CDN required. */
(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const total = Number(document.body.dataset.pageCount) || 223;
  const PAGE_WIDTH = 425.197;  // PDF points; all pages of the 2019 edition share this size.
  const pageInput = $('reader-page');
  const image = $('reader-image');
  const frame = $('reader-image-frame');
  const scrollArea = $('reader-scroller');
  const status = $('reader-status');
  const sidebar = $('reader-sidebar');
  const layout = $('reader-layout');
  const sidebarToggle = $('reader-contents-toggle');
  const searchInput = $('reader-search');
  const resultsSection = $('reader-results');
  const resultsList = $('reader-results-list');
  const chaptersSection = $('reader-chapters');
  const textView = $('reader-page-text');
  const textButton = $('reader-text-toggle');
  const textContent = $('reader-text-content');
  const highlights = $('reader-highlights');
  const THEME_KEY = 'kyselytutor_theme_v1';
  const CONTENTS_KEY = 'kyselytutor_contents_open_v2';
  let currentPage = 1;
  let zoom = null;      // null means fit to available width
  let activeQuery = '';
  let generation = 0;
  let pageText = '';
  let textGeneration = 0;

  function saved(key) {try { return localStorage.getItem(key); } catch (_) {return null;} }
  function remember(key, val) {try {localStorage.setItem(key, val);} catch (_) {}}
  function applyTheme(mode, persist = true) {
    const dark = mode === 'dark';
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
    $('reader-theme').setAttribute('aria-pressed', String(dark));
    $('reader-theme').setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
    $('reader-theme-label').textContent = dark ? 'Light mode' : 'Dark mode';
    document.querySelector('meta[name="theme-color"]').content = dark ? '#10171d' : '#ffffff';
    if (persist) remember(THEME_KEY, dark ? 'dark' : 'light');
  }
  applyTheme(document.documentElement.dataset.theme, false);
  $('reader-theme').addEventListener('click', () => applyTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'));

  function setSidebar(open, persist = true) {
    sidebar.hidden = !open;
    layout.classList.toggle('no-sidebar', !open);
    sidebarToggle.setAttribute('aria-expanded', String(open));
    sidebarToggle.querySelector('span').textContent = open ? 'Hide contents' : 'Show contents';
    if (persist) remember(CONTENTS_KEY, open ? 'yes' : 'no');
    if (zoom === null) requestAnimationFrame(resizePage);
  }
  const initialContents = saved(CONTENTS_KEY);
  setSidebar(initialContents === null ? window.innerWidth > 740 : initialContents === 'yes', false);
  sidebarToggle.addEventListener('click', () => setSidebar(sidebar.hidden));

  function fitScale() {
    const available = Math.max(245, scrollArea.clientWidth - (window.innerWidth < 740 ? 30 : 65));
    return available / PAGE_WIDTH;
  }
  function displayZoom() {
    return zoom === null ? fitScale() : zoom;
  }
  function resizePage() {
    const value = Math.max(.55, Math.min(3.85, displayZoom()));
    frame.style.width = Math.round(PAGE_WIDTH * value) + 'px';
    $('reader-zoom-level').textContent = zoom === null ? 'Fit width' : Math.round(value * 100) + '%';
  }
  function setZoom(target) {
    zoom = target === null ? null : Math.max(.6, Math.min(3.85, target));
    resizePage();
    // A higher-resolution PNG is requested only when zoom requires it.
    const resolution = displayZoom() > 2.55 ? 3.5 : 2.5;
    const url = `/api/book/page/${currentPage}.png?scale=${resolution}`;
    if (image.getAttribute('src') !== url) image.src = url;
  }
  $('reader-zoom-in').addEventListener('click', () => setZoom(displayZoom() * 1.22));
  $('reader-zoom-out').addEventListener('click', () => setZoom(displayZoom() / 1.22));
  $('reader-fit').addEventListener('click', () => setZoom(null));
  window.addEventListener('resize', () => {if (zoom === null) resizePage();});

  function getUrlPage() {
    const hash = location.hash.match(/(?:^#|&)page=(\d{1,4})/i);
    if (hash) return Number(hash[1]); // Handles old /book.pdf#page=NN links.
    return Number(new URLSearchParams(location.search).get('page')) || 1;
  }
  function bounded(page) {return Math.max(1, Math.min(total, Math.floor(Number(page) || 1)));}

  function updateChapterSelection() {
    document.querySelectorAll('.reader-chapter').forEach(link => {
      const matches = Number(link.dataset.page) === currentPage;
      link.classList.toggle('active', matches);
      if (matches) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });
  }
  async function showHighlights(page, token) {
    highlights.replaceChildren();
    if (!activeQuery) return;
    try {
      const response = await fetch(`/api/book/highlights/${page}?q=${encodeURIComponent(activeQuery)}`);
      if (!response.ok) return;
      const data = await response.json();
      if (token !== generation || page !== currentPage) return;
      (data.boxes || []).forEach(rect => {
        const el = document.createElement('span');
        el.className = 'reader-highlight';
        el.style.left = `${rect.x}%`;
        el.style.top = `${rect.y}%`;
        el.style.width = `${rect.w}%`;
        el.style.height = `${rect.h}%`;
        highlights.appendChild(el);
      });
    } catch (_) {/* An unavailable highlight should not prevent reading. */}
  }
  async function loadPageText(page, token) {
    try {
      const response = await fetch(`/api/book/text/${page}`);
      if (!response.ok) throw Error('Could not load text.');
      const data = await response.json();
      if (token !== textGeneration || page !== currentPage) return;
      pageText = data.text || '';
      textContent.textContent = pageText || 'No selectable text could be extracted from this page.';
    } catch (e) {
      if (token === textGeneration) textContent.textContent = e.message;
    }
  }
  function goToPage(page, updateHistory = true) {
    const target = bounded(page);
    currentPage = target;
    const token = ++generation;
    pageInput.value = String(target);
    $('reader-prev').disabled = target === 1;
    $('reader-next').disabled = target === total;
    status.textContent = `Page ${target} of ${total} · Sivu ${target}/${total}`;
    image.alt = `Original textbook page ${target} of ${total}, authored by Kimmo Vehkalahti`;
    frame.classList.add('loading');
    image.onload = () => {if (token === generation) frame.classList.remove('loading');};
    image.onerror = () => {if (token === generation) {frame.classList.remove('loading');status.textContent = `Page ${target} could not be loaded. Try refreshing.`;}};
    const resolution = displayZoom() > 2.55 ? 3.5 : 2.5;
    image.src = `/api/book/page/${target}.png?scale=${resolution}`;
    resizePage();
    scrollArea.scrollTo({top: 0, left: 0});
    showHighlights(target, token);
    pageText = '';
    textContent.textContent = '';
    const tt = ++textGeneration;
    if (!textView.hidden) loadPageText(target, tt);
    updateChapterSelection();
    if (updateHistory) history.pushState({page: target}, '', `/reader?page=${target}`);
  }
  $('reader-prev').addEventListener('click', () => goToPage(currentPage - 1));
  $('reader-next').addEventListener('click', () => goToPage(currentPage + 1));
  pageInput.addEventListener('change', () => goToPage(pageInput.value));
  pageInput.addEventListener('keydown', event => {if (event.key === 'Enter') {event.preventDefault();pageInput.blur();}});
  window.addEventListener('popstate', () => goToPage(getUrlPage(), false));
  window.addEventListener('hashchange', () => {goToPage(getUrlPage(), false);history.replaceState({page:currentPage}, '', `/reader?page=${currentPage}`);});
  document.querySelectorAll('.reader-chapter').forEach(link => link.addEventListener('click', event => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || event.button !== 0) return;
    event.preventDefault();
    goToPage(link.dataset.page);
    if (window.innerWidth <= 740) setSidebar(false);
  }));
  document.addEventListener('keydown', event => {
    if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey || /input|textarea|select/i.test(document.activeElement?.tagName || '')) return;
    if (event.key === 'ArrowRight') {event.preventDefault();goToPage(currentPage + 1);}
    if (event.key === 'ArrowLeft') {event.preventDefault();goToPage(currentPage - 1);}
  });

  $('reader-search-form').addEventListener('submit', async event => {
    event.preventDefault();
    const query = searchInput.value.trim();
    if (query.length < 2) {searchInput.focus();return;}
    activeQuery = query;
    setSidebar(true);
    chaptersSection.hidden = true;
    resultsSection.hidden = false;
    $('reader-results-count').textContent = 'Searching the original book…';
    resultsList.replaceChildren();
    try {
      const response = await fetch(`/api/book/search?q=${encodeURIComponent(query)}`);
      if (!response.ok) throw Error('Search unavailable.');
      const data = await response.json();
      $('reader-results-count').textContent = data.count ? `${data.count} matching page(s) · ${Math.min(data.results.length, 70)} shown` : 'No results found. Try a different term.';
      (data.results || []).forEach(result => {
        const btn = document.createElement('button');
        btn.type = 'button'; btn.className = 'reader-result';
        const page = document.createElement('strong');page.textContent = `Page ${result.page} · Sivu ${result.page}`;
        const snippet = document.createElement('span');snippet.textContent = result.snippet;
        btn.append(page, snippet);
        btn.addEventListener('click', () => {goToPage(result.page);if (window.innerWidth <= 740) setSidebar(false);});
        resultsList.appendChild(btn);
      });
      showHighlights(currentPage, generation);
    } catch (error) {$('reader-results-count').textContent = error.message;}
  });
  $('reader-results-close').addEventListener('click', () => {
    resultsSection.hidden = true;
    chaptersSection.hidden = false;
    activeQuery = '';
    highlights.replaceChildren();
  });
  textButton.addEventListener('click', () => {
    const show = textView.hidden;
    textView.hidden = !show;
    textButton.setAttribute('aria-pressed', String(show));
    textButton.textContent = show ? 'Hide page text' : 'Show page text';
    if (show && !pageText) loadPageText(currentPage, ++textGeneration);
  });
  async function copyValue(text, button, success) {
    try {
      if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(text);
      else {
        const field = document.createElement('textarea'); field.value = text;
        document.body.appendChild(field);field.select();
        if (!document.execCommand('copy')) throw Error('Copy unavailable.');
        field.remove();
      }
      const original = button.textContent;
      button.textContent = success;
      setTimeout(() => {button.textContent = original;}, 1600);
    } catch (_) {status.textContent = 'Copy unavailable; select the address or page text manually.';}
  }
  $('reader-copy').addEventListener('click', () => copyValue(`${location.origin}/reader?page=${currentPage}`, $('reader-copy'), 'Copied!'));
  $('reader-copy-text').addEventListener('click', async () => {
    if (!pageText) return;
    await copyValue(pageText, $('reader-copy-text'), 'Copied!');
  });
  const start = bounded(getUrlPage());
  history.replaceState({page:start}, '', `/reader?page=${start}`);
  goToPage(start, false);
})();
