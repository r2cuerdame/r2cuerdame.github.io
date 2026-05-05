# Search indexing checklist

Public URL: https://r2cuerdame.github.io/
Sitemap: https://r2cuerdame.github.io/sitemap.xml
RSS: https://r2cuerdame.github.io/feed.xml
LLM guide: https://r2cuerdame.github.io/llms.txt

## Already handled in repo

- robots allows Google, Naver/Yeti, Daumoa, Bing, and major AI/search crawlers.
- sitemap includes static sections, topic hub URLs, and generated article URLs.
- every HTML page has canonical, description, OG, RSS, sitemap link, SearchAction JSON-LD, breadcrumb JSON-LD, and page/article JSON-LD.
- `/topics/` gives Google/Search Console fixed landing URLs for 월세·전세·상가·생활상품 intent tests.
- `/search/` and `data/search-index.json` give users a fast site/product search surface.
- `llms.txt` and `ai.txt` exist for AI search/answer engines.
- new public articles update the related feed and sitemap.

## Registration status

Search engines require owner verification before manual sitemap submission. Verification tokens are kept only as site meta tags, not as account credentials.

- Google Search Console: property verified and `/sitemap.xml` submitted.
- Naver Search Advisor: site ownership accepted; sitemap/robots are ready for crawl checks.
- Daum search/webmaster registration: register site URL and sitemap if the tool asks for it.

Keep publishing complete reader-facing pages. Empty daily rebuilds help freshness but do not replace real content.
