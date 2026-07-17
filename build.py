import json, os, re, html as ihtml

ROOT = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(ROOT, "structure_full.json")))
ASSETS = os.path.join(ROOT, "assets")
EXT = {}
for f in os.listdir(ASSETS):
    name, ext = os.path.splitext(f)
    EXT[name] = ext

def esc(s):
    return ihtml.escape(s or "", quote=False)

def img_tag(name, cls="media"):
    ext = EXT.get(name, ".png")
    return f'<img class="{cls}" src="assets/{name}{ext}" alt="" loading="lazy">'

MODE_TABLE = [
    ("Pace On", "낯선 움직임을 무리 없이 시작하게 하는 기본 안전 모드", "착지, 방향 전환, 균형이 흔들리는 순간",
     "발목과 하체 움직임의 과한 범위를 잡고, 와이어 장력으로 흔들림을 제한", "발목이 덜 꺾이고, 착지와 방향 전환이 안정적으로 느껴짐"),
    ("Boost On", "반복 구간에 일부러 묵직한 저항을 더하는 훈련 모드", "다리를 앞으로 내밀거나 스윙하는 구간",
     "와이어가 순순히 풀리지 않도록 역방향 브레이크를 걸어 저항 생성", "모래주머니를 찬 듯 묵직하게 잡히고, 반복 후 몸이 더 가볍게 느껴짐"),
    ("Press On", "꺼지는 리듬을 다시 앞으로 이어주는 추진 보조 모드", "발뒤꿈치가 지면에서 떨어지고 앞으로 치고 나가는 순간",
     "와이어 장력으로 발목 중심축을 보조해 뒤꿈치를 위로 끌어올림", "다음 발이 더 쉽게 나가고, 후반 리듬이 끊기지 않음"),
    ("Quiet On", "집 안에서도 사뿐히 움직이게 하는 실내 착지 모드", "발이 지면에 닿기 직전부터 뒤꿈치가 완전히 닿는 순간",
     "와이어를 미세하게 풀어 체중 일부를 위에서 받치고 착지를 부드럽게 감속", "발을 쿵 찍지 않고 조용히 내려놓는 느낌"),
]

def render_table():
    head = "".join(f"<th>{h}</th>" for h in ["Mode", "제품 의미", "개입 타이밍", "기구적 개입", "사용자 체감"])
    rows = ""
    for r in MODE_TABLE:
        rows += "<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>"
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'

def is_subhead(text):
    if "\n" in text or len(text) > 42:
        return False
    return not (text.endswith(".") or text.endswith("다") or text.endswith("요"))

URL_RE = re.compile(r'(https?://\S+)')

def linkify(escaped_text):
    return URL_RE.sub(lambda m: f'<a href="{m.group(1)}" target="_blank" rel="noopener">{m.group(1)}</a>', escaped_text)

def render_p(text):
    text = text.strip()
    if not text:
        return ""
    if is_subhead(text) and not text.startswith("http"):
        return f'<p class="subhead">{esc(text)}</p>'
    parts = [linkify(esc(p)) for p in text.split("\n")]
    return f'<p class="body">{"<br>".join(parts)}</p>'

def render_h4(text):
    lines = text.split("\n")
    if lines[0].strip().startswith("{"):
        label = lines[0].strip()
        headline = lines[1].strip() if len(lines) > 1 else ""
        return f'<div class="step-head"><p class="step-label">{esc(label)}</p><h3 class="step-title">{esc(headline)}</h3></div>'
    return f'<h2 class="chapter-title">{"<br>".join(esc(l.strip()) for l in lines)}</h2>'

def render_quote(node):
    inner = render_children(node.get("c", [])) if node.get("c") else ""
    return f'<blockquote class="quote">{esc(node["x"])}</blockquote>{inner}'

def render_toggle(node):
    body = render_children(node.get("c", []))
    return f'<details class="toggle"><summary>{esc(node["x"])}</summary><div class="toggle-body">{body}</div></details>'

def render_callout(node):
    x = node.get("x", "")
    children = node.get("c", [])
    if not x:
        return f'<div class="group">{render_children(children)}</div>'
    body_children = children
    label_html = ""
    if body_children and body_children[0]["t"] == "P" and "\n" in body_children[0].get("x", ""):
        label, headline = body_children[0]["x"].split("\n", 1)
        label_html = f'<p class="finding-label">{esc(label.strip())}</p><p class="finding-headline">{esc(headline.strip())}</p>'
        body_children = body_children[1:]
    return (f'<div class="finding"><div class="finding-icon">{esc(x)}</div>'
            f'<div class="finding-body">{label_html}{render_children(body_children)}</div></div>')

def render_table_node():
    return render_table()

def render_node(n):
    t = n["t"]
    if t == "P":
        return render_p(n.get("x", ""))
    if t == "H4" or t == "H3":
        return render_h4(n.get("x", ""))
    if t == "IMG":
        return f'<figure class="figure">{img_tag(n["src"])}</figure>'
    if t == "TOGGLE":
        return render_toggle(n)
    if t == "CALLOUT":
        return render_callout(n)
    if t == "QUOTE":
        return render_quote(n)
    if t == "HR":
        return ""
    if t == "TABLE":
        return render_table_node()
    return ""

def render_children(items):
    out = []
    i = 0
    while i < len(items):
        n = items[i]
        if n["t"] == "LI":
            group = []
            while i < len(items) and items[i]["t"] == "LI":
                group.append(items[i])
                i += 1
            lis = "".join(f"<li>{esc(g.get('x',''))}</li>" for g in group)
            out.append(f"<ul class='list'>{lis}</ul>")
            continue
        out.append(render_node(n))
        i += 1
    return "".join(out)

