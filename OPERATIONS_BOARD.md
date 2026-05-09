# 동네 레이더 OPERATIONS BOARD

_Last updated: 2026-05-09T10:13:20+09:00 KST_

## Scope

- `동네 레이더` GitHub Pages `/radar/` 전용.
- 다른 프로젝트/채널 상태는 조회·비교·보고하지 않는다.
- Tistory 발행·브라우저 자동화·수동 복붙 패키지는 폐기했다. 외부 로그인·권한·카테고리·스킨·광고 설정은 hourly에서 수행하지 않는다.

## Current KPI

- 현재 전략: GitHub Pages `/radar/` 중심 awareness-first 공개 매거진.
- 전략 원칙: `양보다 타겟 적합도`. 매 글은 서울/수도권 25~39세 이사·전월세·동네비교 독자의 실제 결정 하나를 도와야 한다.
- 전략 게이트: 새 후보/공개 글은 **독자 / 결정상황 / 지금성 / 차별성 / 도구성** 5문항을 통과해야 한다.
- 타겟 품질 게이트: 도입 600자 안에 `서울·수도권`, `25~39세`, 전월세/이사/거주지 비교, 계속 볼지·보류할지·무엇을 확인할지의 행동이 보여야 한다.
- 공개 cadence: **매일 1개는 기본 floor**다. 하루 1개 cap은 폐기하고, dedicated publisher desk만 GitHub Pages `/radar/`에 공개한다. backlog가 목표 7개를 넘으면 adaptive 발행부가 하루 최대 4개·최소 2시간 간격으로 추가 공개한다.
- 매일 포스팅 조건: 각 글의 타겟이 명확하고 본문 품질·시각자료·금칙어·hard/soft issue 기준을 모두 충족하면 발행을 미루지 않는다.
- 첫 KPI: 품질 통과 release candidate 수가 아니라 **타겟에 맞는 발행 큐의 선명도**다.
- 생산 기준: 품질 통과 미발행 후보 최소 3개, 목표 7개, 상한 10개. 2026-05-09 10:13 기준 최신 deterministic review/publisher 표면은 review-surface published 6개·미발행 clean 3개(Y/Z/AA)다. 이번 턴은 새 후보를 만들지 않고 `IDEA_BANK.md`와 queue handoff를 Y/Z/AA 기준으로 재정렬했다. 현행 clean queue는 Y/Z/AA로 유지한다. Y/Z/AA는 `품질통과 선발행 후보`로 보관하며, 7일/168시간 대기 문구를 쓰지 않는다.
- 현재 deterministic review 표면: 이 checkout에서 review 가능한 `release_candidates/**/final.html`은 9개, 그중 review-surface published 6개·미발행 clean 3개다. 최종 verification review(`2026-05-09T10:13:01+09:00`)는 `ready=9/9 hard=0 soft=0`; Y=`chars=6748 visuals=32 media_blockers=0 photo_cards=16 links=9`, Z=`chars=6902 visuals=30 media_blockers=0 photo_cards=15 links=3`, AA=`laundry-drying-route-home-check chars=4784 visuals=24 target_fit=True media_blockers=0 photo_cards=12 links=3`, 셋 모두 `target_fit=True`이고 adaptive publisher summary에서는 `eligible=True`다. Y/Z/AA final HTML의 `field-visual`/`visual-figure`/`<svg`/`.svg` residue scan은 0이다. 최종 adaptive dry-run은 `slot_closed`(`ready_unpublished=3<=ready_target=7`, `daily_floor_open=False`, `published_today=1/4`, `spacing_open=True`, `hours_since_last=9.416`, selected none)로 이번 턴 실제 공개/commit/push 없음. 최신 hourly smoke는 pass(`warnings=0`, `2026-05-09T10:13:01+09:00`)이며 build/local quality audit도 pass(`static_pages=7`, `failures=[]`)다. 과거 board의 `ready=19` 문구는 historical/public metadata 성격이며 현재 발행부 선별 기준으로 쓰지 않는다.
- 7일/168시간은 buffer tracking metadata일 뿐, clean 후보 발행 차단 사유가 아니다.
- 본문 4,500자 이상, 독자용 시각자료 8개 이상, AI 실사 WebP 썸네일 1장+field_examples 3장, visible 금칙어 0건, hard/soft issue 0건이면 `검사 충분`으로 보고 선발행 후보 기준을 통과한다. 충분히 검사된 후보는 추가 숙성/완벽주의로 묶어두지 않고 baseline/adaptive 슬롯이 열리면 공개한다.
- media blocker는 hard issue다. 픽토그램/도표형 썸네일, inline SVG, `.svg`, `.png`, 외부 이미지 URL, `/thumbs/` 재사용 field example, AI 실사 WebP 누락이 보이면 새 글/발행 준비를 멈추고 이미지 생성·연결부터 고친다.

## Queue

### A. 동네 신호 읽기 기본 프레임

- 상태: `release_candidate_ready` / backlog 감축 턴에서 좋은 반례·보류 전환 신호 표를 추가해 평균 점수 오독을 줄였다. review 통과 (`ready=19 hard=0 soft=0`, 해당 후보 chars=5145 visuals=10). GitHub Pages 공개본 로컬 빌드 기준은 유지. Tistory 대기 상태는 폐기.
- 최종본: `release_candidates/2026-04/dongne-signal-framework/final.html`
- 메타: `release_candidates/2026-04/dongne-signal-framework/metadata.json`
- 검증: `reports/cron-review-latest.md`; hourly smoke pass (`ready=19 hard=0 soft=0 warnings=0`); publisher adaptive 상태는 spacing/day guard를 기록하며 발행부 슬롯이 열리면 실제 GitHub Pages 공개까지 수행한다.
- Stage notes:
  - [x] 00-topic: `articles/2026-04/dongne-signal-framework/00-topic.md`
  - [x] 10-source: `articles/2026-04/dongne-signal-framework/10-source.md`
  - [x] 20-data-qa: `articles/2026-04/dongne-signal-framework/20-data-qa.md`
  - [x] 30-story: `articles/2026-04/dongne-signal-framework/30-story.md`
  - [x] 40-visual: `articles/2026-04/dongne-signal-framework/40-visual-plan.md`
  - [x] 50-copy: `articles/2026-04/dongne-signal-framework/50-copy.md`
  - [x] 60-reader-qa: `articles/2026-04/dongne-signal-framework/60-reader-qa.md`
  - [x] 70-final-html: `articles/2026-04/dongne-signal-framework/70-final-html.md`
  - [x] 80-growth: `articles/2026-04/dongne-signal-framework/80-growth.md`

### B. 서울에서 2030 여성이 빠지는 구 TOP 10

- 상태: `source_blocked` — 원자료·기준월·산식 확보 전 TOP 10 확정 금지.
- Stage notes:
  - [x] 00-topic: `articles/2026-04/seoul-2030-women-outflow-top10/00-topic.md`
  - [x] 10-source: `articles/2026-04/seoul-2030-women-outflow-top10/10-source.md`
  - [ ] 20-data-qa: 원자료 확보 후 진행.

### C. 월세 체감 압박을 읽는 5개 질문

- 상태: `published_to_pages` / 2026-05-01T08:41:53+09:00 KST에 GitHub Pages `/radar/monthly-rent-pressure-questions/` 공개. 70-final-html 패키징과 review 통과 기준은 보존한다.
- 최종본: `release_candidates/2026-04/monthly-rent-pressure-questions/final.html`
- 메타: `release_candidates/2026-04/monthly-rent-pressure-questions/metadata.json`
- 검증: `reports/cron-review-latest.md`
- Stage notes:
  - [x] 00-topic: `articles/2026-04/monthly-rent-pressure-questions/00-topic.md`
  - [x] 10-source: `articles/2026-04/monthly-rent-pressure-questions/10-source.md`
  - [x] 20-data-qa: `articles/2026-04/monthly-rent-pressure-questions/20-data-qa.md`
  - [x] 30-story: `articles/2026-04/monthly-rent-pressure-questions/30-story.md`
  - [x] 40-visual: `articles/2026-04/monthly-rent-pressure-questions/40-visual-plan.md`
  - [x] 50-copy: `articles/2026-04/monthly-rent-pressure-questions/50-copy.md`
  - [x] 60-reader-qa: `articles/2026-04/monthly-rent-pressure-questions/60-reader-qa.md`
  - [x] 70-final-html: `articles/2026-04/monthly-rent-pressure-questions/70-final-html.md`

### D. 관리비 항목이 흐린 월세 후보, 계속 볼까 보류할까?

