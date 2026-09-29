#!/usr/bin/env bash
# Tell Bing, Yandex, Seznam, Naver (IndexNow) that the pages changed. Run after a deploy that changes content.
# Usage: scripts/indexnow.sh https://your-domain
set -eu
BASE="${1:?usage: scripts/indexnow.sh https://your-domain}"
HOST="${BASE#https://}"
KEY=$(sed -n "s/^INDEXNOW_KEY = '\([0-9a-f]*\)'.*/\1/p" "$(dirname "$0")/../build.py")
curl -s -o /dev/null -w 'IndexNow: HTTP %{http_code}\n' -X POST https://api.indexnow.org/indexnow \
  -H 'Content-Type: application/json; charset=utf-8' \
  -d "{\"host\":\"$HOST\",\"key\":\"$KEY\",\"keyLocation\":\"$BASE/$KEY.txt\",\"urlList\":[\"$BASE/\",\"$BASE/en/\"]}"