items = data
MARKERS = [
    "01 From Routine to Challenge",
    "02 Challenge Spark",
    "03 Target",
    "04 Solution",
    "05 Wearable Robotics",
    "06 Station",
    "07 Projection Unit",
    "08 Scenario",
    "09 Extensibility",
]

def find_marker_idx(m):
    for idx, n in enumerate(items):
        if n.get("t") == "P" and n.get("x") == m:
            return idx
    raise ValueError(m)

marker_idx = [find_marker_idx(m) for m in MARKERS]

first_hr = None
for idx, n in enumerate(items):
    if n["t"] == "HR":
        first_hr = idx
        break
hero_items = items[first_hr + 1: marker_idx[0]]
hero_items = [n for n in hero_items if n["t"] != "HR" and n.get("src") != "img_02"]

sections = []
for i, m in enumerate(MARKERS):
    start = marker_idx[i]
    end = marker_idx[i + 1] if i + 1 < len(marker_idx) else None
    if m == "09 Extensibility":
        seg = items[start:start + 4]
    else:
        seg = items[start:end]
    sections.append((m, seg))

# move "Play with Newton!" teaser from tail of section 07 to head of section 08
sec07 = sections[6][1]
sec08 = sections[7][1]
if sec07 and sec07[-1].get("t") == "QUOTE" and sec07[-1].get("x") == "Play with Newton!":
    teaser = sec07.pop()
    sec08.insert(1, teaser)  # after the "08 Scenario" marker P itself (index 0)

app_start = marker_idx[-1] + 4
appendix_items = [n for n in items[app_start:] if n["t"] != "HR"]

def extract_hero(items):
    for i, n in enumerate(items):
        if n["t"] == "IMG":
            return n, items[:i] + items[i + 1:]
    return None, items

def first_paragraph(items):
    for i, n in enumerate(items):
        if n["t"] == "P":
            return n, items[:i] + items[i + 1:]
    return None, items

def render_vertical(page_id, kicker, title_html, body_items, hero):
    """549/827 layout: head (title left / intro-body right), content, optional big bottom image."""
    intro_p, rest = first_paragraph(body_items)
    intro_html = render_node(intro_p) if intro_p else ""
    content_html = render_children(rest)
    hero_html = f'<figure class="page-hero">{img_tag(hero["src"])}</figure>' if hero else ""
    data = f' data-page="{page_id}"' if page_id else ""
    kicker_html = f'<p class="kicker">{esc(kicker)}</p>' if kicker else ""
    return f'''
<div class="page"{data}>
  <div class="page-scroll">
    <div class="page-head">
      <div class="head-left">{kicker_html}{title_html}</div>
      <div class="head-right">{intro_html}</div>
    </div>
    <div class="page-content">{content_html}</div>
    {hero_html}
  </div>
</div>'''

def render_page(marker, seg):
    num, kicker = marker.split(" ", 1)
    body = seg[1:]  # drop marker P
    h4 = next((n for n in body if n["t"] in ("H4", "H3")), None)
    rest = [n for n in body if n is not h4]
    title_html = render_h4(h4["x"]) if h4 else ""
    # Scenario page (08) uses the vertical layout with its lead image removed
    if num == "08":
        _, rest_no_hero = extract_hero(rest)
        return render_vertical(f"sec-{num}", kicker, title_html, rest_no_hero, None)
    # everything else keeps the left-image / right-text two-column layout
    hero, rest = extract_hero(rest)
    media_html = img_tag(hero["src"]) if hero else ""
    content_html = render_children(rest)
    return f'''
<div class="page" data-page="sec-{num}">
  <div class="page-media">{media_html}</div>
  <div class="page-text">
    <p class="kicker">{esc(kicker)}</p>
    {title_html}
    {content_html}
  </div>
</div>'''

sections_html = "".join(render_page(m, seg) for m, seg in sections)

# intro page (827 layout): kicker "Now, your turn!", big title "NEWTON"
intro_hero, intro_rest = extract_hero(hero_items)
intro_body = [n for n in intro_rest if n.get("x") != "Now, your turn!"]
intro_page_html = render_vertical("intro", "Now, your turn!",
                                  '<h2 class="chapter-title">NEWTON</h2>', intro_body, intro_hero)

appendix_html = render_children(appendix_items)

# label, first page, member pages
NAV_GROUPS = [
    ("Background", "sec-01", ["sec-01", "sec-02", "sec-03"]),
    ("Solution", "sec-04", ["sec-04"]),
    ("Products", "sec-05", ["sec-05", "sec-06", "sec-07"]),
    ("Scenario", "sec-08", ["sec-08"]),
    ("Extensibility", "sec-09", ["sec-09"]),
]
nav_html = "".join(
    f'<button type="button" class="pill" data-target="{target}" data-members="{",".join(members)}">{esc(label)}</button>'
    for label, target, members in NAV_GROUPS
)

TEMPLATE = open(os.path.join(ROOT, "template.html")).read()
out = (TEMPLATE.replace("{{NAV}}", nav_html)
       .replace("{{INTRO_PAGE}}", intro_page_html)
       .replace("{{SECTIONS}}", sections_html)
       .replace("{{APPENDIX}}", appendix_html))
open(os.path.join(ROOT, "index.html"), "w").write(out)
print("done", len(sections_html), len(intro_page_html), len(appendix_html))
