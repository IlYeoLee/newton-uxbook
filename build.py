import json, os, re, copy, html as ihtml

ROOT = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(ROOT, "structure_full.json"), encoding="utf-8"))
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
    e = TRANS.get(ko) or TRANS.get(ko.replace("\n", " "), "")  # titles may carry a \n line-break; key is the space form
    if not e:
        _missing.add(ko)
        return ""
    return ' data-en="' + ihtml.escape(e, quote=True).replace("\n", " ") + '"'

# hero images have hi-res 16:9 mobile variants (desktop keeps its portrait crop)
MOBILE_SRC = {
    "img_04": "m2", "img_06": "m4", "img_10": "m5", "img_18": "m6",
    "img_22": "m7", "img_23": "m8", "img_14": "m9", "img_37": "m11",
}

def img_tag(name, cls="media"):
    ext = EXT.get(name, ".png")
    m = MOBILE_SRC.get(name)
    mattr = f' data-msrc="assets/{m}.png"' if m else ""
    return f'<img class="{cls}" src="assets/{name}{ext}" alt="" loading="lazy"{mattr}>'

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
    # a real reference line: has a URL/DOI, or is mostly Latin with a (year).
    # Korean explanatory body that merely cites "Author et al.(2025)은 …했다" is NOT a source.
    if "doi.org" in text or "http" in text:
        return True
    kr = sum(1 for c in text if "가" <= c <= "힣")
    if kr >= 10:
        return False
    has_year = bool(re.search(r'\(\d{4}', text))
    return has_year and text.count(".") >= 2 and len(text) > 40

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
    return f'<details class="toggle"><summary{en_attr(node["x"])}>{esc(node["x"])}</summary><div class="toggle-body">{body}</div></details>'

def strip_lead_emoji(s):
    return re.sub(r'^[\U0001F000-\U0001FAFF☀-➿←-⇿️\s]+', '', s or "")

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
            head_html = (f'<p class="finding-label"{en_attr(label.strip())}>{esc(strip_lead_emoji(label.strip()))}</p>'
                         f'<p class="finding-headline"{en_attr(headline.strip())}>{esc(strip_lead_emoji(headline.strip()))}</p>')
        else:
            head_html = f'<p class="finding-title"{en_attr(first)}>{esc(strip_lead_emoji(first))}</p>'
        body_children = body_children[1:]
    # trailing short "종목 / 이름" → caption
    caption_html = ""
    if body_children and body_children[-1]["t"] == "P":
        last = body_children[-1].get("x", "")
        if "/" in last and len(last) <= 30:
            body_children = body_children[:-1]
            caption_html = f'<p class="finding-caption"{en_attr(last)}>{esc(last)}</p>'
    # 콜아웃 안이라고 예외를 두지 않는다 - 토글은 어느 깊이에서도 같은 컨테이너를 쓴다
    inner = render_children(body_children)
    # icon = newton symbol logo (CSS mask); original emoji dropped
    return (f'<div class="finding"><div class="finding-icon"></div>'
            f'<div class="finding-body">{head_html}{inner}{caption_html}</div></div>')

def render_table_node():
    return render_table()

# ---- 시나리오 페이지 미디어 ----
# 번호는 위에서부터 "타이틀+본문" 그룹을 센 순번이다(페이지 헤더가 1번). 한 그룹에
# 영상/이미지가 둘 이상 올 수 있어 리스트로 둔다. 원본 구조의 이미지는 그룹째 갈린다.
SCENARIO_MEDIA = {
    1: ["sc1.mp4", "sc1-2.png"],   # 마음이 먼저 움직이는 순간
    2: ["sc2.mp4"],                # 처음의 한 걸음은 집에서도 충분하니까
    3: ["sc3.mp4"],                # 한번 움직인 마음은 바깥으로 이어진다
    4: ["sc4.mp4"],                # 혼자 익힌 리듬이 함께 움직일 자신감으로
    5: ["sc5.mp4"],                # 혼자 익힌 설렘이 함께 하는 재미가 되어
    6: ["sc6.mp4"],                # 오늘의 두근거림을 다음 도전으로
}
SILENT = {"sc5.mp4"}   # 오디오 트랙이 없는 영상 → 사운드 버튼을 달지 않는다

def video_tag(src, wrap="figure v-figure"):
    """자동재생은 스크롤 위치가 정하고(스크립트), 소리는 사용자가 켤 때만 난다."""
    stem = src.rsplit(".", 1)[0]
    sound = "" if src in SILENT else (
        '<button class="v-sound" type="button" aria-pressed="false" aria-label="소리 켜기">'
        '<svg viewBox="0 0 24 24" aria-hidden="true"><use href="#ic-mute"></use></svg></button>')
    return (
        # --poster 는 모바일에서 세로 화면을 메우는 흐린 배경에 쓴다. 영상을 하나 더
        # 얹으면 폰에서 디코딩이 두 배가 되므로 정지 포스터로 채운다.
        f'<figure class="{wrap}" style="--poster:url(assets/{stem}-poster.jpg)">'
        f'<video src="assets/{src}" poster="assets/{stem}-poster.jpg" '
        f'playsinline muted loop preload="metadata"></video>'
        f'<div class="v-bar">'
        f'<button class="v-play" type="button" aria-pressed="false" aria-label="재생">'
        f'<svg viewBox="0 0 24 24" aria-hidden="true"><use href="#ic-play"></use></svg></button>'
        f'<div class="v-seek" role="slider" tabindex="0" aria-label="재생 위치" '
        f'aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><i class="v-fill"></i></div>'
        f'<span class="v-time">0:00</span>{sound}'
        f'</div></figure>')

