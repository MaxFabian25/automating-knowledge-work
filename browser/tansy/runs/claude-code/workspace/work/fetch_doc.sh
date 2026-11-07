#!/bin/sh
# usage: fetch_doc.sh <id e.g. 2.4-v1> <ext>  -> clicks the viewer's Download button, saving to evidence/<id>.<ext>
D=/tmp/akw-runs/final-claude
AB="$D/work/ab.sh"
OUT="${3:-$D/evidence/$1.$2}"
for i in 1 2 3; do "$AB" open "https://akw-data-room.maxfabian31.workers.dev/doc.html?id=$1" >/dev/null 2>&1 && break; sleep 1; done
if "$AB" get url | grep -q 'next='; then
  echo "re-accepting terms"
  "$AB" check "input[type=checkbox]" >/dev/null
  "$AB" click "button[type=submit], form button" >/dev/null
  "$AB" wait 1500 >/dev/null
fi
"$AB" wait "a[href*='files/']" >/dev/null || { echo "no download link for $1"; exit 1; }
"$AB" download "a[href*='files/']" "$OUT"
