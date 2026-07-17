import json, os, re, copy, html as ihtml

ROOT = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(ROOT, "structure_full.json")))
ASSETS = os.path.join(ROOT, "assets")
EXT = {}
for f in os.listdir(ASSETS):
    name, ext = os.path.splitext(f)
    EXT[name] = ext

def esc(s):
    return ihtml.escape(s or "", quote=False)

# ---- translation cache (free): build reads translations.json and attaches data-en ----
TRANS_PATH = os.path.join(ROOT, "translations.json")
TRANS = json.load(open(TRANS_PATH, encoding="utf-8")) if os.path.exists(TRANS_PATH) else {}
_missing = set()

def _has_kr(s):
    return any("가" <= c <= "힣" for c in (s or ""))

def en_attr(ko):
    """returns ' data-en=\"...\"' when an English translation exists for this Korean text."""
    ko = (ko or "").strip()
    if not ko or not _has_kr(ko):
        return ""
    e = TRANS.get(ko, "")
    if not e:
        _missing.add(ko)
        return ""
    return ' data-en="' + ihtml.escape(e, quote=True).replace("\n", " ") + '"'

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

def is_citation(text):
    # APA-style source line: (year) + a couple of periods + fairly long, or a bare DOI/URL line
    has_year = bool(re.search(r'\(\d{4}', text))
    has_link = "doi.org" in text or text.startswith("http")
    return (has_year and text.count(".") >= 2 and len(text) > 40) or (has_link and len(text) < 130)

def render_p(text):
    text = text.strip()
    if not text:
        return ""
    a = en_attr(text)
    if is_citation(text):
        return f'<p class="cite"{a}>{linkify(esc(text))}</p>'
    # numbered sub-title "01 …" → bold heading (+ body when it carries a description line)
    if re.match(r'^\d\d?\s', text):
        segs = text.split("\n", 1)
        head = segs[0].strip()
        rest = segs[1].strip() if len(segs) > 1 else ""
        html = f'<p class="subhead"{en_attr(head)}>{esc(head)}</p>'
        if rest:
            parts = [linkify(esc(p)) for p in rest.split("\n")]
            html += f'<p class="body"{en_attr(rest)}>{"<br>".join(parts)}</p>'
        return html
    if is_subhead(text) and not text.startswith("http"):
        return f'<p class="subhead"{a}>{esc(text)}</p>'
    parts = [linkify(esc(p)) for p in text.split("\n")]
    return f'<p class="body"{a}>{"<br>".join(parts)}</p>'

def render_h4(text):
    lines = text.split("\n")
    if lines[0].strip()[:1] in ("{", "("):   # "(1)…" and "{1}…" → red caption (label) + title
        label = lines[0].strip()
        headline = lines[1].strip() if len(lines) > 1 else ""
        return f'<div class="step-head"><p class="step-label">{esc(label)}</p><h3 class="step-title"{en_attr(headline)}>{esc(headline)}</h3></div>'
    return f'<h2 class="chapter-title"{en_attr(text)}>{"<br>".join(esc(l.strip()) for l in lines)}</h2>'

def render_quote(node):
    inner = render_children(node.get("c", [])) if node.get("c") else ""
    return f'<blockquote class="quote"{en_attr(node["x"])}>{esc(node["x"])}</blockquote>{inner}'

def render_toggle(node):
    body = render_children(node.get("c", []))
    return f'<details class="toggle"><summary>{esc(node["x"])}</summary><div class="toggle-body">{body}</div></details>'