def render_media(files):
    out = []
    for f in files:
        if f.endswith(".mp4"):
            out.append(video_tag(f))
        else:
            out.append(f'<figure class="figure"><img src="assets/{f}" alt="" loading="lazy"></figure>')
    return "".join(out)

def apply_scenario_media(items, media):
    """타이틀(H4/H3)로 그룹을 끊고, 각 그룹의 원본 이미지를 매핑된 미디어로 갈아끼운다.
    미디어는 그 그룹의 첫 이미지 자리에 들어가고, 같은 그룹의 나머지 이미지는 버린다."""
    out, group, placed = [], 1, set()
    for n in items:
        if n["t"] in ("H4", "H3"):
            group += 1
        if n["t"] == "IMG" and group in media:
            if group not in placed:
                placed.add(group)
                out.append({"t": "MEDIA", "files": media[group]})
            continue
        out.append(n)
    missing = set(media) - placed - {1}
    if missing:
        raise ValueError(f"시나리오 그룹 {sorted(missing)} 에 이미지 자리가 없다")
    return out

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
    if t == "MEDIA":
        return render_media(n["files"])
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

def render_children(items, group_toggles=True):
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
        if n["t"] == "TOGGLE" and group_toggles:
            # consecutive toggles share one grey container (skipped inside a finding box)
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
    "보던 움직임을, \n해보는 움직임으로":
        "하체 웨어러블 로봇\nNewton",
    "내가 있는 곳이, 바로 도전의 필드":
        "어떤 곳이든 도전의 \n필드로 바꾸는 Core",
    "도전이 시작될 자리를 만드는 스테이션":
        "도전을 시작할 \n준비를 돕는 Station",
    "{2} Outdoor Running\n한번 움직인 마음은, 바깥으로 이어진다":
        "한번 움직인 마음은\n바깥으로 이어진다",
    "{3} Basketball Personal Practice\n혼자 익힌 리듬이, 함께 움직일 자신감으로":
        "혼자 익힌 리듬이\n함께 움직일 자신감으로",
    "{4} Home Together Play\n혼자 익힌 설렘이, 함께 하는 재미가 되어":
        "혼자 익힌 설렘이\n함께 하는 재미가 되어",
    "움직임이 끝난 뒤에도, NEWTON은 다음 플레이를 준비합니다. 하체 웨어러블은 포터블 스테이션에서 다시 충전되고, 패브릭 파츠는 분리해 산뜻하게 관리됩니다. 오늘 몸에 남은 리듬과 막혔던 순간은 다음 도전을 위한 단서가 됩니다. 오늘의 플레이는 여기서 멈추지 않고 더 가볍고, 더 익숙한 다음 움직임으로 이어집니다.":
        "플레이가 끝난 뒤에도 오늘의 움직임은 다음을 향해 이어집니다. 리포트는 꿈꾸던 플레이와 \n가까워진 정도를 보여주며, 움직임의 성취를 새로운 도전의 가능성으로 확장합니다. 함께 뛰었던 Newton은 스테이션 위에서 충전되고, 땀에 닿은 패브릭 파츠는 세탁하여 산뜻하게 보관됩니다. 오늘의 감각은 다음 도전을 기다리는 설렘으로 남습니다.",
    "NEWTON은 스포츠를 시작하고 더 깊이 도전하는 경험에서 출발합니다.\n하지만 우리가 설계한 것은 특정 종목의 기술이 아니라, 낯선 움직임을 각자의 몸에 맞는 속도로 시작하게 하는 방식입니다. 이 방식은 새로운 스텝을 익히는 순간을 넘어, 처음 균형을 배우고 다시 걷는 감각을 되찾는 순간까지 확장될 수 있습니다.\n누구나 자신의 차례를 믿고, 다음 움직임을 시작할 수 있도록.":
        "Newton은 스포츠를 시작하고 도전하는 경험에서 출발합니다.\n하지만 그 중심에는 하나의 종목이 아니라, 낯선 움직임을 내 몸의 속도로 시작하게 하는 구조에 있습니다. 그 가능성은 러닝, 복싱, 농구를 넘어 균형을 배우고 다시 걷는 감각을 회복하는 \n순간까지 확장될 수 있습니다. 누구나 자신의 차례를 믿고, 새로운 움직임에 도전할 수 있도록.",
    "NEWTON은 꿈꾸던 스포츠 콘텐츠를 내가 있는 곳에서 바로 도전할 수 있는 경험으로 바꿉니다. 바닥과 벽면에 펼쳐진 움직임의 단서를 따라가며, 보고만 있던 멋진 동작을 내 몸으로 시도하죠. 하체 웨어러블은 움직임의 감각을 조율해, 낯선 움직임도 내 플레이로 이어가게 돕습니다. 이제, 당신의 차례입니다!":
        "Newton은 꿈꾸던 스포츠 콘텐츠를 내가 있는 곳에서 바로 도전할 수 있는 \n경험으로 바꿉니다. 바닥과 벽면에 펼쳐진 움직임의 단서를 따라가며, 보고만 있던 멋진 동작을 내 몸으로 시도하죠. 하체 웨어러블은 움직임의 감각을 조율해, 낯선 움직임도 내 플레이로 이어가게 돕습니다. 이제, 당신의 차례입니다!",
    "운동은 해야 하지만, \n반복은 금방 지루해":
        "운동은 해야 하지만\n반복은 금방 지루해",
    "운동이 필요하다는 사실은 누구나 알고 있습니다. 하지만 규칙적인 운동을 꾸준히 이어가는 일은 쉽지 않습니다. 운동은 귀찮고 해야 할 일처럼 느껴지고, 같은 루틴, 같은 자세, 같은 기록 확인은 금방 지루해집니다. 사람들이 멈추는 건 운동을 싫어해서가 아니라, 다시 움직이고 싶게 만드는 장면을 아직 만나지 못했을 뿐입니다.":
        "운동이 필요하다는 사실은 누구나 알고 있습니다. 하지만 규칙적인 운동을 꾸준히 이어가는 일은 쉽지 않습니다. 운동은 귀찮고 해야 할 일처럼 느껴지며, 같은 루틴과 자세, 반복되는 기록 확인은 금세 지루해집니다. 사람들이 운동을 멈추는 것은 그 자체를 싫어해서가 아니라, 다시 움직이고 싶게 만드는 장면을 아직 만나지 못했기 때문입니다.",
    "새로운 움직임은 \n다시 몸을 움직이게 한다":
        "새로운 움직임은\n다시 몸을 움직이게 한다",
    "“나도 해보고 싶다”는 순간, 운동은 다시 뜨거워집니다. 경기 막판의 스텝백, 링 위를 가르는 풋워크, 결승선까지 무너지지 않는 러너의 페이스처럼 마음을 뺏는 움직임은 보는 순간 몸을 당깁니다. NEWTON은 그 장면을 저장에서 멈추지 않고, 지금 내가 있는 곳에서 바로 시도해볼 수 있는 도전으로 바꿉니다.":
        "“나도 해 보고 싶다”라는 마음이 드는 순간, 운동은 다시 뜨거워집니다. 경기 막판의 스텝백, 링 위를 가르는 풋워크, 결승선까지 페이스를 잃지 않는 러너의 움직임처럼 시선을 빼앗는 장면은 보는 순간 몸을 움직이고 싶게 만듭니다.",
    "NEWTON의 타깃은 멋진 움직임에 끌리고, 내가 있는 곳에서 바로 도전하고 싶은 라이트 액티브 유저입니다. 러닝 크루, 복싱 숏폼, 농구 하이라이트를 보며 해보고 싶다고 느끼는 사람들. 이들에게 운동은 숙제가 아니라, 저장하고 따라 해보고 싶은 추구미입니다. NEWTON은 그 추구미를 내가 있는 곳에서 바로 시작할 수 있는 도전으로 바꿉니다.":
        "Newton의 타깃은 멋진 움직임에 끌리고, 내가 있는 곳에서 바로 도전하고 싶은 라이트 액티브 유저입니다. 러닝 크루, 복싱 숏폼, 농구 하이라이트를 보며 해보고 싶다고 느끼는 사람들. \n이들에게 운동은 숙제가 아니라, 저장하고 따라 해보고 싶은 추구미입니다.",
    "움직임도 이제 고르고, \n구독하는 경험":
        "움직임도 이제 고르고\n구독하는 경험",
    "프로의 스텝, 크리에이터의 루틴, 동호회 고수의 한 수까지.\n따라 해보고 싶은 움직임은 NEWTON에서 Challenge Pack이 됩니다. 지금 끌리는 Pack을 고르면, NEWTON은 그 움직임을 따라 해볼 수 있는 단서로 풀어냅니다. 보고 저장한 움직임은 벽면과 바닥, 야외 지면 위로 펼쳐지고 내가 있는 공간에서 바로 시작됩니다.":
        "프로의 스텝, 크리에이터의 루틴, 동호회 고수의 한 수까지.\n따라 해 보고 싶은 움직임은 Challenge Pack이 됩니다. 지금 끌리는 Pack을 고르면, \nNewton은 그 움직임을 따라 해 볼 수 있는 단서로 펼쳐냅니다. 보고 저장해 둔 움직임은 벽면과 바닥, 야외 지면 위에 이어지고, 내가 있는 공간에서 바로 시작할 수 있는 도전이 됩니다.\n\n▶ Newton의 전체 플레이 여정 보기",
    "하체 웨어러블의 IMU센서는 디딤과 착지, 회전과 보폭을 직접 읽습니다. 스테이션에 존재하는 카메라센서와 개인 3D 모델을 더하면 상체 움직임과 체형 기반 비교까지 확장될 수 있습니다.":
        "Newton은 IMU 센서를 비롯한 다중 감각 센서를 통해 사용자의 움직임을 실시간으로 이해하고 돕는 웨어러블 로봇입니다. BLDC 모터를 기반으로 구성된 콤팩트한 장력 구조를 통해 \n사용자에게 최적화된 물리적 보조를 제공합니다. 이를 통해 관절과 근육의 부담을 최소화하고, \n누구나 편안하고 안정적인 상태에서 운동 본연의 즐거움에 집중하게 합니다.",
    "프로젝션 유닛은 Challenge Pack의 움직임을 화면 밖으로 꺼내, 내가 있는 공간 위에 펼칩니다. 책상 앞의 시작 넛지, 집 안의 벽면 가이드, 밖에서의 지면 위 스텝까지. 발 위치와 리듬, 방향, 위험 범위는 따라 해볼 수 있는 단서로 눈앞에 펼쳐집니다. 몸을 여는 스트레칭부터 동작 습득, 실전 연습까지. 화면 속 움직임은 어디에 있든 내 몸으로 시작되는 플레이로 이어집니다.":
        "Core 유닛은 Challenge Pack의 움직임을 레이저 빔 스캐닝(LBS) 방식으로 내가 있는 공간에 투사합니다. Newton과 Station에 연동해 책상 앞과 실내 벽면, 야외 지면 등 다양한 공간에 \n시각적 가이드를 펼치며, 해 보고 싶었던 움직임을 눈앞에서 직접 따라 할 수 있도록 돕습니다.",
    "스테이션은 하체 웨어러블을 충전하고 보관하며, 착용 전 준비 상태를 정돈하는 거치형 허브입니다. 운동을 시작할 때는 웨어러블의 상태를 확인하고, 프로젝션 유닛이 안정적으로 놓일 위치와 각도를 잡아줍니다. NEWTON의 다음 움직임은 이 자리에서 준비되고, 하체 웨어러블을 착용하는 순간 오늘의 도전으로 이어집니다.":
        "Station은 Newton을 충전하고 보관하는 거치형 허브입니다. 운동하지 않을 때는 하드웨어의 상태를 점검하고, 실내에서 Core 유닛이 놓일 위치와 투사 각도를 조정합니다. 다음 움직임은 \n이 자리에서 준비되고, 웨어러블 로봇을 착용하는 순간 새로운 도전으로 이어집니다.",
    "책상 앞에 오래 앉아 굳어 있던 몸 앞에, 포터블 스테이션은 지금 끌릴 만한 Challenge Pack을 짧게 띄웁니다. 어릴 때 배워봤던 복싱의 회피 스텝과 짧은 풋워크 하이라이트가 집 안에 펼쳐지고, 투사된 시작 버튼은 다시 움직여보고 싶은 마음을 당깁니다. 누르는 순간, 운동은 해야 할 일이 아니라 지금 바로 시작해보고 싶은 도전이 됩니다":
        "책상 앞에 오래 앉아 몸이 굳어 갈 때, Station은 지금 끌릴 만한 Challenge Pack을 짧게 띄웁니다. 어릴 때 배워 본 복싱의 회피 스텝과 펀치 하이라이트가 공간 위에 펼쳐지고, 투사된 시작 버튼은 다시 몸을 움직이고 싶은 마음을 끌어당깁니다. 버튼을 누르는 순간, 해야 할 운동은 지금 바로 해 보고 싶은 플레이로 바뀝니다.",
    "{1} Home First Trial\n처음의 한 걸음은,\n집에서도 충분하니까":
        "(2) Play On, Step by Step\n처음의 한 걸음은\n집에서도 충분하니까",
    "Pack을 고르면, 방 안의 벽면이 조용한 링으로 바뀝니다. 굳은 몸을 스트레칭으로 열고, Quiet On으로 발소리와 충격을 낮춥니다. 벽에는 복싱 고수의 리듬과 가상 상대의 공격 범위가 펼쳐지고, 한 발 피하고 다시 들어가며 짧은 스파링을 시작합니다. 소음 부담 없이 완성한 첫 움직임은, 또 다른 도전을 해보고 싶은 재미로 이어집니다.":
        "Pack을 고르면 방 안의 벽면이 조용한 링이 됩니다. 스트레칭으로 굳은 몸을 열고, 실내에서도 부담 없이 움직일 준비를 합니다. 벽에 떠오른 고수의 움직임을 따라 리듬을 익히고, 곧 짧은 \n스파링으로 실전 감각을 깨웁니다. 부담 없이 완성한 첫 플레이는 또 다른 움직임을 시작해 보고 싶은 마음을 남깁니다.",
    "집에서 한 번 움직여본 감각은, 피드 속 러닝을 그냥 넘기지 못하게 만듭니다. 오늘의 Pack은 션과 함께 달리는 러닝메이트. NEWTON은 발밑에 페이스와 박자를 안내하고, 리듬이 꺼질 때는 Boost On으로 다음 한 발을 밀어줍니다. 피드에서 보던 러닝이 오늘 내 거리로 넘어오는 순간, 운동은 루틴이 아니라 따라가고 싶은 바깥 플레이가 됩니다.":
        "집에서 한 번 움직여 본 감각은 피드 속 러닝을 그냥 넘기지 못하게 만듭니다. 오늘은 션과 함께 달리는 러닝메이트 Pack을 골라 밖으로 나섭니다. 발밑에 이어지는 빛을 따라 페이스와 박자를 맞추고, 리듬이 흔들릴 때는 Boost On으로 다음 한 발에 힘을 더합니다. 피드에서 바라보던 \n러닝이 내 발밑에서 시작되는 순간, 익숙한 루틴은 따라가고 싶은 플레이가 됩니다.",
    "혼자 달리던 몸은 이제 함께 움직이는 재미를 궁금해합니다. 오늘의 Pack은 스테판 커리의 스텝백. NEWTON은 첫 발, 백스텝, 복귀 리듬을 지면 위에 띄우고, Press On은 발을 빼고 돌아오는 순간에 묵직한 저항을 더해 순발력을 깨웁니다. 혼자 익힌 리듬이 쌓이면, 보기만 하던 플레이는 해볼 수 있는 감각이 됩니다. 그 감각은 친구들과 함께 움직여볼 자신감으로 이어집니다.":
        "혼자 움직이던 시간은 이제 친구들과 함께하는 플레이를 떠올리게 합니다. 오늘의 Pack은 \n스테판 커리의 스텝백. Newton은 첫 발과 백스텝, 복귀 리듬을 지면 위에 띄우고, Press On은 돌아오는 순간 묵직한 저항을 더해 순발력을 깨웁니다. 혼자 익힌 리듬은 친구들과 코트에 나서 보고 싶은 마음을 키우고, 운동은 어느새 함께 빠져드는 스포츠가 됩니다.",
    "혼자 익힌 리듬은, 함께할 때 더 재밌어집니다. NEWTON의 빔프로젝터를 나란히 두는 순간, 거실은 둘만의 플레이 스테이지로 넓어집니다. 커진 투사면 안에서 서로의 움직임이 맞물리고, 운동은 게임처럼 가볍게 이어집니다. 혼자 쌓은 자신감은 친구와 주고받는 리듬이 되고, 연습은 함께 즐기는 플레이가 됩니다.":
        "혼자 익힌 리듬은 함께할 때 더 재밌어집니다. Newton의 Core를 나란히 두는 순간, 공간은 \n둘만의 플레이 스테이지로 넓어집니다. 커진 투사면 안에서 서로의 움직임이 맞물리고, 운동은 게임처럼 가볍게 이어집니다. 혼자 쌓은 자신감은 친구와 주고받는 리듬으로 번지고, 익숙한 \n연습에도 함께하는 재미가 더해집니다.",
    "{5} Dock and Remember\n오늘의 두근거림을,\n다음 도전으로":
        "(3) From Movement to Momentum\n오늘의 두근거림을\n다음 도전으로",
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
    "10 Verbal Branding", "11 Logo", "12 Color", "13 Type", "14 GUI", "15 Goods",
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

