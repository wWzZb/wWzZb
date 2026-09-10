/* HTML-first blog search: no dependencies, no remote service, no user HTML. */
(function (global) {
  'use strict';
  const normalize = value => String(value || '').normalize('NFKC').toLocaleLowerCase();
  function terms(query) {
    return [...new Set(normalize(query).trim().split(/\s+/u).filter(Boolean))].slice(0, 20);
  }
  function search(articles, query, category = '') {
    const words = terms(query);
    if (!words.length) return [];
    return articles.filter(a => !category || a.category === category).map(article => {
      const fields = {
        title: normalize(article.title),
        description: normalize(article.description),
        tags: normalize(article.tags.join(' ')),
        headings: normalize(article.headings.join(' ')),
        text: normalize(article.text)
      };
      const all = Object.values(fields).join(' ');
      if (!words.every(word => all.includes(word))) return null;
      const score = words.reduce((total, word) => total +
        (fields.title.includes(word) ? 12 : 0) +
        (fields.tags.includes(word) ? 8 : 0) +
        (fields.headings.includes(word) ? 5 : 0) +
        (fields.description.includes(word) ? 3 : 0) +
        (fields.text.includes(word) ? 1 : 0), 0);
      return {article, score};
    }).filter(Boolean).sort((a, b) => b.score - a.score || b.article.date.localeCompare(a.article.date));
  }
  function snippet(text, query, limit = 160) {
    const normalized = normalize(text);
    const positions = terms(query).map(word => normalized.indexOf(word)).filter(position => position >= 0);
    const first = positions.length ? Math.min(...positions) : 0;
    const start = Math.max(0, first - 45);
    return (start ? '…' : '') + text.slice(start, start + limit) + (text.length > start + limit ? '…' : '');
  }
  const api = {normalize, terms, search, snippet};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (typeof document === 'undefined') return;

  const form = document.getElementById('search-form');
  if (!form) return;
  const input = document.getElementById('search-input');
  const category = document.getElementById('search-category');
  const results = document.getElementById('search-results');
  const status = document.getElementById('search-status');
  let cached;
  let generation = 0;
  let timer;

  function addHighlighted(parent, text, query) {
    // RegExp metacharacters from user input are escaped before matching.
    const words = terms(query).sort((a,b) => b.length-a.length);
    if (!words.length) { parent.appendChild(document.createTextNode(text)); return; }
    const pattern = words.map(word => word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|');
    const regex = new RegExp(pattern, 'giu');
    let cursor = 0;
    for (const match of text.matchAll(regex)) {
      parent.appendChild(document.createTextNode(text.slice(cursor, match.index)));
      const mark = document.createElement('mark');
      mark.textContent = match[0]; parent.appendChild(mark);
      cursor = match.index + match[0].length;
    }
    parent.appendChild(document.createTextNode(text.slice(cursor)));
  }
  function render(matches, query) {
    const fragment = document.createDocumentFragment();
    for (const {article} of matches) {
      const row = document.createElement('article'); row.className = 'search-result';
      const meta = document.createElement('small');
      meta.textContent = `${article.categoryName} · ${article.date} · ${article.minutes} 分钟`;
      const heading = document.createElement('h2');
      const link = document.createElement('a'); link.href = article.url;
      addHighlighted(link, article.title, query); heading.appendChild(link);
      const excerpt = document.createElement('p');
      addHighlighted(excerpt, snippet(article.text, query), query);
      const tags = document.createElement('div'); tags.className = 'tags';
      article.tags.forEach(text => { const tag = document.createElement('span'); tag.className = 'tag'; tag.textContent = text; tags.appendChild(tag); });
      row.append(meta, heading, excerpt, tags); fragment.appendChild(row);
    }
    results.replaceChildren(fragment);
  }
  async function run(updateUrl = true) {
    const ticket = ++generation;
    const query = input.value.trim().slice(0, 200);
    if (updateUrl) {
      const url = new URL(location.href);
      query ? url.searchParams.set('q', query) : url.searchParams.delete('q');
      category.value ? url.searchParams.set('category', category.value) : url.searchParams.delete('category');
      history.replaceState(null, '', url);
    }
    if (!query) { results.replaceChildren(); status.textContent = '输入关键词开始搜索。'; return; }
    status.textContent = '正在搜索…';
    try {
      if (!cached) cached = fetch(results.dataset.index).then(response => {
        if (!response.ok) throw new Error('index unavailable');
        return response.json();
      }).then(data => data.articles);
      const articles = await cached;
      if (ticket !== generation) return;
      const matches = search(articles, query, category.value);
      render(matches, query);
      status.textContent = matches.length ? `找到 ${matches.length} 篇文章` : '没有找到相关内容。试试更短的关键词，或用空格分开多个关键词。';
    } catch (error) {
      cached = undefined;
      if (ticket !== generation) return;
      results.replaceChildren();
      status.textContent = '搜索暂时不可用，请重试，或通过文章列表阅读。';
    }
  }
  function restore() {
    const params = new URLSearchParams(location.search);
    input.value = (params.get('q') || '').slice(0, 200);
    category.value = params.get('category') || '';
    run(false);
  }
  form.addEventListener('submit', event => { event.preventDefault(); clearTimeout(timer); run(); });
  input.addEventListener('input', () => { clearTimeout(timer); generation++; timer = setTimeout(run, 140); });
  category.addEventListener('change', () => { clearTimeout(timer); run(); });
  global.addEventListener('popstate', restore);
  restore();
})(typeof window === 'undefined' ? globalThis : window);
