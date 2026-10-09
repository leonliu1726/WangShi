"""生成《往事》静态网站。用法：python3 build.py book.json 图片目录 照片目录 输出目录"""
import html, json, os, re, shutil, sys
from PIL import Image
from plates import PLATES, PHOTOS

BOOK, ART, PHOTO_DIR, OUT = sys.argv[1:5]
HERE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(BOOK, encoding="utf-8"))
sections = data["sections"]
by_slug = {s["slug"]: s for s in sections}
esc = html.escape

KICKER = {"front": "", "main": "往 事", "ji": "生 活 纪 事", "back": ""}
GROUPS = [("front", "序言"), ("main", "往事"), ("ji", "生活纪事"), ("back", "后记")]

# ---------- 图片 ----------
os.makedirs(f"{OUT}/img", exist_ok=True)

def webp(src, dst, width, q=80):
    im = Image.open(src).convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(dst, "WEBP", quality=q, method=6)
    return im.size

plate_meta = {}
for i, (slug, name, anchor, cap, alt) in enumerate(PLATES, 1):
    w, h = webp(f"{ART}/{name}.jpg", f"{OUT}/img/p{i:02d}.webp", 1280)
    webp(f"{ART}/{name}.jpg", f"{OUT}/img/p{i:02d}-s.webp", 360, 70)
    plate_meta[name] = {"file": f"p{i:02d}", "w": w, "h": h, "n": i}
for key, (fn, _) in PHOTOS.items():
    plate_meta[key] = dict(zip(("w", "h"), webp(f"{PHOTO_DIR}/{fn}", f"{OUT}/img/{key}.webp", 900, 82)))
cover_sizes = {}
for k in ("1", "2"):
    cover_sizes[k] = webp(f"{ART}/00_封面_{k}.png", f"{OUT}/img/cover{k}.webp", 1200, 82)
# 首页主图：封面里的版画本身（不带封面字），避免与网页标题重复
_c = Image.open(f"{ART}/00_封面_1.png").convert("RGB").crop((112, 1072, 1488, 2067))
_c.save(f"{OUT}/img/hero.webp", "WEBP", quality=82, method=6)
hero_size = _c.size
# 主屏幕图标：朱印“老建”
shutil.copy(f"{HERE}/static/icon.png", f"{OUT}/img/icon.png")
# 社交分享图
Image.open(f"{ART}/00_封面_1.png").convert("RGB").resize((800, 1200)).save(f"{OUT}/img/og.jpg", quality=82)

# ---------- 插图挂到段落 ----------
plates_for = {}
for slug, name, anchor, cap, alt in PLATES:
    paras = [b for b in by_slug[slug]["blocks"] if "p" in b]
    hits = [b for b in paras if anchor in b["p"]]
    assert len(hits) == 1, (name, anchor, len(hits))
    assert cap in hits[0]["p"], (name, "caption not verbatim")
    plates_for.setdefault(id(hits[0]), []).append((name, cap, alt))

# ---------- 公共片段 ----------
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700;900&display=swap" rel="stylesheet">')
EARLY = ("<script>try{var t=localStorage.getItem('ws-theme');if(t)document.documentElement.setAttribute('data-theme',t);"
         "var f=localStorage.getItem('ws-fs');if(f)document.documentElement.style.setProperty('--fs',f+'px')}catch(e){}</script>")
FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='8' fill='%23a8322a'/%3E"
           "%3Ctext x='32' y='45' font-size='38' text-anchor='middle' fill='%23fbf3e8' font-family='serif'%3E往%3C/text%3E%3C/svg%3E")

def head(title, desc):
    return f"""<!doctype html>
<html lang="zh-Hans">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="noindex, nofollow">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="book">
<meta property="og:site_name" content="往事 · 老建回忆录">
<meta property="og:image" content="https://leonliu1726.github.io/WangShi/img/og.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="apple-touch-icon" href="img/icon.png">
<meta name="theme-color" content="#f4eee2">
<link rel="icon" href="{FAVICON}">
{FONTS}
<link rel="stylesheet" href="style.css">
{EARLY}
</head>"""

def drawer(current):
    out = ['<div class="drawer" id="drawer" aria-hidden="true"><div class="scrim" data-close-toc></div>',
           '<nav aria-label="目录"><button class="close" data-close-toc>关闭 ✕</button>',
           '<a href="index.html">封面</a>']
    for g, label in GROUPS:
        out.append(f"<h2>{label}</h2>")
        for s in sections:
            if s["group"] == g:
                cur = ' aria-current="page"' if s["slug"] == current else ""
                out.append(f'<a href="{s["slug"]}.html"{cur}>{esc(s["toc"])}</a>')
    out.append('<h2>附</h2><a href="hua.html"' + (' aria-current="page"' if current == "hua" else "") + '>画卷</a>')
    out.append('<a href="about.html"' + (' aria-current="page"' if current == "about" else "") + '>版权页</a></nav></div>')
    return "".join(out)