def split_h4(text):
    lines = text.split("\n")
    if lines and lines[0].strip()[:1] in ("{", "("):
        return lines[0].strip(), "\n".join(lines[1:]).strip()
    return "", text

def head_block(kicker, title, body, step=False, sub=""):
    """Figma 12:846 header: kicker (red) on top, then title-left(264px) / body-right(flex).
    `sub` (e.g. a credit line) sits under the title in the left column."""
    k = f'<p class="kicker"{en_attr(kicker)}>{esc(kicker)}</p>' if kicker else ""
    tt = "<br>".join(esc(l.strip()) for l in title.split("\n"))
    t = f'<h2 class="head-title"{en_attr(title)}>{tt}</h2>'
    if sub:
        t = f'<div class="head-titlecol">{t}<p class="head-credit">{esc(sub)}</p></div>'
    b = ""
    if body:
        bb = "<br>".join(linkify(esc(l)) for l in body.split("\n"))
        b = f'<p class="head-body"{en_attr(body)}>{bb}</p>'
    cls = "head-block step" if step else "head-block"
    return f'<div class="{cls}">{k}<div class="head-row">{t}{b}</div></div>'

def render_vertical_content(items):
    """each title(+its following paragraph) becomes the same header component."""
    out = []
    i = 0
    while i < len(items):
        n = items[i]
        t = n["t"]
        if t in ("H4", "H3"):
            kick, title = split_h4(n["x"])
            body = ""
            if i + 1 < len(items) and items[i + 1]["t"] == "P" and not is_citation(items[i + 1].get("x", "")):
                body = items[i + 1].get("x", "")
                i += 1
            out.append(head_block(kick, title, body, step=True))
            i += 1
            continue
        if t == "TOGGLE":
            tg = []
            while i < len(items) and items[i]["t"] == "TOGGLE":
                tg.append(render_node(items[i]))
                i += 1
            out.append(f'<div class="group">{"".join(tg)}</div>')
            continue
        out.append(render_node(n))
        i += 1
    return "".join(out)

