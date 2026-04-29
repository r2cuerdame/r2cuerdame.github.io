# 동네 레이더 Rolling Pipeline Policy

_Last updated: 2026-04-29 21:44 KST_

## 핵심 규칙

- `not_matured`, `mature_started_lt_168h`, `after_168h`, `publish_ready_at <= now` 같은 시간-only 조건은 발행 차단 사유가 아니다.
- `mature_started_at`/`publish_ready_at`은 buffer tracking metadata로만 쓴다.
- clean 후보는 dedicated publisher가 하루 cap 안에서 선발행할 수 있다.
- clean 후보가 발행대기 또는 발행완료 상태가 되면 hourly는 즉시 다음 후보를 전진시킨다.

## 후보 상태

- `planned`: 기획만 있음.
- `source_blocked`: 데이터/출처가 부족해 강한 결론을 낼 수 없음.
- `drafting`: story/visual/copy 작업 중.
- `release_candidate`: final.html이 있음.
- `review_required`: hard/soft issue가 있어 보강 필요.
- `publish_ready`: review 통과, external publish는 dedicated job에 맡김.
- `publish_held`: 플랫폼/계정/수동 확인 대기. 콘텐츠는 keep.

## Hourly handoff

- ready 후보 0개: final 후보를 만든다.
- ready 후보 1개: 다음 글 source/story/visual을 전진시킨다.
- 플랫폼 blocked: 발행부만 blocked로 기록하고 제작부는 다음 글을 진행한다.
