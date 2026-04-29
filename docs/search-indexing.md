# Search indexing checklist

Public URL: https://r2cuerdame.github.io/
Sitemap: https://r2cuerdame.github.io/sitemap.xml
RSS: https://r2cuerdame.github.io/feed.xml
LLM guide: https://r2cuerdame.github.io/llms.txt

## Already handled in repo

- robots allows Google, Naver/Yeti, Daumoa, Bing, and major AI/search crawlers.
- sitemap includes static sections and generated article URLs.
- every HTML page has canonical, description, OG, RSS, sitemap link, and JSON-LD.
- `llms.txt` and `ai.txt` exist for AI search/answer engines.
- daily automation keeps metadata current and can add clean article candidates.

## Manual one-time registrations still needed

Search engines usually require owner verification before manual sitemap submission.
Do not store verification tokens in docs. Add verification meta/file only after the owner provides the token.

- Google Search Console: add property for `https://r2cuerdame.github.io/`, verify, submit `/sitemap.xml`.
- Naver Search Advisor: add site, verify, submit `/sitemap.xml` and `/robots.txt` check.
- Daum search/webmaster registration: register site URL and sitemap if the tool asks for it.

After verification, keep publishing complete reader-facing pages. Empty daily rebuilds help freshness but do not replace real content.
