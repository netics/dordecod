#!/usr/bin/env bash
# Post-deploy smoke test. Usage: scripts/smoke.sh https://your-domain
set -u
BASE="${1:?usage: scripts/smoke.sh https://your-domain}"
fail=0
ok()   { printf '  ok   %s\n' "$1"; }
bad()  { printf '  FAIL %s\n' "$1"; fail=1; }
expect_status() { # path status
  s=$(curl -s -o /dev/null -w '%{http_code}' "$BASE$1"); [ "$s" = "$2" ] && ok "$1 -> $s" || bad "$1 -> $s (want $2)"; }
expect_type() { # path content-type-prefix
  t=$(curl -s -o /dev/null -w '%{content_type}' "$BASE$1"); case "$t" in "$2"*) ok "$1 is $t";; *) bad "$1 is $t (want $2)";; esac; }

echo "Status"
for p in / /en/ /robots.txt /sitemap.xml /llms.txt /llms-full.txt /index.md /en/index.md /favicon.ico /favicon.svg /site.webmanifest /og/og-ro-v2.png /og/og-en-v2.png; do expect_status "$p" 200; done
expect_status /en 308
expect_status /nu-exista/ 404

echo "Content types"
expect_type /index.md text/markdown
expect_type /llms.txt text/plain
expect_type /sitemap.xml application/xml
expect_type /og/og-ro-v2.png image/png

echo "Crawlers get the full static text"
for ua in Googlebot GPTBot OAI-SearchBot ChatGPT-User ClaudeBot Claude-User Claude-SearchBot PerplexityBot Perplexity-User Applebot; do
  body=$(curl -s -A "Mozilla/5.0 (compatible; $ua)" "$BASE/en/")
  echo "$body" | grep -q 'Works on my machine' && ok "$ua sees /en/ content" || bad "$ua does not see /en/ content"
done
exit $fail
