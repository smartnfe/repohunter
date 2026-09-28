# -*- coding: utf-8 -*-
"""
RepoHunter fetcher
------------------
รวม 2 แหล่ง:
  1. data/curated.json  -> repo ที่คัดมือไว้ (จาก LINE memo) ต้องอยู่ครบเสมอ
  2. GitHub Search API  -> repo ใหม่ที่ดึงอัตโนมัติ

คำอธิบายไทย (description_th) ของ repo เดิมจะถูกคงไว้ ไม่ให้หายเมื่อรันซ้ำ
"""
import json
import os
import shutil
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

from th_translate import translate_th

# anchor กับ root ของ repo — รันจาก cwd ไหนก็ได้
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'repos.json')
CURATED = os.path.join(ROOT, 'data', 'curated.json')

# ดึงทีละ topic (GitHub legacy search ไม่รองรับวงเล็บ OR — คืน 0 เงียบ ๆ)
WINDOW_DAYS = 120
PER_PAGE = 20
MAX_PER_CATEGORY = 20
SLEEP_BETWEEN = 6  # search API จำกัด ~10 req/นาที เมื่อไม่ใส่ token

TOPIC_GROUPS = {
    'ai': ['ai', 'llm', 'gpt', 'machine-learning', 'agents'],
    'automation': ['automation', 'workflow', 'rpa', 'n8n'],
    'trading': ['trading', 'finance', 'crypto', 'quantitative-finance'],
    'tool': ['developer-tools', 'cli', 'devops', 'productivity'],
}


def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def build_th_map():
    """รวบรวม description_th เดิมจากทั้ง repos.json และ curated.json"""
    th = {}
    for path in (OUT, CURATED):
        data = load_json(path) or {}
        for r in data.get('repos', []):
            name = r.get('full_name')
            if name and r.get('description_th'):
                th[name] = r['description_th']
    return th


def norm(repo, category, th_map):
    """แปลง response จาก GitHub API เป็น record ของเรา"""
    name = repo['full_name']
    desc = repo.get('description') or 'ไม่มีคำอธิบาย'
    return {
        'full_name': name,
        'description': desc,
        'description_th': th_map.get(name) or translate_th(desc, repo.get('language'), category),
        'language': repo.get('language') or '-',
        'stargazers_count': repo.get('stargazers_count', 0),
        'forks_count': repo.get('forks_count', 0),
        'html_url': repo.get('html_url', 'https://github.com/' + name),
        'topics': repo.get('topics', []),
        'category': category,
    }


def fetch(url, headers):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))


def main():
    token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
    headers = {
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'repohunter-fetch',
    }
    if token:
        headers['Authorization'] = 'token ' + token

    # bootstrap: ครั้งแรกให้คัดลอกรายการปัจจุบันเป็น curated
    if not os.path.exists(CURATED) and os.path.exists(OUT):
        shutil.copy(OUT, CURATED)
        print('bootstrapped %s from %s' % (CURATED, OUT))

    curated = (load_json(CURATED) or {}).get('repos', [])
    th_map = build_th_map()
    print('curated: %d repos | th_map: %d entries' % (len(curated), len(th_map)))

    since = (datetime.now(timezone.utc) - timedelta(days=WINDOW_DAYS)).strftime('%Y-%m-%d')

    # คงรายการที่เคยดึงไว้ ไม่ให้หายเมื่อ API ตอบไม่ครบหรือติด rate limit
    known = {}
    curated_names = {r['full_name'] for r in curated}
    for r in (load_json(OUT) or {}).get('repos', []):
        n = r.get('full_name')
        if n and n not in curated_names:
            known[n] = r
    print('carried over: %d repos from previous run' % len(known))

    fresh_names = []
    first = True

    def upsert(repo, category):
        """อัปเดตข้อมูล repo และคงคำแปลไทยเดิมไว้"""
        name = repo['full_name']
        rec = norm(repo, category, th_map)
        old = known.get(name)
        if old and old.get('description_th'):
            rec['description_th'] = old['description_th']
        if name not in known:
            fresh_names.append(name)
        known[name] = rec

    for category, topics in TOPIC_GROUPS.items():
        picked = 0

        for topic in topics:
            if picked >= MAX_PER_CATEGORY:
                break
            if not first:
                time.sleep(SLEEP_BETWEEN)
            first = False

            q = 'topic:%s created:>%s stars:>50' % (topic, since)
            url = 'https://api.github.com/search/repositories?' + urllib.parse.urlencode({
                'q': q, 'sort': 'stars', 'order': 'desc', 'per_page': PER_PAGE,
            })
            try:
                data = fetch(url, headers)
            except Exception as e:
                print('  ERR %-11s topic:%-20s %s' % (category, topic, e))
                continue

            added = 0
            for repo in data.get('items', []):
                if picked >= MAX_PER_CATEGORY:
                    break
                name = repo['full_name']
                if name in curated_names or name in fresh_names:
                    continue
                upsert(repo, category)
                picked += 1
                added += 1
            print('  ok  %-11s topic:%-20s +%-3d (total %d)'
                  % (category, topic, added, data.get('total_count', 0)))

        print('  ==  %-11s -> %d repos' % (category, picked))

    fetched = list(known.values())
    repos = curated + fetched
    repos.sort(key=lambda r: r.get('stargazers_count', 0), reverse=True)

    now = datetime.now(timezone.utc)
    output = {
        '_meta': {
            'last_update': now.strftime('%Y-%m-%d'),
            'sources': ['LINE Memo (curated)', 'github.com/search'],
            'total_repos': len(repos),
            'curated_count': len(curated),
            'fetched_count': len(fetched),
            'new_this_run': len(fresh_names),
            'next_fetch': (now + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ'),
        },
        'repos': repos,
    }

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

    th_kept = sum(1 for r in repos if r.get('description_th') and r['description_th'] != r.get('description'))
    th_any = sum(1 for r in repos if r.get('description_th'))
    print('WROTE %s: %d repos (%d curated + %d fetched, new this run %d)'
          % (OUT, len(repos), len(curated), len(fetched), len(fresh_names)))
    print('Thai descriptions: %d/%d (hand-written %d)' % (th_any, len(repos), th_kept))


if __name__ == '__main__':
    main()