def bar(where):
    return f"""<header class="bar">
<a class="brand" href="index.html" aria-label="回到封面"><span class="seal"><i>老</i><i>建</i></span><b>往事</b></a>
<span class="where">{esc(where)}</span>
<button id="fs-down" aria-label="字变小">字小</button>
<button id="fs-up" aria-label="字变大">字大</button>
<button id="theme" title="切换夜读">夜读</button>
<button data-open-toc>目录</button>
<div class="progress"></div>
</header>"""

FOOT = """<footer class="site">往事 · 老建回忆录 · 范建华 著<br>Copyright©2022老建 · 版权所有，侵权必究<br><a href="about.html">版权页</a></footer>
<script src="app.js"></script>
</body></html>"""

def plate_html(name, cap, alt):
    m = plate_meta[name]
    return (f'<figure class="plate" id="{m["file"]}"><div class="frame"><img src="img/{m["file"]}.webp" '
            f'width="{m["w"]}" height="{m["h"]}" loading="lazy" decoding="async" alt="{esc(alt)}"></div>'
            f'<figcaption><q>{esc(cap)}</q></figcaption></figure>')

def photo_html(b):
    m = plate_meta[b["photo"]]
    wide = " wide" if m["w"] > m["h"] else ""
    return (f'<figure class="photo{wide}"><div class="frame"><img src="img/{b["photo"]}.webp" width="{m["w"]}" height="{m["h"]}" '
            f'loading="lazy" decoding="async" alt="{esc(PHOTOS[b["photo"]][1])}"></div><figcaption>{esc(b["caption"])}</figcaption></figure>')

SIGN = re.compile(r"^二零二一年感恩节于拉斯维加斯")

def body_html(s):
    out, verse = [], []
    blocks = s["blocks"]
    i = 0
    while i < len(blocks):
        b = blocks[i]
        if "photo" in b:
            out.append(photo_html(b))
        else:
            t = b["p"]
            if s["slug"] == "xu" and t == "诗曰：":
                lines = [blocks[i + 1]["p"], blocks[i + 2]["p"]]
                out.append(f'<p class="lead">{esc(t)}</p><div class="verse">' + "".join(f"<span>{esc(x)}</span>" for x in lines) + "</div>")
                i += 3
                continue
            cls = ' class="sign"' if SIGN.match(t) else ""
            out.append(f"<p{cls}>{esc(t)}</p>")
            for p in plates_for.get(id(b), []):
                out.append(plate_html(*p))
        i += 1
    return "\n".join(out)

def first_plate(slug):
    for sl, name, *_ in PLATES:
        if sl == slug:
            return plate_meta[name]["file"]
    return None

# ---------- 章节页 ----------
for idx, s in enumerate(sections):
    prev = sections[idx - 1] if idx > 0 else None
    nxt = sections[idx + 1] if idx + 1 < len(sections) else None
    kicker = KICKER[s["group"]]
    where = (kicker.replace(" ", "") + " · " if kicker else "") + s["toc"]
    first_text = next(b["p"] for b in s["blocks"] if "p" in b)
    lead = ""
    if s["slug"] == "j01":
        lead = f'<p class="lead">{esc(data["ji_intro"])}</p>'
    byline = f'<div class="byline">{esc(s["byline"])}</div>' if s.get("byline") else ""
    pager = '<nav class="pager" aria-label="翻页">'
    if prev:
        pager += f'<a class="prev" href="{prev["slug"]}.html"><small>上一篇</small><span>{esc(prev["toc"])}</span></a>'
    if nxt:
        pager += f'<a class="next" href="{nxt["slug"]}.html"><small>下一篇</small><span>{esc(nxt["toc"])}</span></a>'
    else:
        pager += '<a class="next" href="about.html"><small>书末</small><span>版权页</span></a>'
    pager += "</nav>"
    page = (head(f"{s['toc']} · 往事", first_text[:70] + "……")
            + f'\n<body data-slug="{s["slug"]}" data-title="{esc(s["toc"])}"><div class="wrap">'
            + bar(where) + drawer(s["slug"])
            + f'<main><article class="chapter"><header>'
            + (f'<div class="kicker">{kicker}</div>' if kicker else "")
            + f'<h1>{esc(s["title"])}</h1>{byline}</header>{lead}\n{body_html(s)}\n</article>{pager}</main></div>'
            + FOOT)
    open(f"{OUT}/{s['slug']}.html", "w", encoding="utf-8").write(page)

