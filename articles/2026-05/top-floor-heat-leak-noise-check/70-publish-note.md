# 70-publish note

- status: `release_candidate_ready` after deterministic review passes.
- publication route: only `scripts/publish_next_radar_candidate.py --mode adaptive --max-per-day 4 --min-interval-hours 2 --ready-target 7` may publish to GitHub Pages `/radar/`.
- current expected guard: ready_unpublished should return to 3, which is at buffer minimum and below ready_target=7; adaptive slot should stay closed unless daily floor/queue guard opens later.
- forbidden actions: Tistory, browser/login, captcha, ads, payment, permissions.
