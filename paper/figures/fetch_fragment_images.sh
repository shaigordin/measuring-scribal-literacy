#!/usr/bin/env bash
# Fetches the photo and hand copy of KBo 24.8 for Figure 1 from the Hethitologie-Portal Mainz.
# The images are (c) Hethitologie-Archiv / Hethitologieportal Mainz and are NOT kept in git.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE/external"; mkdir -p "$OUT"
node "$HERE/../../orphans/fotarch/fetch_photos.js" "$OUT" "KBo 24.8"            # photo hethiter.net/: fotarch N08917
curl -s -o "$OUT/KBo_24_8_copy.png" \
  "https://www.hethport.adwmainz.de/hetautgrf/frgg/HPpngKBo24bearb/KBo24.08.png"  # hand copy, KBo 24 Nr. 8
# crop the archive header off the photo and flatten the hand copy onto white, at print resolution
python3 - "$OUT" <<'PY'
import sys
from PIL import Image
out = sys.argv[1]
im = Image.open(f"{out}/KBo_24_8_N08917.jpg").convert("RGB")
im.crop((0, 95, im.width, 950)).save(f"{out}/KBo_24_8_photo.jpg", dpi=(300, 300), quality=92)
c = Image.open(f"{out}/KBo_24_8_copy.png").convert("RGBA")
bg = Image.new("RGB", c.size, (255, 255, 255)); bg.paste(c, mask=c.split()[3])
bg.save(f"{out}/KBo_24_8_handcopy.png", dpi=(150, 150))
PY
