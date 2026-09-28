# -*- coding: utf-8 -*-
"""
สร้างการ์ดภาพ 1080x1080 จากข้อมูล repo — HTML + headless Chrome

ทำไมใช้ HTML ไม่ใช้ PIL: ข้อความไทยต้องพึ่ง shaping ของเบราว์เซอร์
PIL/ImageDraw วางสระและวรรณยุกต์ไทยผิดตำแหน่ง

usage:
    python make_card.py <full_name> [out.png]
    python make_card.py --index 3 out.png
"""
import base64
import html
import io
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(ROOT, 'assets', 'fonts', 'NotoSansThai.ttf')
DATA = os.path.join(ROOT, 'data', 'repos.json')

CHROME_CANDIDATES = [
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    '/usr/bin/google-chrome',
    '/usr/bin/google-chrome-stable',
    '/usr/bin/chromium-browser',
    '/usr/bin/chromium',
]

CAT_LABEL = {
    'ai': 'AI',
    'automation': 'AUTOMATION',
    'trading': 'TRADING',
    'tool': 'TOOLS',
    'tools': 'TOOLS',
}


def find_chrome():
    for p in CHROME_CANDIDATES:
        if os.path.exists(p):
            return p
    for name in ('google-chrome', 'chromium', 'chromium-browser', 'chrome'):
        for d in os.environ.get('PATH', '').split(os.pathsep):
            cand = os.path.join(d, name)
            if os.path.exists(cand):
                return cand
    raise RuntimeError('ไม่พบ Chrome/Chromium สำหรับ render การ์ด')


def font_face_css():
    with open(FONT, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('ascii')
    return ("@font-face{font-family:'NotoThai';font-style:normal;"
            "font-weight:100 900;font-display:block;"
            "src:url(data:font/ttf;base64,%s) format('truetype');}" % b64)


def esc(s):
    return html.escape(str(s if s is not None else ''), quote=True)


def fmt(n):
    return '{:,}'.format(n or 0)


def th_date(iso):
    """2026-09-28T... -> 28 ก.ย. 2026"""
    months = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
              'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.']
    if not iso or len(iso) < 10:
        return '-'
    try:
        y, m, d = iso[:10].split('-')
        return '%s %s %s' % (int(d), months[int(m) - 1], int(y) + 543)
    except Exception:
        return iso[:10]


