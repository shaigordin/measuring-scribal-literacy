#!/usr/bin/env bash
# Fetches the photo and hand copy of KBo 24.8 for Figure 1 from the Hethitologie-Portal Mainz.
# The images are (c) Hethitologie-Archiv / Hethitologieportal Mainz and are NOT kept in git.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE/external"; mkdir -p "$OUT"
node "$HERE/../../orphans/fotarch/fetch_photos.js" "$OUT" "KBo 24.8"            # photo hethiter.net/: fotarch N08917
curl -s -o "$OUT/KBo_24_8_copy.png" \
  "https://www.hethport.adwmainz.de/hetautgrf/frgg/HPpngKBo24bearb/KBo24.08.png"  # hand copy, KBo 24 Nr. 8
