# 동네 레이더 Rolling Pipeline Policy

_Last updated: 2026-05-02T12:00:43+09:00 KST_

## 핵심 규칙

- `not_matured`, `mature_started_lt_168h`, `after_168h`, `publish_ready_at <= now` 같은 시간-only 조건은 발행 차단 사유가 아니다.
- `mature_started_at`/`publish_ready_at`은 buffer tracking metadata로만 쓴다.
- clean 후보는 dedicated publisher가 **매일 1개를 기본 floor**로 GitHub Pages에 선발행한다. backlog가 목표치를 넘으면 발행부 adaptive 슬롯이 추가 공개한다.
- production의 양 KPI는 후보 수가 아니라 **타겟에 맞는 품질 통과 미발행 큐**다. 너무 쌓지 않고 최소 3개, 목표 7개, 상한 10개만 유지한다.
- 하루 순증 목표는 0~+1개다. 3개 미만이면 최대 2개/day까지 보강·완성하고, 3~7개면 새 후보는 하루 1개까지만 만든다. 7개 초과면 새 후보 양산보다 기존 후보의 타겟 선명도·중복 제거·주제 다변화에 집중한다. 10개 초과면 backlog 감축 모드로 보고하고 생산보다 발행-ready 유지·중복 제거·발행부 backlog 소화를 우선한다.
- Reader QA + 타겟 품질 게이트 + 정적/편집 가드 통과 + hard/soft issue 0건이면 `검사 충분`이다. clean 후보는 추가 숙성/완벽주의로 묶어두지 않는다. `daily`는 기본 1개, `adaptive`는 ready_unpublished가 목표 7개 초과일 때 하루 최대 4개·최소 2시간 간격으로 공개한다.
- clean 후보가 발행대기 또는 발행완료 상태가 되면 hourly는 즉시 다음 후보를 전진시키되, 위 버퍼 기준을 넘는 양산은 하지 않는다. 발행부 턴은 `--mode adaptive` dry-run/실행 결과를 보고 다음 부서 작업을 결정한다.

## 후보 상태

- `planned`: 기획만 있음.
- `source_blocked`: 데이터/출처가 부족해 강한 결론을 낼 수 없음.
- `drafting`: story/visual/copy 작업 중.
- `release_candidate`: final.html이 있음.
- `review_required`: hard/soft issue가 있어 보강 필요.
- `publish_ready`: review 통과, external publish는 dedicated job에 맡김.
- `publish_held`: 플랫폼/계정/수동 확인 대기. 콘텐츠는 keep.

## Hourly handoff

- ready 후보 0~2개: target gate를 통과하는 final 후보만 만든다.
- ready 후보 3~10개: 새 글보다 기존 후보의 타겟 fit, 제목, 도입, 행동 도구를 보강한다.
- ready 후보 10개 초과: backlog 감축 모드. 새 후보 생성 금지, 타겟이 흐린 후보는 보강/보류/중복 제거한다.
- 플랫폼 blocked: 발행부만 blocked로 기록하고 제작부는 다음 글을 진행하되, 위 타겟 기준을 넘는 양산은 하지 않는다.
