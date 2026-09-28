#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Techทันใจ poster — หยิบ 1 repo จาก data/repos.json มาทำการ์ด + แคปชัน แล้วโพสต์ลงเพจ FB

ทำไมต้อง HTML+Chrome สำหรับการ์ด: ข้อความไทยต้องอาศัย text shaping ของเบราว์เซอร์
(PIL/ImageDraw วางสระและวรรณยุกต์ผิดตำแหน่ง) — ดู make_card.py

วิธีใช้
  python scripts/daily_post.py --dry-run            # ทำการ์ด+แคปชัน โชว์เฉย ๆ ไม่โพสต์
  python scripts/daily_post.py --now                # โพสต์ทันที
  python scripts/daily_post.py --at 20:00           # ตั้งเวลาโพสต์ (FB native scheduling)
  python scripts/daily_post.py --repo owner/name    # บังคับ repo
  python scripts/daily_post.py --reset              # ล้างประวัติที่โพสต์แล้ว (เริ่มรอบใหม่)

สถานะการโพสต์เก็บที่ data/posted.json — กันโพสต์ซ้ำ
"""
import argparse
import json
import mimetypes
import os
import random
import sys
import time
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPOS_JSON = os.path.join(ROOT, "data", "repos.json")
POSTED_JSON = os.path.join(ROOT, "data", "posted.json")
RENDERS = os.path.join(ROOT, "renders")
SCRIPTS = os.path.join(ROOT, "scripts")

ICT = timezone(timedelta(hours=7))
GRAPH = "https://graph.facebook.com/v21.0"
TOKEN = os.environ.get("FB_PAGE_TOKEN", "")

MIN_STARS = 300          # ข้าม repo เงียบ ๆ ที่ไม่น่าสนใจ
MAX_STARS_UNVERIFIED = 100000   # ดาวสูงเกินจริง (ไม่ได้อยู่ในลิสต์คัดมือ) = ข้าม กันข้อมูลเพี้ยน
LOOKBACK_DAYS = 45       # ให้ความสำคัญกับ repo ที่เพิ่งอัปเดตภายในกี่วัน

CAT_HASHTAG = {
    "ai": "#AI #MachineLearning #AIไทย",
    "automation": "#Automation #Automate #งานอัตโนมัติ",
    "tool": "#DevTools #Productivity #เครื่องมือนักพัฒนา",
    "trading": "#Trading #บอทเทรด #การเงิน",
}

# หน้าเว็บของเรา (RepoHunter) — ส่งท้าย CTA ทุกโพสต์
SITE_URL = "https://smartnfe.github.io/repohunter/"

# เปิดโพสต์ด้วย "ปัญหา" ตามหมวด แล้วโยงไปทางออก — แนวการตลาด
# (FB ลด reach โพสต์ที่มีลิงก์ในแคปชัน + ลิงก์ในแคปชันโพสต์รูปคลิกไม่ได้
#  → URL จริงลงคอมเมนต์แรกแทน ดู post_comment())
CAT_HOOK = {
    "ai": "เบื่อทำงานซ้ำ ๆ ซ้ำซากทุกวันไหม?",
    "automation": "งานเดิม ๆ ที่ต้องรันมือทุกวัน — ปล่อยให้มันทำงานแทนเราดีไหม?",
    "trading": "เทรดยังเดา ๆ ตามอารมณ์อยู่หรือเปล่า?",
    "tool": "รู้สึกทำงานช้า ติดขัดกับเครื่องมือเดิม ๆ อยู่ใช่ไหม?",
}

sys.path.insert(0, SCRIPTS)
from make_card import CAT_LABEL, render_card  # noqa: E402


# ---------------------------------------------------------------- utilities
def log(msg):
    print(msg, flush=True)


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def parse_iso(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def th_date(dt):
    months = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
              "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
    return "%d %s %d" % (dt.day, months[dt.month - 1], dt.year + 543)


def th_num(n):
    return "{:,}".format(int(n))


# ---------------------------------------------------------------- config
def load_fb_config():
    """หา page_id/token: env > config/fb-config.json > โปรเจกต์เดิม"""
    candidates = [
        os.path.join(ROOT, "config", "fb-config.json"),
        "E:/AI-Projects/hyperframes/techtanjai-reel/references/fb-config.json",
    ]
    cfg = {}
    for p in candidates:
        if os.path.exists(p):
            cfg = load_json(p, {})
            break
    page_id = os.environ.get("FB_PAGE_ID") or cfg.get("page_id")
    token = TOKEN or cfg.get("access_token") or cfg.get("page_access_token")
    return page_id, token, cfg.get("page_name", "Techทันใจ")


# ---------------------------------------------------------------- selection
def pick_repo(repos, posted, force=None):
    if force:
        for r in repos:
            if r.get("full_name", "").lower() == force.lower():
                return r
        raise SystemExit("ไม่พบ repo: %s" % force)

    done = set(posted.get("posted_full_names", []))
    now = datetime.now(timezone.utc)
    fresh_cut = now - timedelta(days=LOOKBACK_DAYS)

    cands = []
    for r in repos:
        name = r.get("full_name")
        if not name or name in done:
            continue
        stars = r.get("stargazers_count") or 0
        if stars < MIN_STARS:
            continue
        if stars > MAX_STARS_UNVERIFIED and not r.get("curated"):
            continue
        if not (r.get("description_th") or "").strip():
            continue
        cands.append(r)

    if not cands:
        return None

    # กลุ่ม "สดใหม่" มาก่อน (เพิ่ง push ภายใน LOOKBACK_DAYS) แล้วเรียงดาวมาก→น้อย
    fresh = [r for r in cands if (parse_iso(r.get("pushed_at")) or datetime(1970, 1, 1, tzinfo=timezone.utc)) >= fresh_cut]
    pool = fresh or cands
    pool.sort(key=lambda r: (1 if r.get("curated") else 0,
                             r.get("stargazers_count") or 0), reverse=True)
    return pool[0]


# ---------------------------------------------------------------- caption
def build_caption(repo, url):
    name = repo.get("full_name", "")
    cat = repo.get("category") or "tool"
    key = str(cat).lower()
    stars = repo.get("stargazers_count") or 0
    forks = repo.get("forks_count") or 0
    lang = repo.get("language") or "ไม่ระบุ"
    desc_th = (repo.get("description_th") or "").strip()
    desc_en = (repo.get("description") or "").strip()
    pushed = parse_iso(repo.get("pushed_at"))
    topics = [t for t in (repo.get("topics") or []) if t][:5]

    lines = []
    lines.append(CAT_HOOK.get(key, "หาของดี ๆ มาใช้เพิ่มประสิทธิภาพการทำงานอยู่หรือเปล่า?"))
    lines.append("")
    if desc_th and desc_en and desc_en.lower() not in desc_th.lower():
        lines.append("%s — %s" % (desc_th, desc_en))
    else:
        lines.append(desc_th or desc_en)
    lines.append("")
    lines.append("📦 %s" % name)
    lines.append("⭐ %s ดาว  •  🍴 %s ฟอร์ก  •  💻 %s" % (th_num(stars), th_num(forks), lang))
    if pushed:
        lines.append("🕒 อัปเดตล่าสุด %s" % th_date(pushed.astimezone(ICT)))
    if topics:
        lines.append("🏷 " + " · ".join("#" + t.replace("-", "") for t in topics))
    lines.append("")
    lines.append("มีอีก 100+ โปรเจกต์จัดหมวดพร้อมใช้ — ตามไปดูที่เว็บเราได้เลยครับ")
    lines.append("🔗 ลิงก์อยู่ในคอมเมนต์แรก")
    lines.append("")
    lines.append("📌 หมวด %s %s" % (CAT_LABEL.get(key, key.upper()), CAT_HASHTAG.get(key, "")))
    lines.append("#Techทันใจ #GitHub #OpenSource #นักพัฒนา #เทคโนโลยี #โปรแกรมเมอร์")
    return "\n".join(lines).strip()


# ---------------------------------------------------------------- facebook
def _multipart(fields, files):
    boundary = "----HermesBoundary" + uuid.uuid4().hex
    body = b""
    for k, v in fields.items():
        body += ("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n"
                 % (boundary, k, v)).encode("utf-8")
    for k, (fname, data, ctype) in files.items():
        body += ("--%s\r\nContent-Disposition: form-data; name=\"%s\"; filename=\"%s\"\r\n"
                 "Content-Type: %s\r\n\r\n" % (boundary, k, fname, ctype)).encode("utf-8")
        body += data + b"\r\n"
    body += ("--%s--\r\n" % boundary).encode("utf-8")
    return body, "multipart/form-data; boundary=%s" % boundary


def post_photo(page_id, token, image_path, caption, scheduled_ts=None):
    with open(image_path, "rb") as f:
        data = f.read()
    ctype = mimetypes.guess_type(image_path)[0] or "image/png"
    fields = {"message": caption, "access_token": token}
    if scheduled_ts:
        fields["published"] = "false"
        fields["scheduled_publish_time"] = str(int(scheduled_ts))
    else:
        fields["published"] = "true"

    body, ctype_hdr = _multipart(fields, {"source": (os.path.basename(image_path), data, ctype)})
    req = urllib.request.Request("%s/%s/photos" % (GRAPH, page_id), data=body,
                                 headers={"Content-Type": ctype_hdr}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", "replace")
        raise SystemExit("FB API error %s: %s" % (e.code, err))


def post_comment(post_id, token, message):
    """POST /{post_id}/comments — ใส่ลิงก์ในคอมเมนต์แรก (คลิกได้, ไม่โดนลด reach)
    ใช้ form-urlencoded utf-8 — ปลอดภัยกับข้อความไทย"""
    data = urllib.parse.urlencode({"message": message, "access_token": token}).encode("utf-8")
    req = urllib.request.Request("%s/%s/comments" % (GRAPH, post_id), data=data,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode("utf-8", "replace")}


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="ไม่โพสต์ แค่สร้างการ์ด+แคปชัน")
    ap.add_argument("--now", action="store_true", help="โพสต์ทันที")
    ap.add_argument("--at", default="20:00", help="เวลาโพสต์ ICT (default 20:00)")
    ap.add_argument("--repo", help="บังคับ repo owner/name")
    ap.add_argument("--reset", action="store_true", help="ล้างประวัติการโพสต์")
    args = ap.parse_args()

    if args.reset:
        save_json(POSTED_JSON, {"posted": [], "posted_full_names": []})
        log("🧹 ล้างประวัติการโพสต์แล้ว")
        return

    data = load_json(REPOS_JSON, {})
    repos = data.get("repos", [])
    if not repos:
        raise SystemExit("ไม่พบข้อมูล repo ใน %s" % REPOS_JSON)

    posted = load_json(POSTED_JSON, {"posted": [], "posted_full_names": []})
    posted.setdefault("posted", [])
    posted.setdefault("posted_full_names", [])

    repo = pick_repo(repos, posted, args.repo)
    if not repo:
        log("✅ โพสต์ครบทุก repo ที่มีในคลังแล้ว — ไม่มีอะไรใหม่ให้โพสต์วันนี้")
        return

    name = repo.get("full_name")
    url = repo.get("html_url") or ("https://github.com/" + name)
    slug = name.replace("/", "-").lower()
    today = datetime.now(ICT).strftime("%Y-%m-%d")
    card_path = os.path.join(RENDERS, "%s-%s.png" % (today, slug))

    log("🎯 เลือก: %s (%s ดาว)" % (name, th_num(repo.get("stargazers_count") or 0)))
    render_card(repo, card_path)
    log("🖼  การ์ด: %s (%s bytes)" % (card_path, os.path.getsize(card_path)))

    caption = build_caption(repo, url)
    log("─" * 46)
    log(caption)
    log("─" * 46)

    if args.dry_run:
        log("🧪 dry-run — ไม่โพสต์")
        return

    page_id, token, page_name = load_fb_config()
    if not page_id or not token:
        raise SystemExit("ไม่พบ page_id/access_token (ตั้งใน config/fb-config.json หรือ env FB_PAGE_ID/FB_PAGE_TOKEN)")

    scheduled_ts = None
    if not args.now:
        hh, mm = [int(x) for x in args.at.split(":")]
        target = datetime.now(ICT).replace(hour=hh, minute=mm, second=0, microsecond=0)
        if target <= datetime.now(ICT) + timedelta(minutes=10):
            target += timedelta(days=1)
        scheduled_ts = target.timestamp()
        log("⏰ ตั้งเวลาโพสต์: %s ICT" % target.strftime("%Y-%m-%d %H:%M"))

    res = post_photo(page_id, token, card_path, caption, scheduled_ts)
    post_id = res.get("post_id") or res.get("id")
    log("✅ โพสต์ขึ้นเพจ %s แล้ว — post_id=%s" % (page_name, post_id))

    link_comment_id = None
    if post_id:
        repo_link = SITE_URL + "?q=" + urllib.parse.quote(name.split("/")[-1].lower())
        cmt = post_comment(post_id, token,
                           "🔗 ดู repo นี้ + อีก 100+ โปรเจกต์จัดหมวดไว้แล้วที่เว็บเรา: %s" % repo_link)
        if cmt.get("id"):
            link_comment_id = cmt["id"]
            log("💬 คอมเมนต์ลิงก์หน้าเว็บแล้ว — comment_id=%s" % link_comment_id)
        else:
            log("⚠️ คอมเมนต์ลิงก์ไม่สำเร็จ: %s" % json.dumps(cmt, ensure_ascii=False)[:200])

    posted["posted"].append({
        "full_name": name,
        "slug": slug,
        "date": today,
        "card": os.path.relpath(card_path, ROOT).replace("\\", "/"),
        "post_id": post_id,
        "link_comment_id": link_comment_id,
        "scheduled_for": datetime.fromtimestamp(scheduled_ts, ICT).isoformat() if scheduled_ts else "now",
    })
    posted["posted_full_names"].append(name)
    save_json(POSTED_JSON, posted)
    log("📝 เหลือ repo ในคลัง %d รายการ" % (len(repos) - len(posted["posted_full_names"])))


if __name__ == "__main__":
    main()