def render_vertical(page_id, kicker, title_text, body_items, hero, scroll_hint=False, head_sub=""):
    """549/827: header component + content (each step reuses the same header), then big image."""
    first_p, rest = first_paragraph(body_items)
    first_body = first_p.get("x", "") if first_p else ""
    head = head_block(kicker, title_text, first_body, sub=head_sub)
    content_html = render_vertical_content(rest)
    hero_html = f'<figure class="page-hero">{img_tag(hero["src"])}</figure>' if hero else ""
    data = f' data-page="{page_id}"' if page_id else ""
    hint_html = ('<div class="scroll-hint" aria-hidden="true">'
                 '<span class="scroll-mouse"></span>'
                 '<span class="chevs"><i class="chev"></i><i class="chev"></i><i class="chev"></i></span>'
                 '</div>') if scroll_hint else ""
    return f'''
<div class="page"{data}>
  <div class="page-scroll">
    {head}
    <div class="page-content">{content_html}</div>
    {hero_html}
  </div>
  {hint_html}
</div>'''

# 피그마 "텍스트+이미지 크게쓰고싶을 때"(27:302) 레이아웃을 쓰는 페이지.
# 이미지가 2.6:1 가로형이라 좌우 2단이 아니라 텍스트 위 / 이미지 아래로 간다.
WIDE_PAGES = {"10", "11", "12", "13"}

