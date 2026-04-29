# Hourly Department Turns — 동네 레이더

_Last updated: 2026-04-29 21:44 KST_

## 이 job의 약속

- #naver/동네 레이더만 다룬다.
- `deliver: local` 전제이므로 최종 응답은 `[SILENT]`다.
- `terminal(background=true)`와 `notify_on_complete=true`는 금지한다.
- 매시간 review script와 auto-publish dry-run을 실행하되, hourly 자체는 실제 publish를 하지 않는다.
- 글이 발행대기/blocked가 되어도 제작 루프는 멈추지 않는다.

## 한 턴 출력 형식

1. 검증 명령과 결과.
2. 10개 부서별 실제 산출/수정/검증 1줄.
3. `글 keep + 다음 부서 작업` 또는 `발행 완료 + 다음 버퍼 보강`.
4. 다음 시간 handoff 1개.

## 우선순위 규칙

1. hard issue가 있는 후보를 먼저 고친다.
2. ready 후보가 0개면 70-final-html 후보를 만든다.
3. ready 후보가 1개 이상이면 다음 중간 후보를 00-topic/10-source/30-story 중 한 단계 전진시킨다.
4. 순위형 글은 데이터 출처와 산식이 검증되기 전까지 최종 순위를 쓰지 않는다.