def render_callout(node):
    x = node.get("x", "")
    children = node.get("c", [])
    if not x:
        return render_children(children)   # toggles inside get grouped by render_children
    body_children = list(children)
    head_html = ""
    # first paragraph → bold title (or label + headline when it carries a \n)
    if body_children and body_children[0]["t"] == "P":
        first = body_children[0].get("x", "")
        if "\n" in first:
            label, headline = first.split("\n", 1)
            head_html = (f'<p class="finding-label"{en_attr(label.strip())}>{esc(label.strip())}</p>'
                         f'<p class="finding-headline"{en_attr(headline.strip())}>{esc(headline.strip())}</p>')
        else:
            head_html = f'<p class="finding-title"{en_attr(first)}>{esc(first)}</p>'
        body_children = body_children[1:]
    # trailing short "종목 / 이름" → caption
    caption_html = ""
    if body_children and body_children[-1]["t"] == "P":
        last = body_children[-1].get("x", "")
        if "/" in last and len(last) <= 30:
            body_children = body_children[:-1]
            caption_html = f'<p class="finding-caption"{en_attr(last)}>{esc(last)}</p>'
    inner = render_children(body_children)
    # icon = newton symbol logo (CSS mask); original emoji dropped
    return (f'<div class="finding"><div class="finding-icon"></div>'
            f'<div class="finding-body">{head_html}{inner}{caption_html}</div></div>')

def render_table_node():
    return render_table()

def render_node(n):
    t = n["t"]
    if t == "P":
        if n.get("credit"):
            return f'<p class="credit">{esc(n["x"])}</p>'
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
            lis = "".join(f"<li{en_attr(g.get('x',''))}>{esc(g.get('x',''))}</li>" for g in group)
            out.append(f"<ul class='list'>{lis}</ul>")
            continue
        if n["t"] == "TOGGLE":
            # consecutive toggles always share one grey container
            tg = []
            while i < len(items) and items[i]["t"] == "TOGGLE":
                tg.append(render_node(items[i]))
                i += 1
            out.append(f'<div class="group">{"".join(tg)}</div>')
            continue
        out.append(render_node(n))
        i += 1
    return "".join(out)

items = copy.deepcopy(data)

# ---- latest text (patches applied to node .x by exact match) ----
TEXT_PATCHES = {
    "보던 움직임을, \n해보는 움직임으로": "내 플레이를 깨우는\n하체 웨어러블 로보틱스",
    "내가 있는 곳이, 바로 도전의 필드": "공간을 도전의 필드로\n바꾸는 프로젝션 유닛",
    "도전이 시작될 자리를 만드는 스테이션": "도전이 시작될\n자리를 만드는 스테이션",
    "{1} Home First Trial\n처음의 한 걸음은, 집에서도 충분하니까":
        "(2) Step by Step, Into Play\n처음의 한 걸음은, 집에서도 충분하니까",
    "{2} Outdoor Running\n한번 움직인 마음은, 바깥으로 이어진다":
        "한번 움직인 마음은,\n바깥으로 이어진다",
    "{3} Basketball Personal Practice\n혼자 익힌 리듬이, 함께 움직일 자신감으로":
        "혼자 익힌 리듬이,\n함께 움직일 자신감으로",
    "{4} Home Together Play\n혼자 익힌 설렘이, 함께 하는 재미가 되어":
        "혼자 익힌 설렘이,\n함께 하는 재미가 되어",
    "{5} Dock and Remember\n오늘의 두근거림을, 다음 도전으로":
        "(3) From Movement to Momentum\n오늘의 두근거림을, 다음 도전으로",
    "움직임이 끝난 뒤에도, NEWTON은 다음 플레이를 준비합니다. 하체 웨어러블은 포터블 스테이션에서 다시 충전되고, 패브릭 파츠는 분리해 산뜻하게 관리됩니다. 오늘 몸에 남은 리듬과 막혔던 순간은 다음 도전을 위한 단서가 됩니다. 오늘의 플레이는 여기서 멈추지 않고 더 가볍고, 더 익숙한 다음 움직임으로 이어집니다.":
        "움직임이 끝난 뒤에도, NEWTON은 다음 플레이를 준비합니다. 오늘의 리듬과 흔들렸던 순간은 리포트로 남아 다음 도전의 단서가 됩니다. 하체 웨어러블은 다시 충전되고, 패브릭 파츠는 산뜻하게 관리됩니다. 오늘의 플레이는 그렇게 다음 움직임으로 이어집니다.",
    "NEWTON은 스포츠를 시작하고 더 깊이 도전하는 경험에서 출발합니다.\n하지만 우리가 설계한 것은 특정 종목의 기술이 아니라, 낯선 움직임을 각자의 몸에 맞는 속도로 시작하게 하는 방식입니다. 이 방식은 새로운 스텝을 익히는 순간을 넘어, 처음 균형을 배우고 다시 걷는 감각을 되찾는 순간까지 확장될 수 있습니다.\n누구나 자신의 차례를 믿고, 다음 움직임을 시작할 수 있도록.":
        "NEWTON은 스포츠를 시작하고 도전하는 경험에서 출발합니다.\n하지만 핵심은 하나의 종목이 아니라, 낯선 움직임을 내 몸의 속도로 시작하게 하는 구조에 있습니다. 이 구조는 러닝, 복싱, 농구를 넘어 균형을 배우고 다시 걷는 감각을 회복하는 순간까지 확장될 수 있습니다. 누구나 자신의 차례를 믿고, 새로운 움직임에 도전할 수 있도록.",
}