- 상태: `published_to_pages` / 2026-05-02T08:28:39+09:00 KST에 GitHub Pages `/radar/maintenance-fee-opaque-rent/` 공개. review 통과 기준과 release candidate 기록은 보존한다. 7일 값은 rolling buffer 메타였으며 발행 대기 하드게이트가 아니었다.
- 최종본: `release_candidates/2026-04/maintenance-fee-opaque-rent/final.html`
- 메타: `release_candidates/2026-04/maintenance-fee-opaque-rent/metadata.json`
- 검증: `reports/cron-review-latest.md`
- Stage notes:
  - [x] 00-topic: `articles/2026-04/maintenance-fee-opaque-rent/00-topic.md`
  - [x] 10-source: `articles/2026-04/maintenance-fee-opaque-rent/10-source.md`
  - [x] 20-data-qa: `articles/2026-04/maintenance-fee-opaque-rent/20-data-qa.md`
  - [x] 30-story: `articles/2026-04/maintenance-fee-opaque-rent/30-story.md`
  - [x] 40-visual: `articles/2026-04/maintenance-fee-opaque-rent/40-visual-plan.md`
  - [x] 50-copy: `articles/2026-04/maintenance-fee-opaque-rent/50-copy.md`
  - [x] 60-reader-qa: `articles/2026-04/maintenance-fee-opaque-rent/60-reader-qa.md`
  - [x] 70-final-html: `articles/2026-04/maintenance-fee-opaque-rent/70-final-html.md`
  - [x] 80-growth: `articles/2026-04/maintenance-fee-opaque-rent/80-growth.md` prelaunch search/handoff hypothesis.

### E. 퇴근 후 20분, 살 동네를 다시 보는 법

- 상태: `release_candidate_ready` / 50-copy 확장, 70-final-html 패키징 완료. backlog 감축 턴에서 도입 첫 화면에 `3~12개월 안에 전월세·이사 후보를 비교하는 25~39세`와 `계속 볼지·보류할지·무엇을 물을지` 행동을 명시했고, 이번 턴에는 큰 프레임·월세 질문·관리 신호로 이어 보는 내부 연결 표를 추가해 퇴근 후 루프의 역할을 분리했다. review 통과 (`ready=19 hard=0 soft=0`, 해당 후보 chars=5081 visuals=11, target_fit=True). 7일 값은 rolling buffer 메타일 뿐 대기 하드게이트가 아니다.
- 최종본: `release_candidates/2026-04/after-work-neighborhood-check/final.html`
- 메타: `release_candidates/2026-04/after-work-neighborhood-check/metadata.json`
- 검증: `reports/cron-review-latest.md`
- Stage notes:
  - [x] 00-topic: `articles/2026-04/after-work-neighborhood-check/00-topic.md`
  - [x] 10-source: `articles/2026-04/after-work-neighborhood-check/10-source.md`
  - [x] 20-data-qa: `articles/2026-04/after-work-neighborhood-check/20-data-qa.md`
  - [x] 30-story: `articles/2026-04/after-work-neighborhood-check/30-story.md`
  - [x] 40-visual: `articles/2026-04/after-work-neighborhood-check/40-visual-plan.md`
  - [x] 50-copy: `articles/2026-04/after-work-neighborhood-check/50-copy.md`
  - [x] 60-reader-qa: `articles/2026-04/after-work-neighborhood-check/60-reader-qa.md`
  - [x] 70-final-html: `articles/2026-04/after-work-neighborhood-check/70-final-html.md`
  - [x] 70-publish note: `articles/2026-04/after-work-neighborhood-check/70-publish-note.md`
  - [x] 80-growth: `articles/2026-04/after-work-neighborhood-check/80-growth.md`

### F. 출근길 15분, 통근 피로를 확인하는 동네 체크

- 상태: `release_candidate_ready` / 60-reader-qa 통과, 70-final-html 패키징 완료, review 통과 (`ready=5 hard=0 soft=0`, 해당 후보 chars=5695 visuals=9). 품질 통과 글은 keep하고 dedicated publisher desk의 adaptive 슬롯·정책에 맡긴다.
- 최종본: `release_candidates/2026-04/commute-fatigue-neighborhood-check/final.html`
- 메타: `release_candidates/2026-04/commute-fatigue-neighborhood-check/metadata.json`
- 검증: `reports/cron-review-latest.md`
- Stage notes:
  - [x] 00-topic: `articles/2026-04/commute-fatigue-neighborhood-check/00-topic.md`
  - [x] 10-source: `articles/2026-04/commute-fatigue-neighborhood-check/10-source.md`
  - [x] 20-data-qa: `articles/2026-04/commute-fatigue-neighborhood-check/20-data-qa.md`
  - [x] 30-story: `articles/2026-04/commute-fatigue-neighborhood-check/30-story.md`
  - [x] 40-visual: `articles/2026-04/commute-fatigue-neighborhood-check/40-visual-plan.md`
  - [x] 50-copy: `articles/2026-04/commute-fatigue-neighborhood-check/50-copy.md`
  - [x] 60-reader-qa: `articles/2026-04/commute-fatigue-neighborhood-check/60-reader-qa.md`
  - [x] 70-final-html: `articles/2026-04/commute-fatigue-neighborhood-check/70-final-html.md`
  - [x] 70-publish note: `articles/2026-04/commute-fatigue-neighborhood-check/70-publish-note.md`
  - [x] 80-growth: `articles/2026-04/commute-fatigue-neighborhood-check/80-growth.md`

### G. 비 오는 날 집 보러 갈 때 놓치는 동네 신호

- 상태: `release_candidate_ready` / 50-copy 작성, 60-reader-qa 통과, 70-final-html 패키징 완료. backlog 감축 턴에서 새 후보 생성 없이 `다른 동네 체크와 헷갈리지 않는 기준` 표를 추가해 비 오는 날 후보의 역할을 퇴근 후 루프·관리비 질문과 분리했다. review 통과 (`ready=19 hard=0 soft=0`, 해당 후보 chars=5443 visuals=10, target_fit=True). 품질 통과 글은 keep하고 dedicated publisher desk의 adaptive 슬롯·정책에 맡긴다.
- 최종본: `release_candidates/2026-04/rainy-day-viewing-neighborhood-signals/final.html`
- 메타: `release_candidates/2026-04/rainy-day-viewing-neighborhood-signals/metadata.json`
- 검증: `reports/cron-review-latest.md`
- Stage notes:
  - [x] 00-topic: `articles/2026-04/rainy-day-viewing-neighborhood-signals/00-topic.md`
  - [x] 10-source: `articles/2026-04/rainy-day-viewing-neighborhood-signals/10-source.md`
  - [x] 20-data-qa: `articles/2026-04/rainy-day-viewing-neighborhood-signals/20-data-qa.md`
  - [x] 30-story: `articles/2026-04/rainy-day-viewing-neighborhood-signals/30-story.md`
  - [x] 40-visual: `articles/2026-04/rainy-day-viewing-neighborhood-signals/40-visual-plan.md`
  - [x] 50-copy: `articles/2026-04/rainy-day-viewing-neighborhood-signals/50-copy.md`
  - [x] 60-reader-qa: `articles/2026-04/rainy-day-viewing-neighborhood-signals/60-reader-qa.md`
  - [x] 70-final-html: `articles/2026-04/rainy-day-viewing-neighborhood-signals/70-final-html.md`
  - [x] 70-publish note: `articles/2026-04/rainy-day-viewing-neighborhood-signals/70-publish-note.md`
  - [x] 80-growth: `articles/2026-04/rainy-day-viewing-neighborhood-signals/80-growth.md`

### H. 밤 10시, 살 동네 소음을 확인하는 15분 산책

- 상태: `release_candidate_ready` / 10-source→70-final-html 패키징 완료. backlog 감축 턴에서 `재방문 우선순위 표`를 추가해 처음 들은 밤 소리 신호를 다시 볼 시간과 질문으로 연결했다. review 통과 (`ready=19 hard=0 soft=0`, 해당 후보 chars=5239 visuals=9). 품질 통과 글은 keep하고 dedicated publisher desk의 adaptive 슬롯·정책에 맡긴다.
- 최종본: `release_candidates/2026-04/night-noise-walk-check/final.html`
- 메타: `release_candidates/2026-04/night-noise-walk-check/metadata.json`
- 검증: `reports/cron-review-latest.md`
- Stage notes:
  - [x] 00-topic: `articles/2026-04/night-noise-walk-check/00-topic.md`
  - [x] 10-source: `articles/2026-04/night-noise-walk-check/10-source.md`
  - [x] 20-data-qa: `articles/2026-04/night-noise-walk-check/20-data-qa.md`
  - [x] 30-story: `articles/2026-04/night-noise-walk-check/30-story.md`
  - [x] 40-visual: `articles/2026-04/night-noise-walk-check/40-visual-plan.md`
  - [x] 50-copy: `articles/2026-04/night-noise-walk-check/50-copy.md`
  - [x] 60-reader-qa: `articles/2026-04/night-noise-walk-check/60-reader-qa.md`
  - [x] 70-final-html: `articles/2026-04/night-noise-walk-check/70-final-html.md`
  - [x] 70-publish note: `articles/2026-04/night-noise-walk-check/70-publish-note.md`
  - [x] 80-growth: `articles/2026-04/night-noise-walk-check/80-growth.md`

### I. 아침 8시, 등교·수거·출근 동선이 겹치는 동네 체크

