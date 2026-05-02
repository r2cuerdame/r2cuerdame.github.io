# 동네 레이더 Auto Publish Policy

_Last updated: 2026-05-02T12:31:00+09:00 KST_

## 절대 금지

- Tistory/브라우저/로그인/광고/결제/권한 관련 외부 publish는 자동 실행하지 않는다.
- 로그인, 캡차 우회, 계정 권한 변경, 카테고리 생성, 스킨 변경, 광고 설정, 결제/비용 발생 작업은 자동 수행하지 않는다.
- 외부 채널에 원고 전문, 표, 로그, 토큰, 쿠키, 계정 정보를 출력하지 않는다.
- 공개 본문에 직접 판매/결제/구독/제휴형 구매 유도/내부 제작 용어를 노출하지 않는다.

## 선발행 가능 조건

- 동네 레이더 공개 cadence는 **매일 1개가 floor(기본 최소)**이지 ceiling(상한)이 아니다. 회사식 운영에서는 발행부가 슬롯을 열어 clean backlog를 더 소화한다.
- 매일 포스팅은 문제가 없다. 조건은 명확하다: **각 글의 타겟이 선명하고, Reader QA + 타겟 품질 게이트 + 정적/편집 가드 + hard/soft issue 0건을 모두 통과해야 한다.**
- 전용 GitHub Pages publisher만 실제 GitHub Pages 공개 커밋/푸시를 수행한다.
- hourly department job은 기본적으로 스모크·보강·검수·후보 생산을 맡되, **발행부 턴**에서는 `scripts/publish_next_radar_candidate.py --mode adaptive`로 GitHub Pages 공개를 실행할 수 있다.
- 생산 KPI는 후보 수가 아니라 **타겟에 맞는 품질 통과 미발행 큐**다. 너무 쌓지 않고 최소 3개, 목표 7개, 상한 10개만 유지한다.
- 3개 미만이면 최대 2개/day까지 보강·완성한다. 3~7개면 새 후보는 하루 1개까지만 만들고 나머지 턴은 기존 후보의 타겟 적합도와 품질을 올린다. 7개 초과면 새 후보 양산을 멈추고 타겟 선명도/중복제거/주제다변화/내부링크에 집중한다. 10개 초과면 backlog 감축 모드로 보고하고 생산보다 발행-ready 유지·중복 제거·발행부 backlog 소화를 우선한다.
- Reader QA + 타겟 품질 게이트 + 정적/편집 가드 통과 + hard/soft issue 0건이면 `검사 충분`으로 본다. clean 후보는 7일 숙성이나 추가 완벽주의를 이유로 묶어두지 않는다. daily baseline은 1개, adaptive 발행부는 clean 미발행 큐가 목표 7개를 초과할 때 하루 최대 4개·최소 2시간 간격으로 추가 공개한다.

Dedicated publisher가 발행 후보를 고르려면 아래가 모두 참이어야 한다.

1. `release_candidates/YYYY-MM/<slug>/final.html`이 존재한다.
2. `<script>` 태그가 없다.
3. visible body length가 4,500자 이상이다.
4. reader-facing visual count가 8개 이상이다.
5. visual rhythm이 있다: 첫 화면 visual scan/요약카드, 본문 중간 callout/카드/지도형 모듈이 있고 표만 연속되지 않는다.
6. 금칙어/내부어/제휴 혼입이 visible text에서 0건이다.
7. 도입 600자 안에 `서울·수도권`, `25~39세`, 전월세/이사/거주지 비교 맥락, 계속 볼지/보류할지/무엇을 확인할지의 행동이 보인다.
8. 반례, 한계, 해석, 현장 질문, 사용법 신호가 기사 안에 존재한다.
9. review script의 hard issue와 soft issue가 모두 0건이다.
10. daily baseline 모드에서는 하루 1개를 넘지 않는다. adaptive 발행부 모드에서는 clean 미발행 큐가 목표 7개를 초과하고 spacing guard가 열렸을 때 하루 최대 4개까지만 공개한다.

## 7일 버퍼 규칙

- `mature_started_at`과 `publish_ready_at`은 7일 rolling buffer를 추적하는 메타다.
- 이 값은 품질이 깨끗한 글의 발행 차단 사유가 아니다.
- 발행으로 큐가 줄면 hourly는 다음 후보 제작·보강으로 버퍼를 다시 채운다.

## 실패 모드

- 플랫폼 보안/로그인/캡차/브라우저/CDP 오류: `platform_security_hold` 또는 `external_publish_blocked`로 fail-closed.
- 콘텐츠 품질 오류: `review_required`로 보강 후 재검수.
- 데이터 불충분/순위 산출 불가: `source_blocked`로 표시하고 추정 순위 작성 금지.
- dry-run은 후보 선택과 blocker만 기록한다. 실제 업로드는 수행하지 않는다.
- 실제 GitHub Pages 공개는 `daily` 또는 `adaptive` publisher 모드에서만 수행한다.