def apply_patches(nodes):
    for n in nodes:
        if n.get("x") in TEXT_PATCHES:
            n["x"] = TEXT_PATCHES[n["x"]]
        if n.get("c"):
            apply_patches(n["c"])

apply_patches(items)

# ---- content re-arrangement ----
def pop_by(container, pred):
    for i, n in enumerate(container):
        if pred(n):
            return container.pop(i)
        if n.get("c"):
            f = pop_by(n["c"], pred)
            if f is not None:
                return f
    return None

def parent_list_of(container, pred):
    for n in container:
        if pred(n):
            return container
        if n.get("c"):
            r = parent_list_of(n["c"], pred)
            if r is not None:
                return r
    return None

is_toggle = lambda name: (lambda n: n.get("t") == "TOGGLE" and name in (n.get("x") or ""))

# pull the toggles / image we're relocating
diff_toggle  = pop_by(items, is_toggle("차별화"))
touch_toggle = pop_by(items, is_toggle("터치포인트"))
flow_toggle  = pop_by(items, is_toggle("전체 시나리오"))
wire_toggle  = pop_by(items, is_toggle("와이어프레임"))
img14 = pop_by(items, lambda n: n.get("src") == "img_14")

# "차별화 포인트" → next to "감각 Pack" toggle inside Solution
sol_list = parent_list_of(items, is_toggle("감각 Pack"))
if sol_list is not None and diff_toggle:
    sol_list.append(diff_toggle)

# delete the now-empty "Now Your Turn!" section (H3 + its emptied callout)
pop_by(items, lambda n: n.get("t") == "H3" and "Now Your Turn" in (n.get("x") or ""))
pop_by(items, lambda n: n.get("t") == "CALLOUT" and not n.get("x") and not n.get("c"))
# remove the standalone "Play with Newton!" quote (promoted to its own page)
pop_by(items, lambda n: n.get("t") == "QUOTE" and "Play with Newton" in (n.get("x") or ""))

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

# appendix page is removed entirely (wireframe toggle relocated, simulator dropped)

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

def render_vertical(page_id, kicker, title_html, body_items, hero, scroll_hint=False):
    """549/827 layout: head (title left / intro-body right), content, optional big bottom image."""
    intro_p, rest = first_paragraph(body_items)
    intro_html = render_node(intro_p) if intro_p else ""
    content_html = render_children(rest)
    hero_html = f'<figure class="page-hero">{img_tag(hero["src"])}</figure>' if hero else ""
    data = f' data-page="{page_id}"' if page_id else ""
    kicker_html = f'<p class="kicker">{esc(kicker)}</p>' if kicker else ""
    hint_html = ('<div class="scroll-hint" aria-hidden="true">'
                 '<span class="scroll-mouse"></span>'
                 '<span class="chevs"><i class="chev"></i><i class="chev"></i><i class="chev"></i></span>'
                 '</div>') if scroll_hint else ""
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
  {hint_html}
