"""把 docx 纯文本拆成结构化章节。正文一字不改，只做分段。"""
import json, re, sys

SRC = sys.argv[1]
OUT = sys.argv[2]
lines = open(SRC, encoding="utf-8").read().split("\n")

# (slug, 目录标题, 正文标题, 起始行号(1-based, 标题行), 分组)
SECTIONS = [
    ("xu", "序", "序", 67, "front"),
    ("zixu", "自序", "自 序", 81, "front"),
    ("c01", "一 范氏家族", "一  范氏家族", 109, "main"),
    ("c02", "二 我的祖父母", "二 我的祖父母", 141, "main"),
    ("c03", "三 大爷爷一家", "三  大爷爷一家", 183, "main"),
    ("c04", "四 三爷爷一家", "四 三爷爷一家", 211, "main"),
    ("c05", "五 我们家", "五 我们家", 219, "main"),
    ("c06", "六 母亲的冤案", "六 母亲的冤案", 291, "main"),
    ("c07", "七 挣扎", "七 挣扎", 323, "main"),
    ("c08", "八 童年记忆", "八 我的童年记忆", 375, "main"),
    ("c09", "九 少年时代", "九 少年时代", 427, "main"),
    ("c10", "十 灰色青春", "十 灰色青春", 447, "main"),
    ("c11", "十一 拨云见日", "十一 拨云见日", 517, "main"),
    ("c12", "十二 沉重年代", "十二 沉重的时代", 531, "main"),
    ("c13", "十三 回归", "十三  回归", 567, "main"),
    ("j01", "一 沙果大王赵子洪", "一 沙果大王赵子洪", 605, "ji"),
    ("j02", "二 白老歪", "二 白老歪", 609, "ji"),
    ("j03", "三 黄二爷", "三 黄二爷", 619, "ji"),
    ("j04", "四 杨友德", "四 杨友德", 629, "ji"),
    ("j05", "五 张书华的苦恼", "五 张书华的苦恼", 637, "ji"),
    ("j06", "六 大老妈的牌坊", "六 大老妈的牌坊", 643, "ji"),
    ("j07", "七 高维刚", "七 高维刚", 649, "ji"),
    ("j08", "八“大干苦干加二十三干”", "八 “大干苦干加23干”", 661, "ji"),
    ("j09", "九 工业大检查", "九 工业大检查", 665, "ji"),
    ("houji", "后记", " 后记", 671, "back"),
]
# 各节结束行（不含）：下一节标题行；特殊的结构性标记行另行剔除
ENDS = {s[0]: (SECTIONS[i + 1][3] if i + 1 < len(SECTIONS) else 697) for i, s in enumerate(SECTIONS)}
ENDS["zixu"] = 103          # 之后是竖排“往 事”分部标记
ENDS["c13"] = 593           # 之后是竖排“生活记事”分部标记
ENDS["houji"] = 693         # 之后是照片说明＋照片＋版权页
JI_INTRO = (603, 604)       # “在东北生活的十八年中……”
PHOTOS = {163: "photo1", 319: "photo2", 453: "photo3", 473: "photo4", 589: "photo5", 695: "photo6"}

def ln(n):
    return lines[n - 1]

def sp(t):
    """标题里的空格（含不换行空格）统一为一个空格，只动空白，不动文字。"""
    return re.sub(r"\s+", " ", t).strip()

for slug, _, body_title, start, _ in SECTIONS:
    assert sp(ln(start)) == sp(body_title), (slug, ln(start), body_title)

def blocks(a, b):
    out, n = [], a
    while n < b:
        t = ln(n)
        if n in PHOTOS:
            out.append({"photo": PHOTOS[n], "caption": ln(n + 2)})
            n += 3
            continue
        if t.strip():
            out.append({"p": t.strip()})
        n += 1
    return out

book = []
for slug, toc, body_title, start, group in SECTIONS:
    a, b = start + 1, ENDS[slug]
    bl = blocks(a, b)
    sec = {"slug": slug, "toc": toc, "title": sp(body_title), "group": group, "blocks": bl}
    if slug == "xu":
        # 署名“文刃”单列
        assert bl[0]["p"] == "文刃"
        sec["byline"] = "文刃"
        sec["blocks"] = bl[1:]
    if slug == "houji":
        # 末尾“拉斯维加斯的家”是照片说明（照片在说明之后）
        assert ln(693) == "拉斯维加斯的家" and ln(695) == "[]"
        sec["blocks"] = bl + [{"photo": "photo6", "caption": "拉斯维加斯的家"}]
    book.append(sec)

intro = ln(JI_INTRO[0]).strip()
colophon = [ln(n).strip() for n in range(697, 724) if ln(n).strip()]

# 照片6在“拉斯维加斯的家”之后；blocks() 在 houji 范围外，这里单独确认
assert ln(695) == "[]"

json.dump({"sections": book, "ji_intro": intro, "colophon": colophon},
          open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

total = sum(len(b.get("p", "")) for s in book for b in s["blocks"])
print("sections", len(book), "chars", total)
