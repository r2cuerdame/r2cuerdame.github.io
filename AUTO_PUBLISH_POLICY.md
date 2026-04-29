# 동네 레이더 Auto Publish Policy

_Last updated: 2026-04-29 21:44 KST_

## 절대 금지

- hourly department job은 실제 외부 publish를 실행하지 않는다.
- 로그인, 캡차 우회, 계정 권한 변경, 카테고리 생성, 스킨 변경, 광고 설정, 결제/비용 발생 작업은 자동 수행하지 않는다.
- 외부 채널에 원고 전문, 표, 로그, 토큰, 쿠키, 계정 정보를 출력하지 않는다.
- 공개 본문에 직접 판매/결제/구독/제휴형 구매 유도/내부 제작 용어를 노출하지 않는다.

## 선발행 가능 조건

Dedicated publisher가 발행 후보를 고르려면 아래가 모두 참이어야 한다.

1. `release_candidates/YYYY-MM/<slug>/final.html`이 존재한다.
2. `<script>` 태그가 없다.
3. visible body length가 4,500자 이상이다.
4. reader-facing visual count가 8개 이상이다.
5. 금칙어/내부어/제휴 혼입이 visible text에서 0건이다.
6. 반례, 한계, 해석, 현장 질문, 사용법 신호가 기사 안에 존재한다.
7. review script의 hard issue와 soft issue가 모두 0건이다.
8. 하루 최대 1개 cap을 넘지 않는다.

## 7일 버퍼 규칙

- `mature_started_at`과 `publish_ready_at`은 7일 rolling buffer를 추적하는 메타다.
- 이 값은 품질이 깨끗한 글의 발행 차단 사유가 아니다.
- 발행으로 큐가 줄면 hourly는 다음 후보 제작·보강으로 버퍼를 다시 채운다.

## 실패 모드

- 플랫폼 보안/로그인/캡차/브라우저/CDP 오류: `platform_security_hold` 또는 `external_publish_blocked`로 fail-closed.
- 콘텐츠 품질 오류: `review_required`로 보강 후 재검수.
- 데이터 불충분/순위 산출 불가: `source_blocked`로 표시하고 추정 순위 작성 금지.
- dry-run은 후보 선택과 blocker만 기록한다. 실제 업로드는 수행하지 않는다.