</div>'''

KICKER_OVERRIDE = {"03": "For Those Who Turn Trends Into Play", "08": "(1) A Spark to Move"}

def render_page(marker, seg):
    num, kicker = marker.split(" ", 1)
    kicker = KICKER_OVERRIDE.get(num, kicker)
    body = seg[1:]  # drop marker P
    h4 = next((n for n in body if n["t"] in ("H4", "H3")), None)
    rest = [n for n in body if n is not h4]
    title_html = render_h4(h4["x"]) if h4 else ""
    # Scenario page (08): vertical layout — toggle sits right under the body, image below it
    if num == "08":
        hero, rest2 = extract_hero(rest)
        ci = next((i for i, n in enumerate(rest2) if n.get("t") == "CALLOUT"), None)
        if hero is not None:
            rest2.insert(ci + 1 if ci is not None else 0, hero)
        return render_vertical(f"sec-{num}", kicker, title_html, rest2, None, scroll_hint=True)
    # everything else keeps the left-image / right-text two-column layout
    hero, rest = extract_hero(rest)
    if num == "02":
        # sec-02: 4-image cross-fade loop (2s each), 3-1..3-4
        seq = [1, 2, 3, 4, 1]  # last = first, for a seamless loop with no white gap
        media_html = ('<div class="fade-stack"><div class="fade-track">'
                      + "".join(f'<img src="assets/fade{i}.png" alt="" loading="lazy">' for i in seq)
                      + '</div></div>')
    else:
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

# "Play with Newton!" — new first Scenario page: two-column (left image + right text/toggles)
playwith_toggles = [t for t in (touch_toggle, flow_toggle, wire_toggle) if t]
playwith_media = img_tag(img14["src"]) if img14 else ""
playwith_page = f'''
<div class="page" data-page="playwith">
  <div class="page-media">{playwith_media}</div>
  <div class="page-text">
    <p class="kicker">Scenario</p>
    <h2 class="chapter-title">Play with Newton!</h2>
    {render_children(playwith_toggles)}
  </div>
</div>'''

pages_out = []
for m, seg in sections:
    pages_out.append(render_page(m, seg))
    if m.startswith("07"):
        pages_out.append(playwith_page)
sections_html = "".join(pages_out)

# intro page (827 layout): kicker "Now, your turn!", big title "NEWTON"
intro_hero, intro_rest = extract_hero(hero_items)
intro_body = [n for n in intro_rest if n.get("x") != "Now, your turn!"]
intro_body.append({"t": "P", "x": "송시헌, 이일여, 김소진, 박주원, 전다빈", "credit": True})
intro_page_html = render_vertical("intro", "Now, your turn!",
                                  '<h2 class="chapter-title">NEWTON</h2>', intro_body, intro_hero)

# label, first page, member pages
NAV_GROUPS = [
    ("Background", "sec-01", ["sec-01", "sec-02", "sec-03"]),
    ("Solution", "sec-04", ["sec-04"]),
    ("Products", "sec-05", ["sec-05", "sec-06", "sec-07"]),
    ("Scenario", "playwith", ["playwith", "sec-08"]),
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
       .replace("{{APPENDIX}}", ""))
open(os.path.join(ROOT, "index.html"), "w").write(out)
print("done", len(sections_html), len(intro_page_html))
if _missing:
    with open("/tmp/missing.json", "w", encoding="utf-8") as f:
        json.dump(sorted(_missing, key=len), f, ensure_ascii=False, indent=0)
    print(f"[i18n] 미번역 {len(_missing)}개 → /tmp/missing.json")