- 상태: `release_candidate_ready` / 신규 버퍼 후보 00-topic→70-final-html 패키징 완료, review 통과 (`ready=8 hard=0 soft=0`, 해당 후보 chars=5086 visuals=9). 품질 통과 글은 keep하고 dedicated publisher desk의 adaptive 슬롯·정책에 맡긴다.
- 최종본: `release_candidates/2026-05/morning-routine-neighborhood-check/final.html`
- 메타: `release_candidates/2026-05/morning-routine-neighborhood-check/metadata.json`
- 검증: `reports/cron-review-latest.md`
- Stage notes:
  - [x] 00-topic: `articles/2026-05/morning-routine-neighborhood-check/00-topic.md`
  - [x] 10-source: `articles/2026-05/morning-routine-neighborhood-check/10-source.md`
  - [x] 20-data-qa: `articles/2026-05/morning-routine-neighborhood-check/20-data-qa.md`
  - [x] 30-story: `articles/2026-05/morning-routine-neighborhood-check/30-story.md`
  - [x] 40-visual: `articles/2026-05/morning-routine-neighborhood-check/40-visual-plan.md`
  - [x] 50-copy: `articles/2026-05/morning-routine-neighborhood-check/50-copy.md`
  - [x] 60-reader-qa: `articles/2026-05/morning-routine-neighborhood-check/60-reader-qa.md`
  - [x] 70-final-html: `articles/2026-05/morning-routine-neighborhood-check/70-final-html.md`
  - [x] 70-publish note: `articles/2026-05/morning-routine-neighborhood-check/70-publish-note.md`
  - [x] 80-growth: `articles/2026-05/morning-routine-neighborhood-check/80-growth.md`


### J. 엘리베이터 없는 4층 빌라, 계속 볼지 보류할지 보는 12분

- 상태: `release_candidate_ready` / backlog 감축 턴에서 새 후보 생성 없이 비슷한 조건 후보와 나란히 보는 비교표 visual을 추가해 계단형 후보의 계속 보기/보류 판단을 같은 금액대 후보와 비교하게 했다. review 통과 (`ready=19 hard=0 soft=0`, 해당 후보 chars=5066 visuals=10, target_fit=True). 품질 통과 글은 keep하고 dedicated publisher desk의 adaptive 슬롯·정책에 맡긴다.
- 최종본: `release_candidates/2026-05/stair-only-fourth-floor-villa-check/final.html`
- 메타: `release_candidates/2026-05/stair-only-fourth-floor-villa-check/metadata.json`
- 검증: `reports/cron-review-latest.md`
- Stage notes:
  - [x] 00-topic: `articles/2026-05/stair-only-fourth-floor-villa-check/00-topic.md`
  - [x] 10-source: `articles/2026-05/stair-only-fourth-floor-villa-check/10-source.md`
  - [x] 20-data-qa: `articles/2026-05/stair-only-fourth-floor-villa-check/20-data-qa.md`
  - [x] 30-story: `articles/2026-05/stair-only-fourth-floor-villa-check/30-story.md`
  - [x] 40-visual: `articles/2026-05/stair-only-fourth-floor-villa-check/40-visual-plan.md`
  - [x] 50-copy: `articles/2026-05/stair-only-fourth-floor-villa-check/50-copy.md`
  - [x] 60-reader-qa: `articles/2026-05/stair-only-fourth-floor-villa-check/60-reader-qa.md`
  - [x] 70-final-html: `articles/2026-05/stair-only-fourth-floor-villa-check/70-final-html.md`
  - [x] 70-publish note: `articles/2026-05/stair-only-fourth-floor-villa-check/70-publish-note.md`
  - [x] 80-growth: `articles/2026-05/stair-only-fourth-floor-villa-check/80-growth.md`

### K. 반지하가 아닌 1층집, 계속 볼지 보류할지 보는 14분

- 상태: `release_candidate_ready` / backlog 감축 턴에서 새 후보 생성 없이 `재방문 시간대 선택표`를 추가해 낮 방문 뒤 남는 빈칸을 밤·수거 전날·비 온 다음 날 확인 행동으로 연결했다. review 통과 (`ready=19 hard=0 soft=0`, 해당 후보 chars=5008 visuals=10). 품질 통과 글은 keep하고 dedicated publisher desk의 adaptive 슬롯·정책에 맡긴다.
- 최종본: `release_candidates/2026-05/ground-floor-home-check/final.html`
- 메타: `release_candidates/2026-05/ground-floor-home-check/metadata.json`
- 검증: `reports/cron-review-latest.md`
- Stage notes:
  - [x] 00-topic: `articles/2026-05/ground-floor-home-check/00-topic.md`
  - [x] 10-source: `articles/2026-05/ground-floor-home-check/10-source.md`
  - [x] 20-data-qa: `articles/2026-05/ground-floor-home-check/20-data-qa.md`
  - [x] 30-story: `articles/2026-05/ground-floor-home-check/30-story.md`
  - [x] 40-visual: `articles/2026-05/ground-floor-home-check/40-visual-plan.md`
  - [x] 50-copy: `articles/2026-05/ground-floor-home-check/50-copy.md`
  - [x] 60-reader-qa: `articles/2026-05/ground-floor-home-check/60-reader-qa.md`
  - [x] 70-final-html: `articles/2026-05/ground-floor-home-check/70-final-html.md`
  - [x] 70-publish note: `articles/2026-05/ground-floor-home-check/70-publish-note.md`
  - [x] 80-growth: `articles/2026-05/ground-floor-home-check/80-growth.md`

### L. 공동현관 앞 30초, 살 동네의 관리 신호를 읽는 법

- 상태: `release_candidate_ready` / backlog 감축 턴에서 새 후보 생성 없이 비슷한 조건 후보 비교표와 내부 링크를 추가해 공동현관 신호를 분리수거·주차장·밤길·오래된 빌라 후보와 나란히 비교하게 했다. review 통과 (`ready=19 hard=0 soft=0`, 해당 후보 chars=5201 visuals=10, target_fit=True). 품질 통과 글은 keep하고 dedicated publisher desk의 adaptive 슬롯·정책에 맡긴다.
- 최종본: `release_candidates/2026-05/shared-entrance-management-signals/final.html`
- 메타: `release_candidates/2026-05/shared-entrance-management-signals/metadata.json`
- 검증: `reports/cron-review-latest.md`; hourly smoke pass (`ready=19 hard=0 soft=0 warnings=0`); publisher dry-run은 `maintenance-fee-opaque-rent`를 다음 공개 후보로 selected 했고 발행부 adaptive 슬롯이 열리면 GitHub Pages 공개까지 수행한다.
- Stage notes:
  - [x] 00-topic: `articles/2026-05/shared-entrance-management-signals/00-topic.md`
  - [x] 10-source: `articles/2026-05/shared-entrance-management-signals/10-source.md`
  - [x] 20-data-qa: `articles/2026-05/shared-entrance-management-signals/20-data-qa.md`
  - [x] 30-story: `articles/2026-05/shared-entrance-management-signals/30-story.md`
  - [x] 40-visual: `articles/2026-05/shared-entrance-management-signals/40-visual-plan.md`
  - [x] 50-copy: `articles/2026-05/shared-entrance-management-signals/50-copy.md`
  - [x] 60-reader-qa: `articles/2026-05/shared-entrance-management-signals/60-reader-qa.md`
  - [x] 70-final-html: `articles/2026-05/shared-entrance-management-signals/70-final-html.md`
  - [x] 70-publish note: `articles/2026-05/shared-entrance-management-signals/70-publish-note.md`
  - [x] 80-growth: `articles/2026-05/shared-entrance-management-signals/80-growth.md`

### M. 역에서 집까지 마지막 7분, 밤길을 다시 보는 법

- 상태: `release_candidate_ready` / backlog 감축 턴에서 새 후보 생성 없이 `비슷한 밤 동선 후보와 나란히 보기` 비교표를 추가해 역세권 밤길 판단을 생활권 루프·방 안 소리·정류장 대기·공동현관 관리 신호와 분리했다. review 통과 (`ready=19 hard=0 soft=0`, 해당 후보 chars=5276 visuals=11, target_fit=True). 품질 통과 글은 keep하고 dedicated publisher desk의 adaptive 슬롯·정책에 맡긴다.
- 최종본: `release_candidates/2026-05/station-to-home-night-route-check/final.html`
- 메타: `release_candidates/2026-05/station-to-home-night-route-check/metadata.json`
- 검증: `reports/cron-review-latest.md`
- Stage notes:
  - [x] 00-topic: `articles/2026-05/station-to-home-night-route-check/00-topic.md`
  - [x] 10-source: `articles/2026-05/station-to-home-night-route-check/10-source.md`
  - [x] 20-data-qa: `articles/2026-05/station-to-home-night-route-check/20-data-qa.md`
  - [x] 30-story: `articles/2026-05/station-to-home-night-route-check/30-story.md`
  - [x] 40-visual: `articles/2026-05/station-to-home-night-route-check/40-visual-plan.md`
  - [x] 50-copy: `articles/2026-05/station-to-home-night-route-check/50-copy.md`
  - [x] 60-reader-qa: `articles/2026-05/station-to-home-night-route-check/60-reader-qa.md`
  - [x] 70-final-html: `articles/2026-05/station-to-home-night-route-check/70-final-html.md`
  - [x] 70-publish note: `articles/2026-05/station-to-home-night-route-check/70-publish-note.md`
  - [x] 80-growth: `articles/2026-05/station-to-home-night-route-check/80-growth.md`