KICKER_OVERRIDE = {"03": "For Those Who Turn Trends Into Play", "08": "(1) A Spark to Move"}

# 다중 이미지 페이지 → 데스크톱은 슬라이딩 캐러셀, 모바일은 16:9 합성 한 장.
# 피그마 "웹" 섹션의 프레임 이름이 그대로 페이지 번호이고, N-1/N-2 가 추가 컷이다.
# (섹션 번호, [이미지들], 모바일 합성본) — 첫 장은 그 섹션의 원래 히어로다.
CAROUSEL = {
    "02": (["fade1", "fade2", "fade3", "fade4"], "m3"),          # 피그마 3-1..3-4
    "05": (["img_18", "img_18-2", "img_18-3"], "m6"),            # 피그마 6, 6-1, 6-2
    "06": (["img_22", "img_22-2"], "m7"),                        # 피그마 7, 7-1  (스테이션)
    "07": (["img_23", "img_23-2"], "m8"),                        # 피그마 8, 8-1  (프로젝션 유닛)
    "12": (["bx_color", "bx_color_dark"], "bx_color"),           # 라이트/다크 컬러 시스템
}

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
        rest2 = apply_scenario_media(rest2, SCENARIO_MEDIA)
        return render_vertical(f"sec-{num}", kicker, h4["x"] if h4 else "", rest2, None, scroll_hint=True)
    # 가로형 이미지 페이지: 텍스트가 위, 이미지가 아래 전폭 (피그마 27:302)
    if num in WIDE_PAGES:
        hero, rest2 = extract_hero(rest)
        car = CAROUSEL.get(num)
        if car:
            names, _ = car
            seq = names + names[:1]
            slides = "".join(f'<img src="assets/{n}{EXT.get(n, ".png")}" alt="" loading="lazy">' for n in seq)
            media = f'<div class="fade-stack"><div class="fade-track" data-n="{len(seq)}">{slides}</div></div>'
        else:
            media = img_tag(hero["src"]) if hero else ""
        # 피그마 27:302 는 kicker 위, 타이틀 좌 / 본문 우다 — 기존 head_block 이 그 구조다
        # 본문 문단은 전부 타이틀 우측 칸(.head-body)에 넣는다. 첫 문단만 넣으면
        # 나머지가 .head-row 밖으로 빠져 타이틀 아래 전체 폭으로 흘러내린다.
        paras = [n for n in rest2 if n["t"] == "P"]
        rest3 = [n for n in rest2 if n["t"] != "P"]
        body_text = "\n".join(n.get("x", "") for n in paras if n.get("x"))
        head = head_block(kicker, h4['x'] if h4 else '', body_text)
        return f'''
<div class="page wide-page" data-page="sec-{num}">
  <div class="wide-text">{head}{render_children(rest3)}</div>
  <div class="wide-media">{media}</div>
</div>'''
    # everything else keeps the left-image / right-text two-column layout
    hero, rest = extract_hero(rest)
    car = CAROUSEL.get(num)
    if car:
        names, mobile = car
        seq = names + names[:1]   # last = first, for a seamless loop with no white gap
        # desktop: sliding carousel; mobile: single hi-res 16:9 composite
        slides = "".join(f'<img src="assets/{n}{EXT.get(n, ".png")}" alt="" loading="lazy">' for n in seq)
        media_html = (f'<div class="fade-stack"><div class="fade-track" data-n="{len(seq)}">{slides}</div></div>'
                      f'<img class="media m-only" src="assets/{mobile}.png" alt="" loading="lazy">')
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

