(() => {
  const root = document.querySelector('[data-seoul-density-tool-root]');
  if (!root) return;
  const stationSelect = root.querySelector('#tool-station');
  const compareSelect = root.querySelector('#tool-compare-station');
  const industrySelect = root.querySelector('#tool-industry');
  const purposeSelect = root.querySelector('#tool-purpose');
  const mapLayerLabel = root.querySelector('[data-map-layer-label]');
  const scoreRoot = root.querySelector('[data-density-result]');
  const stationMeta = root.querySelector('[data-station-meta]');
  const stationTitle = root.querySelector('[data-station-title]');
  const gradeEl = root.querySelector('[data-risk-grade]');
  const summaryEl = root.querySelector('[data-risk-summary]');
  const countEl = root.querySelector('[data-density-count]');
  const countLabelEl = root.querySelector('[data-density-label]');
  const commercialDensityEl = root.querySelector('[data-commercial-density]');
  const popDensityEl = root.querySelector('[data-pop-density]');
  const popLabelEl = root.querySelector('[data-pop-label]');
  const riskListEl = root.querySelector('[data-risk-list]');
  const barsEl = root.querySelector('[data-density-bars]');
  const linksEl = root.querySelector('[data-recommend-links]');
  const comparePanel = root.querySelector('[data-compare-panel]');
  const compareTitleEl = root.querySelector('[data-compare-title]');
  const compareMetricsEl = root.querySelector('[data-compare-metrics]');
  const compareNoteEl = root.querySelector('[data-compare-note]');
  const sourceNoteEl = root.querySelector('[data-source-note]');
  const layerButtons = Array.from(root.querySelectorAll('[data-density-layer]'));
  const stationButtons = Array.from(root.querySelectorAll('[data-station-map]'));
  if (!stationSelect || !compareSelect || !industrySelect || !purposeSelect || !stationTitle || !riskListEl || !barsEl) return;

  const esc = (value) => String(value || '').replace(/[&<>"]/g, (ch) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[ch]));
  const link = (href, label) => `<a href="${href}">${esc(label)}</a>`;
  const categoryOrder = ['cafe', 'food', 'convenience', 'beauty', 'clinic', 'academy', 'retail'];
  let payload = null;

  const categoryLabel = (key) => (payload?.categories?.[key] || ({population: '인구밀도'}[key]) || key);
  const maxFor = (key) => {
    if (!payload?.stations?.length) return 1;
    if (key === 'population') return 100;
    return Math.max(1, ...payload.stations.map((station) => Number(station.counts?.[key] || 0)));
  };
  const stationById = (id) => payload?.stations?.find((station) => station.id === id) || payload?.stations?.[0];
  const valueFor = (station, industry) => industry === 'population'
    ? Number(station.population_density_index || 0)
    : Number(station.counts?.[industry] || 0);
  const signed = (value) => `${value > 0 ? '+' : ''}${value}`;
  const compareStationFor = (station) => {
    let compare = stationById(compareSelect.value);
    if (!compare || compare.id === station.id) {
      compare = payload.stations.find((candidate) => candidate.id !== station.id) || station;
      compareSelect.value = compare.id;
    }
    return compare;
  };
  const renderCompare = (station, compare, industry) => {
    if (!comparePanel || !compareTitleEl || !compareMetricsEl || !compareNoteEl) return;
    const selectedDelta = valueFor(station, industry) - valueFor(compare, industry);
    const popDelta = Number(station.population_density_index || 0) - Number(compare.population_density_index || 0);
    const rentDelta = Number(station.rent_pressure_index || 0) - Number(compare.rent_pressure_index || 0);
    const metric = (label, value) => `<div class="${value > 0 ? 'compare-up' : value < 0 ? 'compare-down' : 'compare-same'}"><span>${esc(label)}</span><strong>${signed(value)}</strong></div>`;
    compareTitleEl.textContent = `${station.name} ↔ ${compare.name}`;
    compareMetricsEl.innerHTML = [metric(categoryLabel(industry), selectedDelta), metric('인구밀도', popDelta), metric('임대압력', rentDelta)].join('');
    compareNoteEl.textContent = rentDelta > 7
      ? `${station.name}은 ${compare.name}보다 임대 압력이 높습니다. 권리금·고정비 회수 기간을 더 보수적으로 잡으세요.`
      : rentDelta < -7
        ? `${station.name}은 ${compare.name}보다 임대 압력이 낮습니다. 대신 목적 방문 이유와 반복 동선을 확인하세요.`
        : `${station.name}과 ${compare.name}은 임대 압력이 비슷합니다. 업종 밀도와 생활 동선 차이를 우선 보세요.`;
  };
  const gradeFor = (station, industry) => {
    const density = industry === 'population' ? Number(station.population_density_index || 0) : Number(station.commercial_density_index || 0);
    const rent = Number(station.rent_pressure_index || 0);
    const selectedCount = industry === 'population' ? density : Number(station.counts?.[industry] || 0);
    let score = 86 - Math.round(density * .18) - Math.round(rent * .12);
    if (selectedCount > maxFor(industry) * .72) score -= 13;
    if (selectedCount < maxFor(industry) * .16) score -= 8;
    score = Math.max(28, Math.min(92, score));
    const grade = score >= 74 ? 'good' : score >= 55 ? 'warn' : 'hold';
    return {score, grade, label: grade === 'good' ? '진행' : grade === 'warn' ? '주의' : '보류'};
  };
  const questionsFor = (station, industry, purpose) => {
    const label = categoryLabel(industry);
    if (purpose === 'home') {
      return [
        `${station.name} 주변 인구밀도가 ${station.population_density_label}입니다. 밤 10시 이후 귀가 동선과 소음 방향을 직접 걸어봤나요?`,
        `반경 ${station.radius_m || 650}m 생활 POI가 ${station.total_poi_count || 0}개 잡힙니다. 장보기·병원·운동 동선이 실제 생활 리듬과 맞나요?`,
        `관리비·교통비까지 합친 월 고정비를 같은 예산의 다른 역 후보와 비교했나요?`
      ];
    }
    return [
      industry === 'population'
        ? `인구밀도 지수 ${station.population_density_index || 0}입니다. 거주 기반 업종인지, 출퇴근 유동 기반 업종인지 먼저 나눴나요?`
        : `${label} 기준 주변 매장 ${(station.counts?.[industry] || 0)}개입니다. 같은 고객을 나눠 갖는 직접 경쟁인지 분리했나요?`,
      `${station.name}은 임대 압력 지수 ${station.rent_pressure_index || 0}입니다. 임대료·관리비·권리금 회수 기간을 보수적으로 다시 계산했나요?`,
      `평일 점심·퇴근·주말 3번을 나눠 유입을 세고, 앵커시설 없이도 재방문 이유가 있는지 확인했나요?`
    ];
  };
  const updateMapHeat = (industry) => {
    const max = maxFor(industry);
    stationButtons.forEach((button) => {
      const station = stationById(button.dataset.stationMap);
      if (!station) return;
      const raw = industry === 'population' ? Number(station.population_density_index || 0) : Number(station.counts?.[industry] || 0);
      const heat = Math.max(.18, Math.min(1, raw / max));
      button.style.setProperty('--heat', heat.toFixed(2));
      const small = button.querySelector('small');
      if (small) small.textContent = industry === 'population' ? `${station.population_density_index}` : `${raw}`;
      button.setAttribute('aria-pressed', station.id === stationSelect.value ? 'true' : 'false');
    });
    layerButtons.forEach((button) => button.setAttribute('aria-pressed', button.dataset.densityLayer === industry ? 'true' : 'false'));
    if (mapLayerLabel) mapLayerLabel.textContent = industry === 'population' ? '인구밀도' : `${categoryLabel(industry)} 밀도`;
  };
  const renderBars = (station) => {
    const maxes = Object.fromEntries(categoryOrder.map((key) => [key, maxFor(key)]));
    barsEl.innerHTML = categoryOrder.slice(0, 6).map((key) => {
      const value = Number(station.counts?.[key] || 0);
      const pct = Math.max(4, Math.round(value / maxes[key] * 100));
      return `<div class="density-bar"><b>${esc(categoryLabel(key))}</b><span style="--value:${pct}%"></span><em>${value}</em></div>`;
    }).join('');
  };
  const evaluate = () => {
    if (!payload?.stations?.length) return;
    const station = stationById(stationSelect.value) || payload.stations[0];
    const industry = industrySelect.value || 'cafe';
    const purpose = purposeSelect.value || 'commercial';
    const count = valueFor(station, industry);
    const compare = compareStationFor(station);
    const grade = gradeFor(station, industry);
    root.dataset.grade = grade.grade;
    scoreRoot && (scoreRoot.dataset.grade = grade.grade);
    stationMeta && (stationMeta.textContent = `${station.district} ${station.dong} · ${station.radius_m || 650}m`);
    stationTitle.textContent = `${station.name} ${industry === 'population' ? '인구밀도' : `${categoryLabel(industry)} 밀도`}`;
    gradeEl && (gradeEl.textContent = `${grade.label} ${grade.score}`);
    countEl && (countEl.textContent = String(count));
    countLabelEl && (countLabelEl.textContent = categoryLabel(industry));
    commercialDensityEl && (commercialDensityEl.textContent = String(station.commercial_density_index || 0));
    popDensityEl && (popDensityEl.textContent = String(station.population_density_index || 0));
    popLabelEl && (popLabelEl.textContent = station.population_density_label || '지수');
    summaryEl && (summaryEl.textContent = `${station.name}은 상권 밀도 ${station.commercial_density_label}, 인구밀도 ${station.population_density_label} 구간입니다. ${station.default_take || ''}`);
    riskListEl.innerHTML = questionsFor(station, industry, purpose).map((item) => `<li>${esc(item)}</li>`).join('');
    linksEl && (linksEl.innerHTML = purpose === 'home'
      ? [link('/topics/jeonwolse-contract-check/', '전월세 체크 글 목록'), link('/search/?q=%EB%B0%A4%EA%B8%B8%20%EC%86%8C%EC%9D%8C%20%EC%B2%B4%ED%81%AC', '밤길·소음 검색'), link('/search/?q=%EA%B4%80%EB%A6%AC%EB%B9%84%20%EC%B2%B4%ED%81%AC', '관리비 검색')].join('')
      : [link('/topics/cafe-commercial-lease-risk/', '상가 계약 체크 글 목록'), link('/search/?q=%EC%83%81%EA%B0%80%20%EA%B3%84%EC%95%BD', '상가 계약 검색'), link('/search/?q=%EA%B6%8C%EB%A6%AC%EA%B8%88%20%EB%A6%AC%EC%8A%A4%ED%81%AC', '권리금 검색')].join(''));
    renderBars(station);
    renderCompare(station, compare, industry);
    updateMapHeat(industry);
  };

  const hydrate = (data) => {
    payload = data;
    if (payload?.source_summary && sourceNoteEl) sourceNoteEl.textContent = payload.source_summary;
    evaluate();
  };
  layerButtons.forEach((button) => button.addEventListener('click', () => { industrySelect.value = button.dataset.densityLayer || 'cafe'; evaluate(); }));
  stationButtons.forEach((button) => button.addEventListener('click', () => { stationSelect.value = button.dataset.stationMap || stationSelect.value; evaluate(); }));
  stationSelect.addEventListener('change', evaluate);
  compareSelect.addEventListener('change', evaluate);
  industrySelect.addEventListener('change', evaluate);
  purposeSelect.addEventListener('change', evaluate);

  fetch(root.dataset.densitySrc || '/data/seoul-commercial-areas.json', {cache: 'no-store'})
    .then((res) => res.ok ? res.json() : Promise.reject(new Error(`density data ${res.status}`)))
    .then(hydrate)
    .catch((error) => {
      console.warn('seoul density data load failed', error);
      const embedded = window.SEOUL_COMMERCIAL_AREAS;
      if (embedded) hydrate(embedded);
    });
})();