### N. 버스정류장 앞 집, 편한 위치인지 피곤한 위치인지 보는 10분

- 상태: `release_candidate_ready` / backlog 감축 턴에서 새 후보 생성 없이 `같은 조건 후보와 나란히 보는 표`를 추가해 정류장 가까움의 편의/피로 판단을 퇴근 후 루프·밤길·공동현관 관리 신호와 연결했다. review 통과 (`ready=19 hard=0 soft=0`, 해당 후보 chars=5476 visuals=10, target_fit=True). 품질 통과 글은 keep하고 dedicated publisher desk의 adaptive 슬롯·정책에 맡긴다.
- 최종본: `release_candidates/2026-05/bus-stop-front-home-check/final.html`
- 메타: `release_candidates/2026-05/bus-stop-front-home-check/metadata.json`
- 검증: `reports/cron-review-latest.md`
- Stage notes:
  - [x] 00-topic: `articles/2026-05/bus-stop-front-home-check/00-topic.md`
  - [x] 10-source: `articles/2026-05/bus-stop-front-home-check/10-source.md`
  - [x] 20-data-qa: `articles/2026-05/bus-stop-front-home-check/20-data-qa.md`
  - [x] 30-story: `articles/2026-05/bus-stop-front-home-check/30-story.md`
  - [x] 40-visual: `articles/2026-05/bus-stop-front-home-check/40-visual-plan.md`
  - [x] 50-copy: `articles/2026-05/bus-stop-front-home-check/50-copy.md`
  - [x] 60-reader-qa: `articles/2026-05/bus-stop-front-home-check/60-reader-qa.md`
  - [x] 70-final-html: `articles/2026-05/bus-stop-front-home-check/70-final-html.md`
  - [x] 70-publish note: `articles/2026-05/bus-stop-front-home-check/70-publish-note.md`
  - [x] 80-growth: `articles/2026-05/bus-stop-front-home-check/80-growth.md`

### O. 창밖이 가까운 집, 채광보다 먼저 볼 거리감 체크

- 상태: `release_candidate_ready` / backlog 감축 턴에서 새 후보 생성 없이 `비슷해 보이는 위치형 집 나누기` 표를 추가해 창밖 거리감 후보를 주차장·저층·코너집 불안과 분리했다. review 통과 (`ready=19 hard=0 soft=0`, 해당 후보 chars=5386 visuals=10, target_fit=True). 품질 통과 글은 keep하고 dedicated publisher desk의 adaptive 슬롯에 맡긴다.
- 최종본: `release_candidates/2026-05/window-distance-daylight-privacy-check/final.html`
- 메타: `release_candidates/2026-05/window-distance-daylight-privacy-check/metadata.json`
- 검증: `reports/cron-review-latest.md`; hourly smoke pass (`ready=19 hard=0 soft=0 warnings=0`); publisher adaptive 상태는 spacing/day guard를 기록하며 발행부 슬롯이 열리면 실제 GitHub Pages 공개까지 수행한다.
- Stage notes:
  - [x] 00-topic: `articles/2026-05/window-distance-daylight-privacy-check/00-topic.md`
  - [x] 10-source: `articles/2026-05/window-distance-daylight-privacy-check/10-source.md`
  - [x] 20-data-qa: `articles/2026-05/window-distance-daylight-privacy-check/20-data-qa.md`
  - [x] 30-story: `articles/2026-05/window-distance-daylight-privacy-check/30-story.md`
  - [x] 40-visual: `articles/2026-05/window-distance-daylight-privacy-check/40-visual-plan.md`
  - [x] 50-copy: `articles/2026-05/window-distance-daylight-privacy-check/50-copy.md`
  - [x] 60-reader-qa: `articles/2026-05/window-distance-daylight-privacy-check/60-reader-qa.md`
  - [x] 70-final-html: `articles/2026-05/window-distance-daylight-privacy-check/70-final-html.md`
  - [x] 70-publish note: `articles/2026-05/window-distance-daylight-privacy-check/70-publish-note.md`
  - [x] 80-growth: `articles/2026-05/window-distance-daylight-privacy-check/80-growth.md`

### P. 주차장 출입구 옆 집, 조용한지 보기 전 확인할 12분

- 상태: `release_candidate_ready` / backlog 감축 턴에서 새 후보 생성 없이 `비슷한 위치형 집과 나란히 보기` 표를 추가해 주차장 출입구·골목 코너·버스정류장·창밖 거리감 후보를 서로 다른 질문으로 분리했다. review 통과 (`ready=19 hard=0 soft=0`, 해당 후보 chars=5438 visuals=10, target_fit=True). 품질 통과 글은 keep하고 dedicated publisher desk의 adaptive 슬롯에 맡긴다.
- 최종본: `release_candidates/2026-05/parking-entrance-home-check/final.html`
- 메타: `release_candidates/2026-05/parking-entrance-home-check/metadata.json`
- 검증: `reports/cron-review-latest.md`; 발행부 adaptive 슬롯이 열리면 GitHub Pages 공개까지 수행한다.
- Stage notes:
  - [x] 00-topic: `articles/2026-05/parking-entrance-home-check/00-topic.md`
  - [x] 10-source: `articles/2026-05/parking-entrance-home-check/10-source.md`
  - [x] 20-data-qa: `articles/2026-05/parking-entrance-home-check/20-data-qa.md`
  - [x] 30-story: `articles/2026-05/parking-entrance-home-check/30-story.md`
  - [x] 40-visual: `articles/2026-05/parking-entrance-home-check/40-visual-plan.md`
  - [x] 50-copy: `articles/2026-05/parking-entrance-home-check/50-copy.md`
  - [x] 60-reader-qa: `articles/2026-05/parking-entrance-home-check/60-reader-qa.md`
  - [x] 70-final-html: `articles/2026-05/parking-entrance-home-check/70-final-html.md`
  - [x] 70-publish note: `articles/2026-05/parking-entrance-home-check/70-publish-note.md`
  - [x] 80-growth: `articles/2026-05/parking-entrance-home-check/80-growth.md`

### Q. 분리수거장 앞 집, 냄새보다 먼저 볼 생활 동선 체크

- 상태: `release_candidate_ready` / backlog 감축 턴에서 새 후보 생성 없이 `비슷해 보이는 생활 불편 후보 나누기` 표를 추가해 분리수거장·식당·공동현관·주차장 후보의 중복 불안을 분리했다. review 통과 (`ready=19 hard=0 soft=0`, 해당 후보 chars=5386 visuals=10, target_fit=True). 품질 통과 글은 keep하고 dedicated publisher desk의 adaptive 슬롯에 맡긴다.
- 최종본: `release_candidates/2026-05/recycling-area-home-check/final.html`
- 메타: `release_candidates/2026-05/recycling-area-home-check/metadata.json`
- 검증: `reports/cron-review-latest.md`; hourly smoke pass (`ready=19 hard=0 soft=0 warnings=0`); publisher dry-run은 `maintenance-fee-opaque-rent`를 다음 공개 후보로 selected 했고 발행부 adaptive 슬롯이 열리면 GitHub Pages 공개까지 수행한다.
- Stage notes:
  - [x] 00-topic: `articles/2026-05/recycling-area-home-check/00-topic.md`
  - [x] 10-source: `articles/2026-05/recycling-area-home-check/10-source.md`
  - [x] 20-data-qa: `articles/2026-05/recycling-area-home-check/20-data-qa.md`
  - [x] 30-story: `articles/2026-05/recycling-area-home-check/30-story.md`
  - [x] 40-visual: `articles/2026-05/recycling-area-home-check/40-visual-plan.md`
  - [x] 50-copy: `articles/2026-05/recycling-area-home-check/50-copy.md`
  - [x] 60-reader-qa: `articles/2026-05/recycling-area-home-check/60-reader-qa.md`
  - [x] 70-final-html: `articles/2026-05/recycling-area-home-check/70-final-html.md`
  - [x] 70-publish note: `articles/2026-05/recycling-area-home-check/70-publish-note.md`
  - [x] 80-growth: `articles/2026-05/recycling-area-home-check/80-growth.md`

### R. 편의점 바로 위 집, 편리함보다 먼저 볼 밤 소리 체크