# ---- 마지막 장: 목걸이(lanyard)에 매달린 크레딧 카드 ----
# 카드 앞/뒤 모두 CSS 로 그린다. 이미지로 구우면 확대·플립할 때 그라디언트에 밴딩이
# 생기고 사진 페이드 마스크가 깨진다. 사진만 넣고 나머지는 벡터로 둔다.
# roles/desc/socials 는 피그마가 아직 1번 카드 양식만 채워둬서 그 값을 따랐다.
# 역할 약어는 피그마 "인물원본+정보"(49:1927)의 이름 뒤 라벨 그대로다.
ROLE_NAME = {"PL": "Project Lead", "ID": "Industrial Design",
             "UX": "UX Design", "VD": "Video Direction"}
PEOPLE = [
    # 링크의 추적 파라미터(igsh, utm_source)는 떼고 넣는다
    {"ko": "송시헌", "en": "Siheon Song", "img": "person1", "roles": ["PL", "ID"],
     "desc": ["Product Design Lead", "3D Modeling", "3D Rendering",
              "Prototyping", "Mockup Engineering", "Film Directing"],
     "sns": {"instagram": "https://www.instagram.com/halcy_heon",
             "behance": "https://www.behance.net/halcyheon"}},
    {"ko": "이일여", "en": "Ilyeo Lee", "img": "person2", "roles": ["UX"],
     "desc": ["UX Research Strategy", "Mobile UX  Projection GUI",
              "Sports Simulator Development", "UX Process Book Development"],
     "sns": {"instagram": "https://www.instagram.com/leeilyeoo",
             "behance": "https://www.behance.net/leeilyeoo"}},
    {"ko": "김소진", "en": "SoJin Kim", "img": "person3", "roles": ["ID"],
     "sns": {"instagram": "https://www.instagram.com/o3_so_j",
             "behance": "https://www.behance.net/sojin_"}},
    {"ko": "박주원", "en": "Juwon Park", "img": "person4", "roles": ["ID"],
     "sns": {"instagram": "https://www.instagram.com/juparki_03"}},     # 비핸스 없음
    {"ko": "전다빈", "en": "Dabin Jeon", "img": "person5", "roles": ["VD"],
     "desc": ["Logo & Graphic Design", "Mobile GUI Design & Development",
              "Motion Graphics", "Goods & Poster Design"],
     "sns": {"instagram": "https://www.instagram.com/nadabiniii",
             "behance": "https://www.behance.net/davinjeon"}},
]

