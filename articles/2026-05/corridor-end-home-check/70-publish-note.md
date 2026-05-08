# 복도 끝 집, 조용함인지 사각지대인지 보는 밤 12분 — 70-publish note

- 상태: `published_to_pages_visual_audit_passed`
- GitHub Pages `/radar/` 공개 완료: `https://r2cuerdame.github.io/radar/corridor-end-home-check/` (`pages_published_at=2026-05-08T00:34:49+09:00`).
- 공개 후 visual hotfix: 카드 thumbnail 1개와 AI field-example WebP 3개를 연결했고, `scripts/build_site.py && scripts/audit_public_site_quality.py` 및 hourly smoke가 통과했다. 이미 `published_to_pages`로 표시됐으나 remote 404였던 상태는 recovery commit `4ea0419` push 후 live `/radar/corridor-end-home-check/`, `/radar/`, thumbnail WebP 200으로 확인했다.
- 향후 GitHub Pages `/radar/` 공개는 계속 `scripts/publish_next_radar_candidate.py --mode adaptive --max-per-day 4 --min-interval-hours 2 --ready-target 7` 전용 가드만 사용한다.
- Tistory/브라우저/로그인/광고/결제/권한 변경 금지.
- slot이 닫히면 후보는 keep하고 다음 생산/폴리싱을 계속한다.
