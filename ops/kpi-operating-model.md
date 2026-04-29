# 동네 레이더 KPI Operating Model

_Last updated: 2026-04-29 21:44 KST_

## 현재 단계

- 단계: awareness-first public magazine.
- 즉시 매출 목표: 현재 보류. 공개 신뢰 자산, 검색 유입, 반복 방문, 저장/공유 반응을 먼저 만든다.
- 첫 KPI: 품질 통과 release candidate와 7일 rolling buffer.

## 계산 메모

도구 계산 결과:

- 7일 buffer = 168시간.
- dedicated publisher 하루 최대 1개면 주간 최대 7개, 30일 기준 월간 최대 30개.
- 독자용 시각자료 최소 6개 기준으로 매일 1개 발행 시 주간 최소 42개 visual 검수가 필요하다.

## 현행 KPI

| KPI | 기준 | 현재 적용 |
|---|---:|---|
| publish-ready 후보 | 최소 1개 이상 유지 | hourly가 후보를 만들고 review한다 |
| 7일 rolling buffer | 7개 publish-ready/near-ready 후보 지향 | 발행 지연 hard gate 아님 |
| 본문 품질 | 4,500~7,000자 | 3,200자 미만 차단 |
| 시각자료 | 8개 이상 목표 | 6개 미만 차단 |
| 공개 금칙어 | 0건 | visible body scan |
| 외부 발행 | dedicated job만 | hourly publish 금지 |

## 미래 옵션

- 방문/검색/반복 방문 데이터가 쌓인 뒤 광고, 리포트, 협업, 데이터 패키지 가능성을 관찰한다.
- 해당 옵션은 현재 공개 본문에 직접 노출하지 않는다.
