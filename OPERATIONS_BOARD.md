# 동네 레이더 OPERATIONS BOARD

_Last updated: 2026-05-02T13:47:55+09:00 KST_

## Scope

- `recuerdame / #naver` 전용.
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
- 생산 기준: 품질 통과 미발행 후보 최소 3개, 목표 7개, 상한 10개. 현재 7개 초과 구간에서는 새 후보 양산을 멈추고 기존 후보 품질 보강·중복 제거·주제 다변화에 쓴다. 10개 초과면 backlog 감축 모드로 보고한다.
- 7일/168시간은 buffer tracking metadata일 뿐, clean 후보 발행 차단 사유가 아니다.
- 본문 4,500자 이상, 독자용 시각자료 8개 이상, visible 금칙어 0건, hard/soft issue 0건이면 `검사 충분`으로 보고 선발행 후보 기준을 통과한다. 충분히 검사된 후보는 추가 숙성/완벽주의로 묶어두지 않고 baseline/adaptive 슬롯이 열리면 공개한다.

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

## Department handoff

- 출판관리부: latest review 기준 total ready 19 / publisher dry-run 기준 미발행 ready 15 / 오늘 공개 2 / cap 10 초과로 `backlog_reduction` 모드다. 새 후보·새 articles·새 release_candidates 생성은 계속 금지하고 기존 후보 품질 보강과 dedicated publisher의 adaptive backlog 소화를 우선한다.
- 발행부: Tistory/로그인형 외부 publish는 실행하지 않는다. GitHub Pages 공개는 전용 publisher desk가 담당하며, 이번 hourly 발행부 dry-run은 `publish_slot_closed_spacing`(마지막 공개 후 1.75h, 최소 2h)이라 실제 공개/푸시를 실행하지 않았다. daily 1개는 floor일 뿐 상한이 아니다.
- 기획부/자료수집부/데이터검증부: B의 원자료·기준월·산식 확인 전 순위 작성 금지. 이번 턴은 G 비 오는 날 후보가 습기/하자 단정 글처럼 읽힐 위험과 퇴근 후 루프·관리비 질문과 섞일 위험을 확인하고, 새 자료 수집 없이 공개 후보 내 표로 `비 오는 날=날씨가 드러낸 빈칸`, `퇴근 후=평일 귀가 루프`, `관리비=비용·책임 질문` 역할을 분리했다.
- 편집부/그래픽부/카피부/검수부/성장분석부: G 후보는 chars 5,215→5,443, visuals 9→10, target_fit=True를 확인했다. review 재검증 결과 전체 `ready=19 hard=0 soft=0`을 유지한다. 다음 시간 우선순위도 backlog 감축: 새 후보 양산 금지, 기존 후보 중 1개만 제목·도입·캡션·중복 주제·내부링크·반례 균형 중 하나를 폴리싱.

## Blockers

- Tistory/브라우저/로그인형 외부 publish는 hourly에서 금지. GitHub Pages `/radar/` 공개는 전용 publisher desk와 adaptive 가드로만 허용한다.
- Tistory/브라우저/계정/권한 문제는 더 이상 blocker로 운영하지 않는다. 공개 원본은 GitHub Pages `/radar/`이며 제작은 계속한다.
