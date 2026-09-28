# -*- coding: utf-8 -*-
"""
สร้าง description_th ใหม่ให้ repo ที่ไม่ได้อยู่ใน curated.json
(คำอธิบายของ curated เป็นงานเขียนมือ -> ไม่แตะ)

ใช้หลังแก้เทมเพลต/glossary ใน th_translate.py

usage:
    python refresh_th_desc.py [--dry-run]
"""
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))

from th_translate import translate_th, has_thai  # noqa: E402

REPOS = os.path.join(ROOT, 'data', 'repos.json')
CURATED = os.path.join(ROOT, 'data', 'curated.json')


def load(path):
    with io.open(path, encoding='utf-8') as f:
        return json.load(f)


def main():
    dry = '--dry-run' in sys.argv
    data = load(REPOS)
    curated = {r['full_name'] for r in load(CURATED)['repos']}

    changed = skipped = no_thai = 0
    samples = []
    for r in data['repos']:
        if r['full_name'] in curated:
            skipped += 1
            continue
        new = translate_th(r.get('description'), r.get('language'), r.get('category'))
        if new != r.get('description_th'):
            if len(samples) < 6:
                samples.append((r['full_name'], r.get('description_th'), new))
            r['description_th'] = new
            changed += 1
        if not has_thai(r.get('description_th')):
            no_thai += 1

    if not dry:
        data.setdefault('_meta', {})['th_descriptions'] = len(data['repos'])
        with io.open(REPOS, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    print('repos      : %d' % len(data['repos']))
    print('curated kept: %d' % skipped)
    print('rewritten  : %d' % changed)
    print('no-Thai    : %d' % no_thai)
    print('dry-run    : %s' % dry)
    print('--- ตัวอย่างก่อน -> หลัง ---')
    for name, old, new in samples:
        print('\n%s\n  old: %s\n  new: %s' % (name, old, new))


if __name__ == '__main__':
    main()