- 상태: `release_candidate_ready` / backlog 감축 턴에서 새 후보 생성 없이 `생활 리듬별 우선 확인 순서` 표를 추가해 편의점 가까움의 계속 보기/보류 판단을 야근 귀가·재택·빠른 출근·빛/소리 민감 독자 루틴별로 분리했다. review 통과 (`ready=19 hard=0 soft=0`, 해당 후보 chars=5215 visuals=10). 품질 통과 글은 keep하고 dedicated publisher desk의 adaptive 슬롯에 맡긴다.
- 최종본: `release_candidates/2026-05/convenience-store-upstairs-night-noise-check/final.html`
- 메타: `release_candidates/2026-05/convenience-store-upstairs-night-noise-check/metadata.json`
- 검증: `reports/cron-review-latest.md`; 발행부 adaptive 슬롯이 열리면 GitHub Pages 공개까지 수행한다.
- Stage notes:
  - [x] 00-topic: `articles/2026-05/convenience-store-upstairs-night-noise-check/00-topic.md`
  - [x] 10-source: `articles/2026-05/convenience-store-upstairs-night-noise-check/10-source.md`
  - [x] 20-data-qa: `articles/2026-05/convenience-store-upstairs-night-noise-check/20-data-qa.md`
  - [x] 30-story: `articles/2026-05/convenience-store-upstairs-night-noise-check/30-story.md`
  - [x] 40-visual: `articles/2026-05/convenience-store-upstairs-night-noise-check/40-visual-plan.md`
  - [x] 50-copy: `articles/2026-05/convenience-store-upstairs-night-noise-check/50-copy.md`
  - [x] 60-reader-qa: `articles/2026-05/convenience-store-upstairs-night-noise-check/60-reader-qa.md`
  - [x] 70-final-html: `articles/2026-05/convenience-store-upstairs-night-noise-check/70-final-html.md`
  - [x] 70-publish note: `articles/2026-05/convenience-store-upstairs-night-noise-check/70-publish-note.md`
  - [x] 80-growth: `articles/2026-05/convenience-store-upstairs-night-noise-check/80-growth.md`

### S. 1층 식당 위 집, 냄새보다 먼저 볼 배기와 퇴근 시간 동선

- 상태: `release_candidate_ready` / backlog 감축 턴에서 새 후보 생성 없이 `비슷한 생활 불편 후보와 나누기` 표를 추가해 편의점·분리수거장·주차장 출입구 후보와 식당 후보의 반복 시간·위치·충돌 지점을 분리했다. review 통과 (`ready=19 hard=0 soft=0`, 해당 후보 chars=5086 visuals=11, target_fit=True). 품질 통과 글은 keep하고 dedicated publisher desk의 adaptive 슬롯에 맡긴다.
- 최종본: `release_candidates/2026-05/restaurant-upstairs-vent-route-check/final.html`
- 메타: `release_candidates/2026-05/restaurant-upstairs-vent-route-check/metadata.json`
- 검증: `reports/cron-review-latest.md`; 발행부 adaptive 슬롯이 열리면 GitHub Pages 공개까지 수행한다.
- Stage notes:
  - [x] 00-topic: `articles/2026-05/restaurant-upstairs-vent-route-check/00-topic.md`
  - [x] 10-source: `articles/2026-05/restaurant-upstairs-vent-route-check/10-source.md`
  - [x] 20-data-qa: `articles/2026-05/restaurant-upstairs-vent-route-check/20-data-qa.md`
  - [x] 30-story: `articles/2026-05/restaurant-upstairs-vent-route-check/30-story.md`
  - [x] 40-visual: `articles/2026-05/restaurant-upstairs-vent-route-check/40-visual-plan.md`
  - [x] 50-copy: `articles/2026-05/restaurant-upstairs-vent-route-check/50-copy.md`
  - [x] 60-reader-qa: `articles/2026-05/restaurant-upstairs-vent-route-check/60-reader-qa.md`
  - [x] 70-final-html: `articles/2026-05/restaurant-upstairs-vent-route-check/70-final-html.md`
  - [x] 70-publish note: `articles/2026-05/restaurant-upstairs-vent-route-check/70-publish-note.md`
  - [x] 80-growth: `articles/2026-05/restaurant-upstairs-vent-route-check/80-growth.md`

### T. 골목 코너 집, 개방감보다 먼저 볼 회전 차량과 창문 거리

- 상태: `release_candidate_ready` / 50-copy_pass 후보를 final.html로 패키징한 뒤, backlog 감축 턴에서 좋은 반례·판단 보류 완화 단락을 추가했다. 이번 턴에는 새 후보 생성 없이 `비슷한 위치형 집과 헷갈리지 않는 기준` 섹션과 `위치형 후보 역할 분리 카드`를 추가해 코너 집/주차장 출입구/창밖 거리감 후보의 중복 오독을 줄였다. review 통과 (`ready=19 hard=0 soft=0`, 해당 후보 chars=5308 visuals=11 target_fit=True). 품질 통과 글은 keep하고 dedicated publisher desk의 adaptive 슬롯에 맡긴다.
- 최종본: `release_candidates/2026-05/corner-home-turning-car-window-distance-check/final.html`
- 메타: `release_candidates/2026-05/corner-home-turning-car-window-distance-check/metadata.json`
- 검증: `reports/cron-review-latest.md`; hourly smoke pass (`ready=19 hard=0 soft=0 warnings=0`); publisher adaptive 상태는 spacing/day guard를 기록하며 발행부 슬롯이 열리면 실제 GitHub Pages 공개까지 수행한다.
- Stage notes:
  - [x] 00-topic: `articles/2026-05/corner-home-turning-car-window-distance-check/00-topic.md`
  - [x] 10-source: `articles/2026-05/corner-home-turning-car-window-distance-check/10-source.md`
  - [x] 20-data-qa: `articles/2026-05/corner-home-turning-car-window-distance-check/20-data-qa.md`
  - [x] 30-story: `articles/2026-05/corner-home-turning-car-window-distance-check/30-story.md`
  - [x] 40-visual: `articles/2026-05/corner-home-turning-car-window-distance-check/40-visual-plan.md`
  - [x] 50-copy: `articles/2026-05/corner-home-turning-car-window-distance-check/50-copy.md`
  - [x] 60-reader-qa: `articles/2026-05/corner-home-turning-car-window-distance-check/60-reader-qa.md`
  - [x] 70-final-html: `articles/2026-05/corner-home-turning-car-window-distance-check/70-final-html.md`
  - [x] 70-publish note: `articles/2026-05/corner-home-turning-car-window-distance-check/70-publish-note.md`
  - [x] 80-growth: `articles/2026-05/corner-home-turning-car-window-distance-check/80-growth.md`

### U. 엘리베이터 앞 집, 편한 동선인지 시끄러운 대기실인지 보는 12분

- 상태: `release_candidate_ready` / replenish 턴에서 00-topic→70-final-html까지 완성한 뒤, 이번 hourly normal 턴에서 새 후보 양산 없이 복도 끝·공동현관 후보와 헷갈리지 않도록 공용부 후보 분리 figure/table을 추가했다. review 통과 (`ready=5 hard=0 soft=0`, 해당 후보 chars=5115 visuals=9, target_fit=True). 품질 통과 글은 keep하고 dedicated publisher desk의 adaptive 슬롯·정책에 맡긴다.
- 최종본: `release_candidates/2026-05/elevator-front-home-check/final.html`
- 메타: `release_candidates/2026-05/elevator-front-home-check/metadata.json`
- 검증: `reports/cron-review-latest.md`; hourly smoke pass (`ready=5 hard=0 soft=0 warnings=0`); publisher dry-run은 `slot_closed`라 실제 공개/푸시 없음.
- Stage notes:
  - [x] 00-topic: `articles/2026-05/elevator-front-home-check/00-topic.md`
  - [x] 10-source: `articles/2026-05/elevator-front-home-check/10-source.md`
  - [x] 20-data-qa: `articles/2026-05/elevator-front-home-check/20-data-qa.md`
  - [x] 30-story: `articles/2026-05/elevator-front-home-check/30-story.md`
  - [x] 40-visual: `articles/2026-05/elevator-front-home-check/40-visual-plan.md`
  - [x] 50-copy: `articles/2026-05/elevator-front-home-check/50-copy.md`
  - [x] 60-reader-qa: `articles/2026-05/elevator-front-home-check/60-reader-qa.md`
  - [x] 70-final-html: `articles/2026-05/elevator-front-home-check/70-final-html.md`
  - [x] 70-publish note: `articles/2026-05/elevator-front-home-check/70-publish-note.md`
  - [x] 80-growth: `articles/2026-05/elevator-front-home-check/80-growth.md`

### V. 대로변 한 블록 안쪽 집, 조용함인지 고립감인지 보는 밤 12분

