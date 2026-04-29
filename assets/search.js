(() => {
  const form = document.querySelector('.site-search');
  const input = document.querySelector('#search-query');
  const results = document.querySelector('#search-results');
  const summary = document.querySelector('#search-summary');
  if (!form || !input || !results || !summary) return;

  const esc = (value) => String(value || '').replace(/[&<>"]/g, (ch) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[ch]));
  const params = new URLSearchParams(window.location.search);
  const initial = params.get('q') || '';
  input.value = initial;

  let indexItems = [];
  const normalize = (value) => String(value || '').toLowerCase().replace(/\s+/g, ' ').trim();
  const tokensOf = (query) => normalize(query).split(' ').filter(Boolean).slice(0, 8);
  const scoreItem = (item, tokens) => {
    const title = normalize(item.title);
    const desc = normalize(item.description);
    const tags = normalize((item.tags || []).join(' '));
    const text = normalize(item.text);
    let score = 0;
    for (const token of tokens) {
      if (title.includes(token)) score += 9;
      if (tags.includes(token)) score += 6;
      if (desc.includes(token)) score += 4;
      if (text.includes(token)) score += 1;
    }
    if (item.section === 'deals') score += 0.5;
    const views = Number(item.views || 0);
    if (views > 0) score += Math.min(3, Math.log10(views + 1));
    return score;
  };
  const render = (query) => {
    const tokens = tokensOf(query);
    if (!tokens.length) {
      results.innerHTML = '';
      summary.textContent = '검색어를 입력하면 관련 글을 보여줍니다.';
      return;
    }
    const matches = indexItems.map((item) => ({item, score: scoreItem(item, tokens)}))
      .filter((x) => x.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, 24);
    summary.textContent = matches.length ? `${matches.length}개 결과를 찾았습니다.` : '관련 결과가 아직 없습니다. 다른 키워드로 검색해보세요.';
    results.innerHTML = matches.map(({item}) => {
      const meta = [item.category, item.item_count_hint, item.price_hint].filter(Boolean).slice(0, 3).join(' · ');
      const image = item.image_url ? `<img src="${esc(item.image_url)}" alt="${esc(item.title)}" loading="lazy" decoding="async" />` : '';
      return `<article class="list-card search-result-card">${image}<div class="card-meta"><span class="tag">${esc(item.section === 'deals' ? '구매가이드' : item.section === 'radar' ? '동네 레이더' : '사이트')}</span></div><h2><a href="${esc(item.path)}">${esc(item.title)}</a></h2><p>${esc(item.description || '')}</p><p class="muted">${esc(meta)}</p><a class="text-link" href="${esc(item.path)}">열기 →</a></article>`;
    }).join('');
  };
  const updateUrl = (query) => {
    const url = new URL(window.location.href);
    if (query) url.searchParams.set('q', query); else url.searchParams.delete('q');
    window.history.replaceState({}, '', url);
  };

  fetch('/data/search-index.json', {cache: 'no-store'})
    .then((res) => res.ok ? res.json() : Promise.reject(new Error('search index missing')))
    .then((data) => {
      indexItems = Array.isArray(data.items) ? data.items : [];
      render(input.value);
    })
    .catch(() => {
      summary.textContent = '검색 데이터를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.';
    });

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const query = input.value.trim();
    updateUrl(query);
    render(query);
  });
  input.addEventListener('input', () => render(input.value));
})();