SNS_ICON = {
    "instagram": '<svg viewBox="0 0 24 24" aria-hidden="true"><use href="#ic-ig"></use></svg>',
    "behance": '<svg viewBox="0 0 24 24" aria-hidden="true"><use href="#ic-be"></use></svg>',
}

# 피그마 49:2014 pc_credit_tutor 실측. 라벨 / 역할 / 이름(한·영) 3열이다.
# 피그마 61:388 "추가되는레이아웃" 그대로. 한 덩어리("thanks to") 아래 4열이고,
# 각 열은 [역할 라벨 | 이름들] 컴포넌트를 세로로 쌓는다. 2열만 컴포넌트가 둘이다.
CREDIT_COLS = [
    [("Advisory\nProfessor", [("심유리", "Yuri Sim"), ("이문환", "Moonhwan Lee")])],
    [("ID Tutor", [("주호영", "Hoyoung Joo")]),
     ("ID tutor", [("정수헌", "Soohun Jung")])],
    [("VD Tutor", [("워크스", "WORKS")])],
    [("Videographer", [("양의열", "Euiyeol Yang"), ("조수완", "Cho Suwan"),
                       ("이문환", "Moonhwan Lee")])],
]

def credit_rows():
    cols = ""
    for groups in CREDIT_COLS:
        blocks = ""
        for role, names in groups:
            people = "".join(
                f'<div class="cr-name"><span class="cr-ko">{esc(ko)}</span>'
                f'<span class="cr-en">{esc(en)}</span></div>'
                for ko, en in names)
            role_html = esc(role).replace("\n", "<br>")
            blocks += (f'<div class="cr-item"><p class="cr-role">{role_html}</p>'
                       f'<div class="cr-names">{people}</div></div>')
        cols += f'<div class="cr-col">{blocks}</div>'
    return f'<p class="cr-label">thanks to</p><div class="cr-cols">{cols}</div>'

# ---- 아카이빙 페이지 (피그마 71:1270 소재 / 68:1116 템플릿) ----
# 묶음 순서와 장수는 피그마 읽는 순서(위→아래, 왼→오른) 그대로다.
ARCHIVE = [
    ("아이디에이션",       "Ideation",      2),
    ("인스퍼",             "Inspiration",   7),
    ("스케일 체크",        "Scale Check",   9),
    ("목업",               "Mockup",        9),
    ("비주얼 / 폼 스터디",  "Visual / Form", 8),
    ("촬영",               "Shooting",      7),
]

def archive_page():
    items, n = "", 0
    for ko, en, cnt in ARCHIVE:
        for _ in range(cnt):
            n += 1
            items += ('<figure class="ar-item" data-ko="%s" data-en="%s">'
                      '<img src="assets/arch%02d.webp" alt="" loading="lazy" draggable="false">'
                      '</figure>') % (esc(ko), esc(en), n)
    return ('\n<div class="page archive-page" data-page="archive">\n'
            '  <div class="ar-stage" id="arStage"><div class="ar-track">' + items + '</div></div>\n'
            '  <div class="ar-foot">\n'
            '    <p class="ar-title">Ideation</p>\n'   # 아카이빙 제목은 언제나 영문
            '    <p class="ar-count"><span class="ar-cur">1</span>/' + str(n) + '</p>\n'
            '  </div>\n'
            '</div>')

def credits_page():
    cards = ""
    for i, p in enumerate(PEOPLE):
        chips = "".join(f'<span class="cc-chip">{esc(r)}</span>' for r in p["roles"])
        first, _, last = p["en"].partition(" ")
        # 사람별 문구가 있으면 그대로, 없으면 역할 약어를 풀어 쓴다
        if p.get("desc"):
            desc = "".join(f'<span>{esc(l)}</span>' for l in p["desc"])
        else:
            desc = ",<br>".join(esc(ROLE_NAME.get(r, r)) for r in p["roles"]) + "."
        links = ""
        for kind, url in p["sns"].items():
            tag, attrs = ("a", f' href="{url}" target="_blank" rel="noopener"') if url else ("span", "")
            links += f'<{tag} class="cc-sns"{attrs} aria-label="{kind}">{SNS_ICON[kind]}</{tag}>'
        cards += f'''
      <div class="lany" data-i="{i}">
        <svg class="lany-rope" aria-hidden="true">
          <defs>
            <linearGradient id="bg{i}" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="0">
              <stop offset="0"    stop-color="#D42020"/>
              <stop offset="0.18" stop-color="#FA3030"/>
              <stop offset="0.82" stop-color="#FA3030"/>
              <stop offset="1"    stop-color="#D42020"/>
            </linearGradient>
            <!-- 크림프(집게)의 금속면. objectBoundingBox 라 버클이 돌아가도 같이 돈다.
                 가로로 어둡게-밝게-어둡게 가야 평면이 아니라 둥근 쇠로 읽힌다. -->
            <linearGradient id="mt{i}" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0"    stop-color="#191D22"/>
              <stop offset="0.16" stop-color="#5F6B76"/>
              <stop offset="0.34" stop-color="#B6C0C8"/>
              <stop offset="0.48" stop-color="#828D97"/>
              <stop offset="0.72" stop-color="#3D454C"/>
              <stop offset="1"    stop-color="#14181C"/>
            </linearGradient>
          </defs>
          <path class="rp-ribbon" fill="url(#bg{i})"/>
          <g class="rp-logos"></g>
          <g class="rp-hw">
            <rect class="rp-buckle" rx="2" fill="url(#mt{i})"/>
            <rect class="rp-bhl"/>
            <rect class="rp-bcrease"/>
          </g>
        </svg>
        <div class="cc" tabindex="0" role="button" aria-label="{esc(p["en"])} 카드">
          <div class="cc-inner">
            <div class="cc-face cc-front">
              <img class="cc-photo" src="assets/{p["img"]}.png" alt="{esc(p["en"])}" loading="lazy" draggable="false">
              <div class="cc-blob"></div>
              <div class="cc-name"><span class="n1">{esc(first)}</span><span class="n2">{esc(last)}</span></div>
              <div class="cc-chips">{chips}</div>
            </div>
            <div class="cc-face cc-back">
              <div class="cc-blob"></div>
              <div class="cc-chips cc-chips-top">{chips}</div>
              <p class="cc-desc">{desc}</p>
              <div class="cc-links">{links}</div>
              <p class="cc-sig">{esc(p["en"])}</p>
            </div>
          </div>
        </div>
      </div>'''
    return f'''
<div class="page credits-page" data-page="credits">
  <div class="cc-dim"></div>
  <div class="lany-stage" id="lanyStage">{cards}
  </div>
  <p class="cc-kicker">DESIGNED BY</p>
  <div class="credits-foot">
    <div class="cr-wrap">{credit_rows()}</div>
  </div>
  <button class="lb-close cc-close" type="button" aria-label="닫기">
    <svg viewBox="0 0 24 24" fill="none"><path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
  </button>
</div>'''