# ---------- 首页 ----------
xu = by_slug["xu"]
xu_first = xu["blocks"][0]["p"]
toc = ['<div class="toc">']
for g, label in GROUPS:
    toc.append(f"<h3>{label}</h3>")
    for s in sections:
        if s["group"] != g:
            continue
        parts = s["toc"].split(" ", 1)
        n, t = (parts if len(parts) == 2 and s["group"] in ("main", "ji") else ("", s["toc"]))
        if s["slug"] == "j08":
            n, t = "八", s["toc"][1:]
        fp = first_plate(s["slug"])
        thumb = f'<img src="img/{fp}-s.webp" alt="" loading="lazy" width="72" height="40">' if fp else ""
        toc.append(f'<a href="{s["slug"]}.html"><span class="n">{esc(n) or "·"}</span><span class="t">{esc(t)}</span>{thumb}</a>')
toc.append("</div>")

verse = [b["p"] for b in xu["blocks"]][-2:]
index = (head("往事 · 老建回忆录", "范建华（老建）回忆录：从潍北范家庄到东北煤矿，再到拉斯维加斯的菜园。")
         + '\n<body><div class="wrap">' + bar("老建回忆录") + drawer("index")
         + f"""<main>
<section class="cover">
  <div class="art"><img src="img/hero.webp" width="{hero_size[0]}" height="{hero_size[1]}" alt="老槐树下的村路，一个孩子走向院门"></div>
  <div class="right">
    <div class="titles"><h1>往事</h1><div class="sub">老建回忆录</div><span class="seal big"><i>老</i><i>建</i></span></div>
    <div class="author">范建华　著</div>
    <div class="actions"><a class="btn-main" href="xu.html">开始阅读</a><a class="btn-ghost" href="#mulu">目录</a><a class="btn-ghost" href="hua.html">画卷</a></div>
    <p class="continue" id="continue">上次读到：<a href="#">—</a></p>
  </div>
</section>
<section class="section">
  <h2>序　文刃</h2>
  <div class="poem-card">
    <p>{esc(xu_first[:118])}……</p>
    <div class="verse">{''.join(f'<span>{esc(v)}</span>' for v in verse)}</div>
    <a class="btn-ghost" href="xu.html">读全序</a>
  </div>
</section>
<section class="section" id="mulu">
  <h2>目录</h2>
  {''.join(toc)}
</section>
</main></div>""" + FOOT)
open(f"{OUT}/index.html", "w", encoding="utf-8").write(index)

# ---------- 画卷页 ----------
cards = []
for slug, name, anchor, cap, alt in PLATES:
    m = plate_meta[name]
    cards.append(f'<a href="{slug}.html#{m["file"]}"><div class="frame"><img src="img/{m["file"]}.webp" loading="lazy" decoding="async" '
                 f'width="{m["w"]}" height="{m["h"]}" alt="{esc(alt)}"></div><div class="cap"><b>{esc(by_slug[slug]["toc"])}</b>{esc(cap)}</div></a>')
hua = (head("画卷 · 往事", "《往事》全书插图")
       + '\n<body data-slug="hua" data-title="画卷"><div class="wrap">' + bar("画卷") + drawer("hua")
       + f'<main class="section" style="border-top:0"><h2>画卷 · {len(PLATES)} 幅</h2><div class="gallery">{"".join(cards)}</div></main></div>' + FOOT)
open(f"{OUT}/hua.html", "w", encoding="utf-8").write(hua)

# ---------- 版权页 ----------
col = data["colophon"]
about = (head("版权页 · 往事", "《往事》版权页")
         + '\n<body><div class="wrap">' + bar("版权页") + drawer("about")
         + f'<main class="section" style="border-top:0"><div class="colophon"><p class="t">{esc(col[0])}</p><p>{esc(col[1])}</p>'
         + "".join(f"<div>{esc(x)}</div>" for x in col[2:])
         + f'<div class="covers"><figure class="photo"><div class="frame"><img src="img/cover1.webp" width="{cover_sizes["1"][0]}" height="{cover_sizes["1"][1]}" loading="lazy" alt="《往事》封面一：老槐树下的村路"></div><figcaption>封面一</figcaption></figure><figure class="photo"><div class="frame"><img src="img/cover2.webp" width="{cover_sizes["2"][0]}" height="{cover_sizes["2"][1]}" loading="lazy" alt="《往事》封面二：老树、院墙与小路"></div><figcaption>封面二</figcaption></figure></div>'
         + "</div></main></div>" + FOOT)
open(f"{OUT}/about.html", "w", encoding="utf-8").write(about)

for f in ("style.css", "app.js"):
    shutil.copy(f"{HERE}/static/{f}", f"{OUT}/{f}")
open(f"{OUT}/.nojekyll", "w").close()
print("pages", len(sections) + 3, "plates", len(PLATES))
