#!/usr/bin/env python3
"""probe_twin_census_gen624.py — ДВОЙНИК-CENSUS: same-basename группы *.py поперёк корней.
Грамматика: group by basename; группа = >=2 тел в РАЗНЫХ директориях; вариант = уникальный md5.
Единицы: группы / тела / варианты. Read-only. Roots аргументами (переносим).
Smoke: --smoke строит трёхтельного лжеца в tmpdir и требует точной классификации ДО корпуса.
Дисклоз: unreadable файлы НЕ скипаются молча (поле unreadable)."""
import sys, os, hashlib, json, tempfile, shutil
from collections import defaultdict

EXCL_DIRS = {'.git', 'node_modules', 'z_trash', '__pycache__'}
def excluded(name):
    return name == '__init__.py' or name.startswith('tmp') or '.bak' in name

def scan(roots):
    groups = defaultdict(list); unreadable = []
    for root in roots:
        for dp, dns, fns in os.walk(root):
            dns[:] = [d for d in dns if d not in EXCL_DIRS]
            for fn in fns:
                if not fn.endswith('.py') or excluded(fn): continue
                p = os.path.join(dp, fn)
                try:
                    h = hashlib.md5(open(p,'rb').read()).hexdigest()
                except OSError as e:
                    unreadable.append({'path': p, 'err': str(e)}); continue
                groups[fn].append({'path': p, 'md5': h})
    twins = {}
    for bn, bodies in groups.items():
        if len(bodies) < 2: continue
        if len({os.path.dirname(b['path']) for b in bodies}) < 2: continue
        variants = len({b['md5'] for b in bodies})
        twins[bn] = {'bodies': bodies, 'n_bodies': len(bodies), 'n_variants': variants,
                     'status': 'identical' if variants == 1 else 'divergent',
                     'frozen_probe': bn.startswith('probe_')}
    return twins, unreadable

def smoke():
    td = tempfile.mkdtemp(prefix='twinsmoke_')
    try:
        a, b = os.path.join(td,'rootA'), os.path.join(td,'rootB')
        os.makedirs(os.path.join(a,'engine')); os.makedirs(os.path.join(b,'clone'))
        # (i) identical pair
        for d in (os.path.join(a,'engine'), os.path.join(b,'clone')):
            open(os.path.join(d,'same_twin.py'),'w').write("x = 1\n")
        # (ii) lag pair: clone missing cure line
        open(os.path.join(a,'engine','lag_twin.py'),'w').write("x = 1\n# CURE gen-551 entropy\ny = 2\n")
        open(os.path.join(b,'clone','lag_twin.py'),'w').write("x = 1\ny = 2\n")
        # (iii) unique body, no twin
        open(os.path.join(a,'engine','lonely.py'),'w').write("z = 3\n")
        twins, unr = scan([a, b])
        ok = (len(twins) == 2 and unr == []
              and twins.get('same_twin.py',{}).get('status') == 'identical'
              and twins.get('lag_twin.py',{}).get('status') == 'divergent'
              and 'lonely.py' not in twins)
        print(f"SMOKE {'EATEN' if ok else 'BLIND'}: groups={len(twins)} "
              f"same={twins.get('same_twin.py',{}).get('status')} lag={twins.get('lag_twin.py',{}).get('status')} "
              f"lonely_in={'lonely.py' in twins}")
        return 0 if ok else 1
    finally:
        shutil.rmtree(td)

if __name__ == '__main__':
    if '--smoke' in sys.argv: sys.exit(smoke())
    roots = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not roots: print("usage: probe_twin_census_gen624.py ROOT [ROOT...] | --smoke"); sys.exit(2)
    twins, unreadable = scan(roots)
    out = {'roots': roots, 'n_groups': len(twins),
           'n_identical': sum(1 for t in twins.values() if t['status']=='identical'),
           'n_divergent': sum(1 for t in twins.values() if t['status']=='divergent'),
           'unreadable': unreadable, 'groups': twins}
    print(json.dumps(out, indent=1, ensure_ascii=False))