def build_html(repo, size=1080):
    name = repo.get('full_name', '')
    owner, _, short = name.partition('/')
    desc_th = repo.get('description_th') or repo.get('description') or ''
    desc_en = repo.get('description') or ''
    show_en = desc_en and desc_en != desc_th
    cat = CAT_LABEL.get(repo.get('category', ''), 'TOOLS')
    stars = fmt(repo.get('stargazers_count'))
    forks = fmt(repo.get('forks_count'))
    lang = repo.get('language') or '-'
    updated = th_date(repo.get('pushed_at'))
    url = repo.get('html_url') or ('https://github.com/' + name)

    return """<!DOCTYPE html>
<html lang="th"><head><meta charset="utf-8">
<style>
%(font)s
*{margin:0;padding:0;box-sizing:border-box;}
html,body{width:%(size)dpx;height:%(size)dpx;}
body{
  font-family:'NotoThai','Leelawadee UI','Tahoma',sans-serif;
  background:#0e1a15;
  color:#eef4ee;
  overflow:hidden;
}
.card{
  position:relative;width:%(size)dpx;height:%(size)dpx;
  padding:64px 68px 62px;
  display:flex;flex-direction:column;
  background:
    radial-gradient(circle at 88%% 6%%, rgba(217,154,28,.20) 0%%, transparent 42%%),
    radial-gradient(circle at 4%% 96%%, rgba(47,93,138,.28) 0%%, transparent 46%%),
    linear-gradient(158deg,#12271f 0%%,#0e1a15 55%%,#0b1411 100%%);
}
.card:before{
  content:'';position:absolute;inset:0;
  background:repeating-linear-gradient(115deg,rgba(255,255,255,.028) 0 2px,transparent 2px 26px);
}
.top{display:flex;align-items:center;justify-content:space-between;position:relative;}
.badge{
  display:inline-flex;align-items:center;gap:12px;
  padding:11px 24px;border-radius:999px;
  background:rgba(217,154,28,.16);border:2px solid rgba(217,154,28,.55);
  color:#f0c46a;font-size:27px;font-weight:600;letter-spacing:.02em;
}
.dot{width:12px;height:12px;border-radius:50%%;background:#d99a1c;}
.date{font-size:26px;color:#a2b9ac;}
.mid{flex:1;display:flex;flex-direction:column;justify-content:center;position:relative;padding:26px 0;}
.owner{font-size:29px;color:#93b0a1;letter-spacing:.03em;margin-bottom:6px;}
.repo{font-size:70px;font-weight:800;line-height:1.12;color:#fff;
  word-break:break-word;letter-spacing:-.01em;}
.rule{width:118px;height:7px;border-radius:4px;background:#d99a1c;margin:30px 0 28px;}
.desc{font-size:37px;line-height:1.62;color:#dce9e0;font-weight:500;}
.desc-en{font-size:25px;line-height:1.55;color:#94ac9f;margin-top:20px;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}
.stats{display:flex;gap:52px;position:relative;padding-top:30px;
  border-top:2px solid rgba(255,255,255,.10);}
.stat{display:flex;flex-direction:column;gap:5px;}
.stat b{font-size:44px;font-weight:800;color:#f0c46a;line-height:1.15;}
.stat span{font-size:24px;color:#a2b9ac;}
.foot{display:flex;align-items:flex-end;justify-content:space-between;
  margin-top:38px;position:relative;}
.cat{font-size:25px;font-weight:700;letter-spacing:.14em;color:#8fb9a4;
  border:2px solid rgba(143,185,164,.42);border-radius:8px;padding:9px 18px;}
.brand{text-align:right;}
.brand .page{font-size:42px;font-weight:800;color:#fff;white-space:nowrap;}
.brand .page i{font-style:normal;color:#d99a1c;}
.brand .url{font-size:25px;color:#93b0a1;margin-top:5px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:660px;}
</style></head>
<body>
<div class="card">
  <div class="top">
    <div class="badge"><span class="dot"></span>Repo น่าใช้</div>
    <div class="date">อัปเดต %(updated)s</div>
  </div>

  <div class="mid">
    <div class="owner">%(owner)s /</div>
    <div class="repo">%(short)s</div>
    <div class="rule"></div>
    <div class="desc">%(desc_th)s</div>
    %(desc_en_html)s
  </div>

  <div class="stats">
    <div class="stat"><b>%(stars)s</b><span>ดาว</span></div>
    <div class="stat"><b>%(forks)s</b><span>ฟอร์ก</span></div>
    <div class="stat"><b>%(lang)s</b><span>ภาษา</span></div>
  </div>

  <div class="foot">
    <div class="cat">%(cat)s</div>
    <div class="brand">
      <div class="page">Tech<i>ทันใจ</i></div>
      <div class="url">github.com/%(name)s</div>
    </div>
  </div>
</div>
</body></html>""" % {
        'font': font_face_css(),
        'size': size,
        'owner': esc(owner),
        'short': esc(short),
        'desc_th': esc(desc_th),
        'desc_en_html': ('<div class="desc-en">%s</div>' % esc(desc_en)) if show_en else '',
        'stars': esc(stars),
        'forks': esc(forks),
        'lang': esc(lang),
        'cat': esc(cat),
        'updated': esc(updated),
        'name': esc(name),
    }


def render_card(repo, out_png, size=1080, keep_html=False):
    chrome = find_chrome()
    out_png = os.path.abspath(out_png)
    html_path = os.path.splitext(out_png)[0] + '.html'
    with io.open(html_path, 'w', encoding='utf-8') as f:
        f.write(build_html(repo, size))

    uri = 'file:///' + html_path.replace('\\', '/')
    cmd = [
        chrome, '--headless=new', '--disable-gpu', '--hide-scrollbars',
        '--force-device-scale-factor=1', '--no-sandbox',
        '--window-size=%d,%d' % (size, size),
        '--screenshot=' + out_png, uri,
    ]
    r = subprocess.run(cmd, capture_output=True, timeout=180)
    if not os.path.exists(out_png):
        raise RuntimeError('render ล้มเหลว: %s\n%s' % (
            r.returncode, (r.stderr or b'').decode('utf-8', 'replace')[-600:]))
    if not keep_html:
        try:
            os.remove(html_path)
        except OSError:
            pass
    return out_png


def load_repo(selector):
    with io.open(DATA, encoding='utf-8') as f:
        repos = json.load(f)['repos']
    if selector.startswith('--index'):
        return repos[int(selector.split()[1] if ' ' in selector else 0)]
    for r in repos:
        if r['full_name'] == selector:
            return r
    raise SystemExit('ไม่พบ repo: %s' % selector)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'renders', 'card.png')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    repo = load_repo(sys.argv[1])
    p = render_card(repo, out)
    print('OK %s (%d bytes)' % (p, os.path.getsize(p)))