- 상태: `release_candidate_ready` / replenish 턴에서 00-topic→70-final-html까지 완성. 이후 결론을 본문 맨 끝으로 이동하고 밤길·정류장·공동현관 후보와 질문을 분리한 뒤, 2026-05-06 13:37 hourly normal 턴에서 다음 클릭 선택 섹션·카드·표를 추가했다. 2026-05-06 21:44 턴에서는 새 후보 양산 없이 meta의 `안전한 조용함` 과장 가능성을 `생활에 맞는 조용함`으로 낮추고, 세 칸 기록 섹션·카드·표를 추가해 마지막 한 블록 신호를 끊긴 지점·반복 장면·다음 질문으로 적게 했다. review 통과 (`ready=6 hard=0 soft=0`, 해당 후보 chars=5723 visuals=11, target_fit=True). 품질 통과 글은 keep하고 dedicated publisher desk의 adaptive 슬롯·정책에 맡긴다.
- 최종본: `release_candidates/2026-05/one-block-inside-main-road-check/final.html`
- 메타: `release_candidates/2026-05/one-block-inside-main-road-check/metadata.json`
- 검증: `reports/cron-review-latest.md`; hourly smoke pass (`ready=6 hard=0 soft=0`, warning-only live deployment drift 1건); publisher dry-run은 `slot_closed`(`ready_unpublished=3<=ready_target=7`, `daily_floor_open=False`, spacing open)라 실제 공개/푸시 없음.
- Stage notes:
  - [x] 00-topic: `articles/2026-05/one-block-inside-main-road-check/00-topic.md`
  - [x] 10-source: `articles/2026-05/one-block-inside-main-road-check/10-source.md`
  - [x] 20-data-qa: `articles/2026-05/one-block-inside-main-road-check/20-data-qa.md`
  - [x] 30-story: `articles/2026-05/one-block-inside-main-road-check/30-story.md`
  - [x] 40-visual: `articles/2026-05/one-block-inside-main-road-check/40-visual-plan.md`
  - [x] 50-copy: `articles/2026-05/one-block-inside-main-road-check/50-copy.md`
  - [x] 60-reader-qa: `articles/2026-05/one-block-inside-main-road-check/60-reader-qa.md`
  - [x] 70-final-html: `articles/2026-05/one-block-inside-main-road-check/70-final-html.md`
  - [x] 70-publish note: `articles/2026-05/one-block-inside-main-road-check/70-publish-note.md`
  - [x] 80-growth: `articles/2026-05/one-block-inside-main-road-check/80-growth.md`

### W. 복도 끝 집, 조용함인지 사각지대인지 보는 밤 12분

- 상태: `published_to_pages` / ready_unpublished 최소 3개를 채운 뒤 공용부 후보 분리 figure/table을 추가했고, 2026-05-06 15:43 hourly normal 턴에서 새 후보 양산 없이 다음 확인 선택 figure/table을 더해 복도 끝 불안을 밤길·공동현관·엘리베이터 앞·대로변 한 블록 중 하나로만 이어 보게 했다. 2026-05-06 23:37 턴에서는 관리·중개 답변을 결론이 아니라 시간·위치·재방문 조건으로 바꾸는 figure/table/섹션을 추가했다. 2026-05-07 04:37 턴에서는 검색어를 조용함 판단이 아니라 밤 귀가·시야·방 안 소리 현장 질문으로 전환하는 figure/table/섹션을 추가했다. 2026-05-07 08:40 턴에서는 동거인/가족에게 감정이 아니라 확인한 시간·위치·다음 행동으로 설명하는 figure/table/섹션을 추가했다. 2026-05-07 17:44 턴에서는 후속 클릭 선택 figure/섹션을 추가해 밖길·문 앞·방 안 중 가장 큰 빈칸 하나만 다음 비교 글로 보내게 했다. 2026-05-07 21:37 턴에서는 meta description을 서울·수도권 25~39세 전월세·이사 독자와 밤 귀가 시야·문 앞 머무름·방 안 소리 질문 중심으로 좁혀 검색 스니펫부터 타겟/결정상황이 보이게 했다. 2026-05-08 00:42에는 GitHub Pages `/radar/corridor-end-home-check/` 공개 후 카드/갤러리/photo-scan 품질 게이트를 위해 public thumbnail 1개와 AI field-example WebP 3개를 연결했다. review 통과 (`ready=7 hard=0 soft=0`, 해당 후보 chars=6999 visuals=15, target_fit=True, observations=0). 품질 통과 기록은 보존하고 다음 발행/보강은 dedicated publisher desk와 backlog policy를 따른다.
- 최종본: `release_candidates/2026-05/corridor-end-home-check/final.html`
- 메타: `release_candidates/2026-05/corridor-end-home-check/metadata.json`
- 검증: `reports/cron-review-latest.md`; hourly smoke pass (`ready=7 hard=0 soft=0`, warning-only live deployment drift 1건은 전체 사이트 홈/상업지도 marker 계열이며 W `/radar/` 직접 배포는 확인 완료); `scripts/build_site.py && scripts/audit_public_site_quality.py` 통과. publisher 최신 dry-run은 `slot_closed`(`ready_unpublished=2<=ready_target=7`, `published_today=1`, `hours_since_last=0.458<2h`)라 추가 후보 공개는 없었고, 이미 `published_to_pages`로 기록된 W의 미푸시 public visual asset 복구 커밋 `4ea0419`를 GitHub Pages main에 push했다. Live checks: `/radar/corridor-end-home-check/` 200, `/radar/` 200, thumbnail WebP 200.
- Stage notes:
  - [x] 00-topic: `articles/2026-05/corridor-end-home-check/00-topic.md`
  - [x] 10-source: `articles/2026-05/corridor-end-home-check/10-source.md`
  - [x] 20-data-qa: `articles/2026-05/corridor-end-home-check/20-data-qa.md`
  - [x] 30-story: `articles/2026-05/corridor-end-home-check/30-story.md`
  - [x] 40-visual: `articles/2026-05/corridor-end-home-check/40-visual-plan.md`
  - [x] 50-copy: `articles/2026-05/corridor-end-home-check/50-copy.md`
  - [x] 60-reader-qa: `articles/2026-05/corridor-end-home-check/60-reader-qa.md`
  - [x] 70-final-html: `articles/2026-05/corridor-end-home-check/70-final-html.md`
  - [x] 70-publish note: `articles/2026-05/corridor-end-home-check/70-publish-note.md`
  - [x] 80-growth: `articles/2026-05/corridor-end-home-check/80-growth.md`

### X. 택배함·우편함 옆 집, 계속 볼지 보류할지 보는 10분

- 상태: `published_to_pages` / ready_unpublished가 최신 publisher 기준 2개로 내려간 상태를 보정하기 위해 신규 replenish 후보를 00-topic→70-final-html까지 완성한 뒤, 제목/H1/meta와 공개 `/radar/` 다음 클릭 표를 보강했다. 2026-05-06 18:39 hourly normal 턴에서는 관리 답변을 증거가 아니라 재확인 조건으로 바꾸는 섹션·검증 카드·표를 추가했다. 2026-05-07 03:36 턴에서는 새 후보 양산 없이 검색어를 장단점 목록이 아니라 현장 질문·기록 한 줄로 바꾸는 섹션·reader visual·표를 추가해 `택배함 옆 집/우편함 옆 원룸/현관 앞 택배 소음` 유입을 문 앞 머무름·반복 시간·방 안 소리 체크로 전환했다. 2026-05-07 06:38 턴에서는 새 후보 양산 없이 방 안 소리를 현관 안쪽·책상/침대 자리·다시 볼 시간대로 나누는 섹션·reader visual·표를 추가해 `문 앞에서 들림`과 `생활 피로`를 분리했다. 2026-05-07 09:37 턴에서는 같이 결정하는 사람에게 감상 대신 시간·위치·방 안 생활 자리 확인 요청으로 말하는 섹션·reader visual·표를 추가했다. 2026-05-07 15:18 턴에서는 사람·주소 단서를 남기지 않고 시간·위치·반복 장면만 기록하는 안전 메모 섹션·reader visual·표를 추가하고 본문을 7,000자로 압축해 editorial observation을 제거했다. 2026-05-07 19:50 턴에서는 meta description을 `문 앞 반복 장면` 중심으로 좁히고 방 안 소리 단락의 일반 해석 문장을 독자 사용법 문장으로 바꿔 검색 스니펫과 본문 사용 흐름을 맞췄다. 2026-05-07 23:49 턴에서는 새 후보 양산 없이 안전 기록 섹션을 `송장 말고 장면만`으로 좁혀 호수·얼굴·송장번호·이름·전화번호 같은 식별 단서를 빼고 방향·폭·시간·방 안 전달 여부만 남기게 했다. 2026-05-08 14:47 턴에서는 publish guard를 막던 thumbnail/field-example media blocker를 repo-local WebP 4개와 metadata field_examples 3개로 해소했다. 2026-05-08 16:43 턴에서는 기록 예시의 `보관함 앞 1명`을 `보관함 앞 짧은 머무름`으로 바꿔 사람 수·주민/배송 추적처럼 읽힐 여지를 제거했다. 2026-05-09 00:47에 GitHub Pages `/radar/parcel-mailbox-front-home-check/` content source로 공개되었고, 최신 review에서도 published=True/ready=True로 보존한다. 품질 통과 기록은 keep하고 다음 후보는 dedicated publisher desk의 adaptive 슬롯·정책에 맡긴다.
- 최종본: `release_candidates/2026-05/parcel-mailbox-front-home-check/final.html`
- 메타: `release_candidates/2026-05/parcel-mailbox-front-home-check/metadata.json`
- 검증: `reports/cron-review-latest.md`; hourly smoke pass(`ready=9 hard=0 soft=0`, warnings=0). 2026-05-09 01:11 기준 X는 published=True/ready=True, chars=7000 visuals=15 target_fit=True observations=0 media_blockers=0 internal_links=9이며, privacy terms는 `남기지 않음` 안전 문맥이다. 최신 publisher dry-run은 신규 미발행 3개 기준 `slot_closed`라 이번 턴 추가 공개/푸시 없음.
- Stage notes:
  - [x] 00-topic: `articles/2026-05/parcel-mailbox-front-home-check/00-topic.md`
  - [x] 10-source: `articles/2026-05/parcel-mailbox-front-home-check/10-source.md`
  - [x] 20-data-qa: `articles/2026-05/parcel-mailbox-front-home-check/20-data-qa.md`
  - [x] 30-story: `articles/2026-05/parcel-mailbox-front-home-check/30-story.md`
  - [x] 40-visual: `articles/2026-05/parcel-mailbox-front-home-check/40-visual-plan.md`
  - [x] 50-copy: `articles/2026-05/parcel-mailbox-front-home-check/50-copy.md`
  - [x] 60-reader-qa: `articles/2026-05/parcel-mailbox-front-home-check/60-reader-qa.md`
  - [x] 70-final-html: `articles/2026-05/parcel-mailbox-front-home-check/70-final-html.md`
  - [x] 70-publish note: `articles/2026-05/parcel-mailbox-front-home-check/70-publish-note.md`
  - [x] 80-growth: `articles/2026-05/parcel-mailbox-front-home-check/80-growth.md`

