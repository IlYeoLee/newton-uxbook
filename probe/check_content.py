# 이번 변경으로 책에서 글이나 그림이 사라졌는지 본다.
#
#     python probe/check_content.py [기준]        기준 없으면 HEAD
#
# 원본(structure_full.json)과 견주지 않는 이유: 빌드가 TEXT_PATCHES 로 문장을
# 갈아끼우고 표지·부록 같은 건 일부러 버린다. 그래서 "원본에 있는데 없다"는
# 대부분 정상이라 경보로 쓸 수가 없다. 대신 방금 전 index.html 과 견준다 —
# 이러면 내가 이번에 흘린 것만 걸린다.
import html as ihtml
import os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def visible(html):
    """눈에 보이는 글만 남긴다. script/style 은 통째로 버린다."""
    html = re.sub(r'(?is)<(script|style)\b.*?</\1>', ' ', html)
    text = ihtml.unescape(re.sub(r'<[^>]+>', '\n', html))
    # 문장 단위로 자르고 공백을 눌러 붙인다(줄바꿈이 <br> 로 바뀌는 것 흡수)
    return {re.sub(r'\s+', '', ln) for ln in text.split('\n') if len(re.sub(r'\s+', '', ln)) >= 8}


def assets(html):
    return set(re.findall(r'assets/[\w./-]+\.(?:png|jpg|jpeg|webp|mp4|svg|glb)', html))


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else 'HEAD'
    old = subprocess.run(['git', 'show', f'{base}:index.html'], cwd=ROOT,
                         capture_output=True).stdout.decode('utf-8')
    new = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()

    lost_text = sorted(visible(old) - visible(new))
    lost_asset = sorted(assets(old) - assets(new))

    if not lost_text and not lost_asset:
        print(f'ok — {base} 에 있던 글과 그림이 전부 남아 있다')
        return 0

    report = []
    if lost_text:
        report.append(f'사라진 글 {len(lost_text)}개')
        report += ['  x ' + t[:120] for t in lost_text]
    if lost_asset:
        report.append(f'사라진 파일 {len(lost_asset)}개')
        report += ['  x ' + a for a in lost_asset]
    text = '\n'.join(report)
    open(os.path.join(ROOT, 'probe', 'lost.txt'), 'w', encoding='utf-8').write(text)
    print(text[:3000])
    return 1


if __name__ == '__main__':
    sys.exit(main())
