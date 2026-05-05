(() => {
  const root = document.querySelector('[data-commercial-tool-root]');
  if (!root) return;
  const form = root.querySelector('[data-commercial-tool]');
  const byId = (id) => root.querySelector(`#${id}`);
  const locationInput = byId('tool-location');
  const typeInput = byId('tool-type');
  const monthlyInput = byId('tool-monthly');
  const trafficInput = byId('tool-traffic');
  const competitionInput = byId('tool-competition');
  const nightInput = byId('tool-night');
  const anchorInput = byId('tool-anchor');
  const monthlyValue = root.querySelector('[data-monthly-value]');
  const scoreEl = root.querySelector('[data-risk-score]');
  const gradeEl = root.querySelector('[data-risk-grade]');
  const summaryEl = root.querySelector('[data-risk-summary]');
  const titleEl = root.querySelector('[data-result-title]');
  const listEl = root.querySelector('[data-risk-list]');
  const linksEl = root.querySelector('[data-recommend-links]');
  if (!form || !locationInput || !typeInput || !monthlyInput || !scoreEl || !gradeEl || !summaryEl || !titleEl || !listEl || !linksEl) return;
  const esc = (value) => String(value || '').replace(/[&<>"]/g, (ch) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[ch]));
  const link = (href, label) => `<a href="${href}">${esc(label)}</a>`;
  const add = (items, condition, item) => { if (condition) items.push(item); };
  const evaluate = () => {
    const type = typeInput.value;
    const monthly = Number(monthlyInput.value || 0);
    const traffic = trafficInput.value;
    const competition = competitionInput.value;
    const night = nightInput.value;
    const anchor = anchorInput.value;
    const place = locationInput.value.trim() || (type === 'commercial' ? '상가 후보지' : '전월세 후보지');
    let score = 72;
    const risks = [];
    if (type === 'commercial') {
      if (monthly >= 520) score -= 17; else if (monthly >= 330) score -= 9; else if (monthly <= 160) score += 5;
      if (traffic === 'weak') score -= 18; else if (traffic === 'strong') score += 8;
      if (competition === 'high') score -= 16; else if (competition === 'low') score += 6;
      if (night === 'unsafe') score -= 10; else if (night === 'safe') score += 4;
      if (anchor === 'weak') score -= 13; else if (anchor === 'strong') score += 8;
      add(risks, monthly >= 330, '월 고정 부담이 큽니다. 임대료·관리비·인건비를 보수적으로 다시 계산하세요.');
      add(risks, traffic === 'weak', '낮 유입이 약합니다. 점심·퇴근·주말 시간대를 나눠 실제 체류 인원을 확인하세요.');
      add(risks, competition === 'high', '경쟁·공실 압력이 높습니다. 같은 업종이 내 고객을 나눠 갖는지 500m 안에서 보세요.');
      add(risks, anchor === 'weak', '앵커시설이 약합니다. 역·회사·학교·마트처럼 반복 방문을 만드는 이유가 있는지 확인하세요.');
      add(risks, night === 'unsafe', '밤길·소음 리스크가 있습니다. 영업 종료 후 귀가 동선과 민원 가능성을 같이 보세요.');
    } else {
      if (monthly >= 260) score -= 16; else if (monthly >= 170) score -= 8; else if (monthly <= 110) score += 5;
      if (traffic === 'weak') score -= 10; else if (traffic === 'strong') score += 8;
      if (competition === 'high') score -= 8; else if (competition === 'low') score += 3;
      if (night === 'unsafe') score -= 18; else if (night === 'safe') score += 7;
      if (anchor === 'weak') score -= 12; else if (anchor === 'strong') score += 8;
      add(risks, monthly >= 170, '월세·관리비·교통비를 합친 고정비가 높습니다. 한 달 현금흐름으로 다시 보세요.');
      add(risks, night === 'unsafe', '밤길이나 소음이 걱정됩니다. 퇴근 후 10분 현장 확인을 먼저 잡으세요.');
      add(risks, traffic === 'weak', '생활 편의가 약합니다. 장보기·병원·운동처럼 반복 동선이 멀어지는지 확인하세요.');
      add(risks, anchor === 'weak', '대체 생활권이 약합니다. 같은 예산으로 갈 수 있는 후보지를 하나 더 남기세요.');
      add(risks, competition === 'high', '공실·관리 상태 압력이 보입니다. 같은 건물과 옆 건물의 관리 흔적을 비교하세요.');
    }
    score = Math.max(18, Math.min(94, Math.round(score)));
    const grade = score >= 78 ? 'good' : score >= 58 ? 'warn' : 'hold';
    const gradeText = grade === 'good' ? '진행' : grade === 'warn' ? '주의' : '보류';
    const fallbackRisks = type === 'commercial'
      ? ['권리금 회수 조건을 계약서 문구로 확인하세요.', '출근·점심·퇴근·주말을 나눠 유입을 다시 보세요.', '비슷한 업종의 가격대와 회전율을 500m 안에서 비교하세요.']
      : ['관리비 항목을 영수증 기준으로 확인하세요.', '밤 10시 이후 소음과 귀가 동선을 확인하세요.', '통근 대체 경로와 비 오는 날 동선을 같이 보세요.'];
    const finalRisks = risks.concat(fallbackRisks).slice(0, 3);
    root.dataset.mode = type === 'commercial' ? 'commercial' : 'home';
    root.dataset.grade = grade;
    monthlyValue.textContent = `${monthly}만원`;
    scoreEl.textContent = String(score);
    gradeEl.textContent = gradeText;
    summaryEl.textContent = `${place} 기준 결과는 ${gradeText} 단계입니다. 계약 전에는 점수보다 아래 질문 3개를 먼저 확인하세요.`;
    titleEl.textContent = type === 'commercial' ? '상가 계약 전에 이 3가지를 다시 보세요' : '전월세 계약 전에 이 3가지를 다시 보세요';
    listEl.innerHTML = finalRisks.map((item) => `<li>${esc(item)}</li>`).join('');
    linksEl.innerHTML = type === 'commercial'
      ? [link('/topics/cafe-commercial-lease-risk/', '상가 계약 체크 글 목록'), link('/search/?q=%EC%83%81%EA%B0%80%20%EA%B3%84%EC%95%BD', '상가 계약 검색'), link('/search/?q=%EA%B6%8C%EB%A6%AC%EA%B8%88%20%EB%A6%AC%EC%8A%A4%ED%81%AC', '권리금 리스크 검색')].join('')
      : [link('/topics/jeonwolse-contract-check/', '전월세 체크 글 목록'), link('/search/?q=%EC%9B%94%EC%84%B8%20%EA%B3%84%EC%95%BD%20%EC%B2%B4%ED%81%AC', '월세 계약 검색'), link('/search/?q=%EB%B0%A4%EA%B8%B8%20%EC%86%8C%EC%9D%8C%20%EC%B2%B4%ED%81%AC', '밤길·소음 검색')].join('');
  };
  form.addEventListener('input', evaluate);
  form.addEventListener('change', evaluate);
  form.addEventListener('submit', (event) => { event.preventDefault(); evaluate(); root.querySelector('.commercial-tool-output')?.scrollIntoView({behavior: 'smooth', block: 'nearest'}); });
  evaluate();
})();