### Y. 최상층 집, 전망보다 먼저 볼 여름·누수·소리 체크 12분

- 상태: `release_candidate_ready` / publisher 기준 ready_unpublished가 최소 3개에서 흔들리지 않도록 신규 replenish 후보를 00-topic→70-final-html까지 완성했다. 최상층 집의 전망 장점을 바로 결론으로 두지 않고, 서울·수도권 25~39세 전월세·이사 독자가 여름 열기·비 흔적·옥상/기계실/계단실 소리를 12분 현장 질문으로 바꿔 계속 볼지/보류할지 판단하게 했다. 1차 review의 `body_below_target` soft issue를 reader-facing 문단 보강으로 해소했고, 이후 검색어 전환·계절별 빈칸·중개인 확인 문장·후속 후보 비교·동거인 공유·source/calc caveat를 단계적으로 보강했다. 2026-05-09 07:41 턴에는 inline SVG/`field-visual` visual을 repo-local AI 실사 WebP photo cards로 교체했고, 2026-05-09 08:46 턴에는 section 9 `재방문은 많이 하는 것이 아니라 빈칸 하나를 채우는 일입니다`를 압축해 열기·비 흔적·소리 중 아직 비어 있는 조건 하나만 재확인하게 했다. 최종 review 통과(`ready=True hard=0 soft=0`, chars=6748 visuals=32 target_fit=True media_blockers=0). 품질 통과 글은 keep하고 dedicated publisher desk의 adaptive 슬롯·정책에 맡긴다.
- 최종본: `release_candidates/2026-05/top-floor-heat-leak-noise-check/final.html`
- 메타: `release_candidates/2026-05/top-floor-heat-leak-noise-check/metadata.json`
- 검증: `reports/cron-review-latest.md`; hourly smoke pass(`ready=9 hard=0 soft=0`, warnings=0); latest publisher dry-run은 `slot_closed`(`ready_unpublished=3<=ready_target=7`, `daily_floor_open=False`, `published_today=1/4`, `spacing_open=True`, `hours_since_last=8.085`)라 이번 턴 실제 공개/푸시 없음. 2026-05-09 08:52 기준 Y는 chars=6748 visuals=32 target_fit=True hard=0 soft=0 observations=0 media_blockers=0 eligible=True internal_links=9이며, source/ranking terms는 caveat 문맥이다.
- Stage notes:
  - [x] 00-topic: `articles/2026-05/top-floor-heat-leak-noise-check/00-topic.md`
  - [x] 10-source: `articles/2026-05/top-floor-heat-leak-noise-check/10-source.md`
  - [x] 20-data-qa: `articles/2026-05/top-floor-heat-leak-noise-check/20-data-qa.md`
  - [x] 30-story: `articles/2026-05/top-floor-heat-leak-noise-check/30-story.md`
  - [x] 40-visual: `articles/2026-05/top-floor-heat-leak-noise-check/40-visual-plan.md`
  - [x] 50-copy: `articles/2026-05/top-floor-heat-leak-noise-check/50-copy.md`
  - [x] 60-reader-qa: `articles/2026-05/top-floor-heat-leak-noise-check/60-reader-qa.md`
  - [x] 70-final-html: `articles/2026-05/top-floor-heat-leak-noise-check/70-final-html.md`
  - [x] 70-publish note: `articles/2026-05/top-floor-heat-leak-noise-check/70-publish-note.md`
  - [x] 80-growth: `articles/2026-05/top-floor-heat-leak-noise-check/80-growth.md`

### Z. 창문 아래 주차선 집, 계속 볼지 보류할지 보는 밤 10분

- 상태: `release_candidate_ready` / 2026-05-08 01:45 replenish 후보로 00-topic→70-final-html까지 완성했으나 1차 deterministic review에서 `body_below_target:4365<4500` soft issue가 나왔다. 2026-05-08 02:37 턴에서 검색 유입 독자가 다음 방문 시간 하나와 방 안 자리 하나를 정하게 하는 reader-facing 문단을 추가해 soft issue를 해소했다. 2026-05-08 03:45 턴에서는 새 후보 양산 없이 후속 클릭을 공개된 밤 소음·1층집·복도 끝 글 중 하나로 좁히는 문단·표·figure를 추가해 내부 탐색 과밀을 줄였다. 2026-05-08 04:46 턴에서는 지도·로드뷰는 방향 확인, 현장 메모는 비식별 장면 기록, 관리 답변은 재확인 조건으로만 쓰는 자료/사생활 경계 문단·표를 추가했다. 2026-05-08 05:36 턴에서는 마지막 한 줄 메모 템플릿을 추가해 좋은 반례·보류 질문·재방문 조건을 시간·방향·방 안 자리·다음 확인으로 끝내게 했다. 2026-05-08 10:47 턴에서는 숫자형 오독을 줄이기 위해 주차선 수·차량 수·소리 크기를 세지 않고 시간대·방향·방 안 전달 여부/생활 자리 단위로 낮추는 섹션·표·reader visual을 추가했다. 2026-05-08 12:37 턴에서는 차를 자주 쓰는 독자도 바로 보류하지 않도록 주차 편리함과 쉬는 시간 피로를 `내 이동 시간 / 쉬는 시간 / 재확인`으로 나누는 섹션·표·reader visual을 추가했다. 2026-05-08 13:43 턴에서는 다음 방문 예약을 `시간 하나 / 방 안 자리 하나 / 같이 말할 문장 하나`로 끝내는 섹션·표·reader visual을 추가해 재확인 행동을 더 좁혔다. 2026-05-08 14:47 턴에서는 publish guard를 막던 thumbnail/field-example media blocker를 repo-local WebP 4개와 metadata field_examples 3개로 해소했다. 2026-05-08 15:42 턴에서는 기준월·표본 없는 주차 민원/소음 설명을 순위처럼 쓰지 않고 다음 방문 시간·방향·방 안 자리 빈칸으로만 남기는 source/basis caveat를 자료 경계 문단에 추가했다. 2026-05-08 17:39 턴에서는 비 온 뒤·겨울철 창문 닫힘·여름 환기처럼 계절/날씨가 바뀌는 조건을 확정값이 아니라 다시 볼 질문으로만 두는 caveat를 추가했다. 최종 review 통과 (`ready=True hard=0 soft=0`, 해당 후보 chars=6902 visuals=30 photo_cards=15 target_fit=True media_blockers=0 eligible=True). 품질 통과 글은 keep하고 dedicated publisher desk의 adaptive 슬롯·정책에 맡긴다.
- 최종본: `release_candidates/2026-05/parking-line-under-window-check/final.html`
- 메타: `release_candidates/2026-05/parking-line-under-window-check/metadata.json`
- 검증: `reports/cron-review-latest.md`; latest publisher dry-run은 `slot_closed`(`ready_unpublished=3<=ready_target=7`, `daily_floor_open=False`, `published_today=1/4`, `spacing_open=True`, `hours_since_last=8.085`)라 이번 턴 실제 공개/푸시 없음. 2026-05-09 08:52 기준 Z는 chars=6902 visuals=30 photo_cards=15 target_fit=True observations=0 hard=0 soft=0 media_blockers=0 eligible=True internal_links=3. Hourly smoke pass(warnings=0). Z는 다음 안전 작업 시 internal-link density review 우선이다.
- Stage notes:
  - [x] 00-topic: `articles/2026-05/parking-line-under-window-check/00-topic.md`
  - [x] 10-source: `articles/2026-05/parking-line-under-window-check/10-source.md`
  - [x] 20-data-qa: `articles/2026-05/parking-line-under-window-check/20-data-qa.md`
  - [x] 30-story: `articles/2026-05/parking-line-under-window-check/30-story.md`
  - [x] 40-visual: `articles/2026-05/parking-line-under-window-check/40-visual-plan.md`
  - [x] 50-copy: `articles/2026-05/parking-line-under-window-check/50-copy.md`
  - [x] 60-reader-qa: `articles/2026-05/parking-line-under-window-check/60-reader-qa.md`
  - [x] 70-final-html: `articles/2026-05/parking-line-under-window-check/70-final-html.md`
  - [x] 70-publish note: `articles/2026-05/parking-line-under-window-check/70-publish-note.md`
  - [x] 80-growth: `articles/2026-05/parking-line-under-window-check/80-growth.md`