# 탭의 첫 장으로 들어가는 전면 영상 페이지 (피그마 "이미지 큰비율로 넣고플때" 레이아웃).
# 텍스트 없이 영상이 페이지를 꽉 채운다. 재생/사운드 조작은 본문 영상과 같다.
def lead_page(page_id, src):
    return f'''
<div class="page lead-page" data-page="{page_id}">
  {video_tag(src, wrap="v-figure")}
</div>'''

# 내용상 프로젝션 유닛이 스테이션보다 먼저 온다. structure_full 의 문서 순서는 건드리지
# 않는다 — 위쪽 구간 슬라이싱이 마커의 문서 위치에 의존하므로, 출력 순서만 바꾼다.
PAGE_ORDER = [
    "01 From Routine to Challenge", "02 Challenge Spark", "03 Target", "04 Solution",
    "05 Wearable Robotics", "07 Projection Unit", "06 Station",
    "08 Scenario", "09 Extensibility",
    "10 Verbal Branding", "11 Logo", "12 Color", "13 Type", "14 GUI", "15 Goods",
]
assert sorted(PAGE_ORDER) == sorted(MARKERS), "PAGE_ORDER 가 MARKERS 를 그대로 담고 있지 않다"
FIRST_PRODUCT = "05 Wearable Robotics"
LAST_PRODUCT = "06 Station"   # "Play with Newton!" 은 Products 마지막 페이지 뒤에 들어간다

seg_of = dict(sections)
pages_out = []
for m in PAGE_ORDER:
    if m == FIRST_PRODUCT:
        pages_out.append(lead_page("products-lead", "lead_products.mp4"))
    pages_out.append(render_page(m, seg_of[m]))
    if m == LAST_PRODUCT:
        pages_out.append(lead_page("scenario-lead", "lead_scenario.mp4"))
        pages_out.append(playwith_page)
pages_out.append(archive_page())      # 인물 소개 앞
pages_out.append(credits_page())      # 마지막 장
sections_html = "".join(pages_out)

# intro page (827 layout): kicker "Now, your turn!", big title "NEWTON"
intro_hero, intro_rest = extract_hero(hero_items)
intro_body = [n for n in intro_rest if n.get("x") != "Now, your turn!"]
# credit sits under the NEWTON title (left column) instead of its own row below the header,
# so the header stays compact and the hero image grows upward (face visible)
intro_page_html = render_vertical("intro", "Now, Your Turn!",
                                  "NEWTON", intro_body, intro_hero,
                                  head_sub="송시헌, 이일여, 김소진, 박주원, 전다빈")

# label, first page, member pages
NAV_GROUPS = [
    ("Background", "sec-01", ["sec-01", "sec-02", "sec-03"]),
    ("Solution", "sec-04", ["sec-04"]),
    # 탭을 누르면 전면 영상부터 나온다 → target 이 lead 페이지다
    ("Products", "products-lead", ["products-lead", "sec-05", "sec-07", "sec-06"]),
    ("Scenario", "scenario-lead", ["scenario-lead", "playwith", "sec-08"]),
    ("Extensibility", "sec-09", ["sec-09"]),
    ("Branding", "sec-10", ["sec-10", "sec-11", "sec-12", "sec-13", "sec-14", "sec-15"]),
]
nav_html = "".join(
    f'<button type="button" class="pill" data-target="{target}" data-members="{",".join(members)}">{esc(label)}</button>'
    for label, target, members in NAV_GROUPS
)

TEMPLATE = open(os.path.join(ROOT, "template.html"), encoding="utf-8").read()
out = (TEMPLATE.replace("{{NAV}}", nav_html)
       .replace("{{INTRO_PAGE}}", intro_page_html)
       .replace("{{SECTIONS}}", sections_html)
       .replace("{{APPENDIX}}", ""))
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8", newline="\n").write(out)
print("done", len(sections_html), len(intro_page_html))
if _missing:
    miss_path = os.path.join(ROOT, "missing.json")
    with open(miss_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(sorted(_missing, key=len), f, ensure_ascii=False, indent=0)
    print(f"[i18n] 미번역 {len(_missing)}개 → {miss_path}")
