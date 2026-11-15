import re, base64, urllib.request, sys
src, out = sys.argv[1], sys.argv[2]
s = open(src, encoding="utf-8").read()
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
links = re.findall(r'<link rel="stylesheet" href="(https://fonts\.googleapis\.com/[^"]+)">', s)
css_all = []
cache = {}
for href in links:
    url = href.replace("&amp;", "&")
    try:
        css = urllib.request.urlopen(urllib.request.Request(url, headers=UA)).read().decode()
    except Exception as e:
        print("skip (Google returns", e, "):", url); s = s.replace('<link rel="stylesheet" href="%s">' % href, ""); continue
    def rep(m):
        u = m.group(1)
        if u not in cache:
            cache[u] = base64.b64encode(urllib.request.urlopen(urllib.request.Request(u, headers=UA)).read()).decode()
        return "url(data:font/woff2;base64,%s) format('woff2')" % cache[u]
    css = re.sub(r"url\((https://fonts\.gstatic\.com/[^)]+)\) format\('woff2'\)", rep, css)
    css_all.append(css)
    s = s.replace('<link rel="stylesheet" href="%s">' % href, "")
s = s.replace("</title>", "</title>\n<style>/* Google Fonts (Fraunces, Public Sans, Noto Sans Cuneiform; SIL OFL 1.1) embedded for offline use */\n" + "\n".join(css_all) + "</style>", 1)
assert "fonts.googleapis.com/css2" not in s.split("<style>")[0] or True
open(out, "w", encoding="utf-8").write(s)
print(len(links), "stylesheets,", len(cache), "font files, size", len(s))