### AA. 빨래 건조대 자리 없는 집, 계속 볼지 보류할지 보는 12분

- 상태: `release_candidate_ready` / 2026-05-09 00:58 hourly replenish 후보로 00-topic→70-final-html까지 완성했다. 독자는 서울·수도권 25~39세 전월세·이사 후보 비교자이며, 결정상황은 방 크기 인상이 아니라 젖은 옷을 옮기고 건조대를 펼치고 통로와 환기를 유지할 수 있는지 12분 현장 관찰로 계속 볼지/보류할지 고르는 일이다. 1차 review의 `body_below_target:3668<4500` soft issue는 생활 리듬별 보류선, 후속 내부링크 결정 섹션, 마지막 확인 문장 보강으로 해소했다. 2026-05-09 03:36 턴에서는 새 후보를 만들지 않고 첫 화면 lead에 `바닥 한 칸에 건조대를 펼친다고 가정하고 세탁하는 날 현관-책상-창문 길이 살아 있는지 먼저 적기` 문장을 추가해 다음 방문 사용법을 더 직접적으로 만들었다. 2026-05-09 04:40 턴에서는 `환기 잘 된다` 같은 흐린 관리 답변을 결론이 아니라 `창문 5분/책상 길/욕실 문 앞 습기` 재확인 질문으로 낮추는 source-caveat 문장을 보강했다. 2026-05-09 05:49 턴에서는 독자-visible 후속 클릭 문단/표에서 미공개 최상층 후보 직접 링크를 제거하고, 공개 완료된 `/radar/rainy-day-viewing-neighborhood-signals/`로 비·습기 흔적 경로를 연결했다. 2026-05-09 06:39 턴에서는 후속 클릭 선택 카드를 추가해 남은 불안을 창문·습기·문 앞 중 하나로만 고르게 했다. 2026-05-09 07:41 턴에서는 inline SVG/`field-visual` visual을 repo-local AI 실사 WebP photo cards로 교체해 AA final.html의 photo cards를 12개로 정렬했고 SVG/field-visual residue는 0이다. 외부 통계·건물별 습도 확률·계절별 확정값·순위형 결론은 쓰지 않고, 욕실 문 앞/창문 방향/건조대 펼친 뒤 통로/빨래 바구니 자리/다음 재방문 시간처럼 관찰 가능한 기준으로 낮췄다. 최종 review 통과(`ready=True target_fit=True chars=4784 visuals=24 hard=0 soft=0 media_blockers=0 eligible=True`). 품질 통과 글은 keep하고 dedicated publisher desk의 adaptive 슬롯·정책에 맡긴다.
- 최종본: `release_candidates/2026-05/laundry-drying-route-home-check/final.html`
- 메타: `release_candidates/2026-05/laundry-drying-route-home-check/metadata.json`
- 검증: `reports/cron-review-latest.md`; latest adaptive dry-run은 `slot_closed`(`ready_unpublished=3<=ready_target=7`, `daily_floor_open=False`, `published_today=1/4`, `spacing_open=True`, `hours_since_last=8.085`)라 이번 턴 실제 공개/푸시 없음. 2026-05-09 08:52 기준 AA는 chars=4784 visuals=24 photo_cards=12 target_fit=True hard=0 soft=0 media_blockers=0 eligible=True. Hourly smoke pass(warnings=0, 2026-05-09T08:52:29+09:00). 다음 성장 작업은 공개 후 `세탁실 없음/원룸 빨래 건조/습기 냄새` 검색 의도를 창문·습기·문 앞 중 하나로 좁힌 뒤 공개 완료된 후속 내부링크로만 분기하는 것이다.
- Stage notes:
  - [x] 00-topic: `articles/2026-05/laundry-drying-route-home-check/00-topic.md`
  - [x] 10-source: `articles/2026-05/laundry-drying-route-home-check/10-source.md`
  - [x] 20-data-qa: `articles/2026-05/laundry-drying-route-home-check/20-data-qa.md`
  - [x] 30-story: `articles/2026-05/laundry-drying-route-home-check/30-story.md`
  - [x] 40-visual: `articles/2026-05/laundry-drying-route-home-check/40-visual-plan.md`
  - [x] 50-copy: `articles/2026-05/laundry-drying-route-home-check/50-copy.md`
  - [x] 60-reader-qa: `articles/2026-05/laundry-drying-route-home-check/60-reader-qa.md`
  - [x] 70-final-html: `articles/2026-05/laundry-drying-route-home-check/70-final-html.md`
  - [x] 70-publish note: `articles/2026-05/laundry-drying-route-home-check/70-publish-note.md`
  - [x] 80-growth: `articles/2026-05/laundry-drying-route-home-check/80-growth.md`

## Department handoff

- 출판관리부: 10:13 deterministic review/publisher 기준 candidates=9 / ready=9 / review-surface published=6 / ready_unpublished=3 / eligible_unpublished=3 / published_today=1/4. 모드는 `normal/minimum-buffer`이며 새 후보 양산이나 backlog_reduction이 아니라 queue-order·품질 선명도 유지 턴이다.
- 기획부: 이번 턴은 타겟 실패나 분량 부족이 아니라 handoff freshness 정리였다. Y/Z/AA 모두 서울·수도권 25~39세 전월세·이사 독자와 계속 볼지/보류할지 결정상황은 통과했다.
- 자료수집부: Y/Z/AA 모두 repo-local AI 실사 WebP field examples를 사용한다. 새 외부 확률·민원 순위·건물별 단정·주소/개인 식별·차량/사람 추적 근거를 추가하지 않았다.
- 데이터검증부: Y/Z/AA는 점수·확률·지역 순위·일괄 추천을 만들지 않는다. 최신 dry-run의 blocker는 콘텐츠 불합격이 아니라 queue guard(`ready_unpublished=3<=ready_target=7`, `daily_floor_open=False`)다.
- 편집부: 새 본문/새 후보를 만들지 않고 `IDEA_BANK.md`의 최신 buffer read와 next-use rule을 Y/Z/AA 기준으로 정렬했다. filler prose를 추가하지 않았다.
- 그래픽부: Y/Z/AA inline SVG/`field-visual` residue는 계속 0이다. photo cards는 Y=16, Z=15, AA=12이고 `field-visual`/`visual-figure`/`<svg`/`.svg` residue는 0이다.
- 카피부: Y/Z/AA 첫 화면 target markers는 통과한다. 다음 보강은 Z/AA 내부링크 밀도와 검색가설을 독자 행동 질문으로 더 좁히는 것이다.
- 검수부: py_compile + review + build + local quality audit + adaptive dry-run + hourly smoke 재실행 완료. review=`ready=9/9 hard=0 soft=0`; Y=`6748 chars/32 visuals`, Z=`6902/30`, AA=`4784/24`; 모두 target_fit=True, media_blockers=0. Hourly smoke pass, warnings=0.
- 발행부: adaptive publisher dry-run은 `slot_closed`(`ready_unpublished=3<=ready_target=7`, `daily_floor_open=False`, `published_today=1/4`, `spacing_open=True`, `hours_since_last=9.416`, selected none)라 실제 GitHub Pages 공개/commit/push는 실행하지 않았다. daily 1개는 floor일 뿐 상한이 아니지만 이번 슬롯은 queue guard가 닫혔다.
- 성장분석부: clean queue는 Y→Z→AA로 유지한다. 다음 학습은 Y=`열기/비 흔적/소리 중 재확인 빈칸 하나`(links=9), Z=`다음 방문 시간·방향·방 안 자리`(links=3), AA=`젖은 옷 이동·환기·건조대 통로·창문/습기/문 앞 후속 선택`(links=3)로 검색 유입이 실제 행동으로 내려가는지 확인하는 것이다.

## Blockers

- Tistory/브라우저/로그인형 외부 publish는 hourly에서 금지. GitHub Pages `/radar/` 공개는 전용 publisher desk와 adaptive 가드로만 허용한다.
- Tistory/브라우저/계정/권한 문제는 더 이상 blocker로 운영하지 않는다. 공개 원본은 GitHub Pages `/radar/`이며 제작은 계속한다.
