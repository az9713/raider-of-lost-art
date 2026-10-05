# Converts DEVELOPMENT-JOURNEY.md into docs/journey.html (dark theme).
# Run from the repo root: python tools/build_html.py
import markdown

md = open('DEVELOPMENT-JOURNEY.md', encoding='utf-8').read().replace('docs/img/', 'img/')
body = markdown.markdown(md, extensions=['tables', 'fenced_code', 'sane_lists'])
css = """<style>
:root{color-scheme:dark;--bg:#0f172a;--card:#1e293b;--text:#e2e8f0;--text2:#cbd5e1;--muted:#94a3b8;--a1:#fb923c;--a2:#2dd4bf;--line:#334155}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text2);font:17px/1.65 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:860px;margin:0 auto;padding:28px 16px 80px}
h1{color:var(--text);font-size:1.9rem;line-height:1.25;margin:.2em 0 .6em}h2{color:var(--a1);margin-top:2.2em;border-bottom:1px solid var(--line);padding-bottom:.3em}h3{color:var(--a2);margin-top:1.8em}
a{color:var(--a2)}strong{color:var(--text)}em{color:var(--text)}code{background:var(--card);padding:.1em .35em;border-radius:4px;font-size:.88em;color:var(--a2);overflow-wrap:anywhere}
pre{background:var(--card);padding:14px;border-radius:8px;overflow:auto}pre code{padding:0}
blockquote{margin:1.2em 0;padding:.6em 1em;background:var(--card);border-left:4px solid var(--a1);border-radius:0 8px 8px 0}blockquote p{margin:.3em 0}
table{border-collapse:collapse;width:100%;display:block;overflow-x:auto;margin:1em 0}th,td{border:1px solid var(--line);padding:7px 10px;text-align:left;vertical-align:top}th{background:var(--card);color:var(--text)}
img{max-width:100%;height:auto;border-radius:8px;border:1px solid var(--line);display:block;margin:1em auto}
hr{border:0;border-top:1px solid var(--line);margin:2em 0}nav{font-size:.9rem;color:var(--muted);margin-bottom:1em}
</style>"""
nav = '<nav><a href="./">&larr; Watch the film</a> &middot; <a href="https://github.com/az9713/raider-of-lost-art">Repository</a></nav>'
html = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="color-scheme" content="dark">'
        '<title>Development Journey: The Idol That Wakes</title>' + css +
        '</head><body><main>' + nav + body + '</main></body></html>')
open('docs/journey.html', 'w', encoding='utf-8').write(html)
print('journey.html', len(html))
