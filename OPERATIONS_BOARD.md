# 동네 레이더 OPERATIONS BOARD

_Last updated: 2026-04-29T22:46:58+09:00 KST_

## Scope

- `recuerdame / #naver` 전용.
- 다른 프로젝트/채널 상태는 조회·비교·보고하지 않는다.
- Tistory 발행·브라우저 자동화·수동 복붙 패키지는 폐기했다. 외부 로그인·권한·카테고리·스킨·광고 설정은 hourly에서 수행하지 않는다.

## Current KPI

- 현재 전략: GitHub Pages `/radar/` 중심 awareness-first 공개 매거진.
- 첫 KPI: 품질 통과 release candidate와 7일 rolling buffer.
- 7일/168시간은 buffer tracking metadata일 뿐, clean 후보 발행 차단 사유가 아니다.
- 본문 4,500자 이상, 독자용 시각자료 8개 이상, visible 금칙어 0건, hard/soft issue 0건을 선발행 후보 기준으로 삼는다.

## Queue

### A. 동네 신호 읽기 기본 프레임

- 상태: `published_revision` / GitHub Pages 공개본 수정 완료. Tistory 대기 상태는 폐기.
- 최종본: `release_candidates/2026-04/dongne-signal-framework/final.html`
- 메타: `release_candidates/2026-04/dongne-signal-framework/metadata.json`
- 검증: `reports/cron-review-latest.md`, `reports/auto-publish-dry-run-latest.md`
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

- 상태: `story_ready` — 20-data-qa에서 산식/단위/과장 차단선을 세움. 다음은 30-story.
- Stage notes:
  - [x] 00-topic: `articles/2026-04/monthly-rent-pressure-questions/00-topic.md`
  - [x] 10-source: `articles/2026-04/monthly-rent-pressure-questions/10-source.md`
  - [x] 20-data-qa: `articles/2026-04/monthly-rent-pressure-questions/20-data-qa.md`
  - [ ] 30-story: 위 5개 질문을 발견→해석→반례/한계→현장 질문→사용법 구조로 작성.

## Department handoff

- 출판관리부: A는 GitHub Pages 공개본 기준으로 수정·검색 노출을 관리한다. Tistory dedicated publisher는 폐기.
- 기획부/자료수집부: B의 원자료·기준월·산식 확인 전 순위 작성 금지.
- 다음 시간 우선순위: C의 30-story에서 월세 압박 5개 질문을 기사 흐름으로 전개한다.

## Blockers

- 외부 publish는 hourly에서 금지.
- Tistory/브라우저/계정/권한 문제는 더 이상 blocker로 운영하지 않는다. 공개 원본은 GitHub Pages `/radar/`이며 제작은 계속한다.
