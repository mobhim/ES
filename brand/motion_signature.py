#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
motion_signature.py  --  motion fingerprint of a single-file HTML page (stdlib only).

Usage
-----
  python motion_signature.py <page.html> [out.json]        build a signature (stdout if no out)
  python motion_signature.py --compare <a.json> <b.json>   diff two signatures
  python motion_signature.py --check <base.json> <page.html>
                                                           build a signature of page.html in
                                                           memory and diff it against base.json

Exit code of --compare / --check:
  0  the "strict" sections are identical (advisory differences are printed as WARN)
  1  at least one "strict" difference  -> something motion-related changed
  2  usage / IO error

Signature layout
----------------
  strict    everything that defines HOW things move. Must be identical before/after a re-skin.
  advisory  things a re-skin is ALLOWED to change (token values, hard-coded colours, colour
            end-points of colour transitions, icon path data ...) but that are worth a look.
            Keys called "line" are ignored by the comparison (line numbers shift freely).

All text is whitespace-normalised. Output is deterministic (no timestamps, no paths,
sorted keys, source order for lists).
"""
import sys, re, json, hashlib, difflib
from html.parser import HTMLParser

SIG_VERSION = 1

# ----------------------------------------------------------------------------- config
MOTION_PROP = re.compile(
    r'^(transition|animation|transform|offset-|opacity$|will-change$|clip-path$|'
    r'stroke-dasharray$|stroke-dashoffset$|view-transition-name$|scroll-behavior$|'
    r'rotate$|scale$|translate$)')
# transitioned properties whose END VALUES are colour/shadow (re-skinnable) -> advisory
COLOR_TRANSITION_PROPS = ('background', 'background-color', 'color', 'border-color', 'box-shadow',
                          'fill', 'stroke', 'outline-color')
# state classes / pseudo parts stripped when relating a "state" rule to its base rule
STATE_CLASSES = ('on', 'sel', 'in', 'off', 'play', 'pre', 'bump', 'pulse')
# a JS function is a "motion function" (strict, full source) when its body matches this
JS_MOTION = re.compile(
    r'\.animate\(|\banim\(|\btween\(|\bopenAnim\(|setTimeout|clearTimeout|requestAnimationFrame|'
    r'classList|IntersectionObserver|\bio\.|startViewTransition|setProperty|\.style\.|'
    r'scrollTo|scrollIntoView|\bplay\(|\benter\(|\bpill\(|\broute\(|\bnav\(|invalidateSize|'
    r'fitBounds|offsetWidth|dataset\.theme|matchMedia|addEventListener|document\.fonts|'
    r'\bRM\b|\bEASE\b|\bVIEWS\s*=')
# functions that only build markup, but markup the motion system hangs on (bays, chips, curves)
FORCED_MOTION_FUNCS = ('step', 'arcade', 'chips', 'curves')
JS_CALLSITES = [
    ('animate', r'\.animate\('), ('anim', r'(?<![\w$.])anim\('), ('tween', r'(?<![\w$.])tween\('),
    ('openAnim', r'(?<![\w$.])openAnim\('), ('setTimeout', r'(?<![\w$.])setTimeout\('),
    ('clearTimeout', r'(?<![\w$.])clearTimeout\('),
    ('requestAnimationFrame', r'(?<![\w$.])requestAnimationFrame\('),
    ('IntersectionObserver', r'new\s+IntersectionObserver\('),
    ('startViewTransition', r'\.startViewTransition\('),
    ('addEventListener', r'(?<![\w$])(?:[\w$.]+\.)?addEventListener\('),
    ('setProperty', r'\.setProperty\('), ('matchMedia', r'(?<![\w$.])matchMedia\('),
    ('scrollTo', r'(?<![\w$.])scrollTo\('), ('scrollIntoView', r'\.scrollIntoView\('),
    ('observe', r'\.(?:un)?observe\('), ('classList', r'\.classList\.\w+\('),
    ('fonts.ready', r'document\.fonts\.ready\.then\('),
]
TIMING_KINDS = ('animate', 'anim', 'tween', 'openAnim', 'setTimeout', 'IntersectionObserver')
COLOR_RE = re.compile(
    r'#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})(?![\w-])|'
    r'\b(?:rgba?|hsla?)\([^()]*\)')
NUM_RE = re.compile(r'(?<![\w.$#-])(\d+\.\d+|\.\d+|\d+)(?![\w])')


def ws(s):
    return re.sub(r'\s+', ' ', s).strip()


def tight(s):
    return re.sub(r'\s*([{};:,>])\s*', r'\1', ws(s))


def nsel(s):
    return re.sub(r'\s*([,>+~])\s*', r'\1', ws(s))


def nval(s):
    return re.sub(r'\s*,\s*', ',', ws(s))


def sha(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def mask_colors(s):
    return COLOR_RE.sub('<COLOR>', s)


# ----------------------------------------------------------------------------- CSS
def css_skip_string(t, i):
    q = t[i]
    i += 1
    while i < len(t):
        if t[i] == '\\':
            i += 2
            continue
        if t[i] == q:
            return i + 1
        i += 1
    return i


def css_match_brace(t, i):
    depth = 0
    while i < len(t):
        c = t[i]
        if c in '"\'':
            i = css_skip_string(t, i)
            continue
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return len(t) - 1


def css_blocks(t):
    out, i, start, n = [], 0, 0, len(t)
    while i < n:
        c = t[i]
        if c in '"\'':
            i = css_skip_string(t, i)
            continue
        if c == '{':
            j = css_match_brace(t, i)
            out.append((t[start:i].strip(), t[i + 1:j]))
            i = j + 1
            start = i
            continue
        if c == ';':
            start = i + 1
        i += 1
    return out


def css_decls(body):
    out, i, start, depth, n = [], 0, 0, 0, len(body)
    parts = []
    while i < n:
        c = body[i]
        if c in '"\'':
            i = css_skip_string(body, i)
            continue
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
        elif c == ';' and depth == 0:
            parts.append(body[start:i])
            start = i + 1
        i += 1
    parts.append(body[start:])
    for p in parts:
        if ':' not in p:
            continue
        k, v = p.split(':', 1)
        k = ws(k).lower() if not ws(k).startswith('--') else ws(k)
        if k:
            out.append((k, nval(v)))
    return out


def var_refs(value, names):
    """balanced var(--name ...) references to the given custom property names"""
    refs = []
    for m in re.finditer(r'var\(\s*(--[\w-]+)', value):
        if m.group(1) not in names:
            continue
        i, depth = m.start() + 3, 0
        while i < len(value):
            if value[i] == '(':
                depth += 1
            elif value[i] == ')':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        refs.append(nval(value[m.start():i + 1]))
    return refs


def strip_state(sel):
    s = re.sub(r'\[[^\]]*\]', '', sel)
    s = re.sub(r'(?<!:):(?!:)[\w-]+(\([^)]*\))?', '', s)          # pseudo-classes, keep ::pseudo-elements
    for c in STATE_CLASSES:
        s = re.sub(r'\.' + c + r'(?![\w-])', '', s)
    s = re.sub(r'\s*>\s*(?=,|$)', '', s)
    return nsel(s)


def analyse_css(css_raw, js_vars):
    css = re.sub(r'/\*.*?\*/', '', css_raw, flags=re.S)
    rules, keyframes, rm_blocks, at_other = [], [], [], []

    def walk(blocks, ctx):
        for prelude, body in blocks:
            p = ws(prelude)
            low = p.lower()
            if low.startswith('@keyframes') or low.startswith('@-webkit-keyframes'):
                keyframes.append({'ctx': ' && '.join(ctx), 'name': p.split(None, 1)[1].strip(),
                                  'body': tight(body)})
            elif low.startswith(('@media', '@supports', '@container', '@layer', '@scope')):
                if 'prefers-reduced-motion' in low:
                    rm_blocks.append({'ctx': ' && '.join(ctx), 'query': tight(p), 'body': tight(body)})
                walk(css_blocks(body), ctx + [tight(p)])
            elif low.startswith('@'):
                at_other.append({'ctx': ' && '.join(ctx), 'rule': p, 'body': tight(body)})
            else:
                rules.append({'ctx': ' && '.join(ctx), 'selector': nsel(p), 'decls': css_decls(body)})

    walk(css_blocks(css), [])

    strict, adv = {}, {}
    strict['keyframes'] = keyframes
    strict['keyframes_names_in_order'] = [k['name'] for k in keyframes]
    strict['reduced_motion_blocks'] = rm_blocks
    strict['view_transition_rules'] = [
        {'ctx': r['ctx'], 'selector': r['selector'], 'decls': [k + ':' + v for k, v in r['decls']]}
        for r in rules if '::view-transition' in r['selector']]

    motion_rules = []
    for r in rules:
        d = [k + ':' + v for k, v in r['decls'] if MOTION_PROP.match(k)]
        if d:
            motion_rules.append({'ctx': r['ctx'], 'selector': r['selector'], 'decls': d})
    strict['motion_rules'] = motion_rules

    # custom properties referenced inside motion declarations / keyframes -> their definitions
    used = set()
    for r in motion_rules:
        for d in r['decls']:
            used.update(re.findall(r'var\(\s*(--[\w-]+)', d))
    for k in keyframes:
        used.update(re.findall(r'var\(\s*(--[\w-]+)', k['body']))
    strict['vars_used_in_motion'] = sorted(used)
    strict['motion_var_definitions'] = [
        {'ctx': r['ctx'], 'selector': r['selector'], 'name': k, 'value': v}
        for r in rules for k, v in r['decls'] if k in used]

    # where the custom properties that JS sets are consumed (var references only -> strict)
    usages, usages_full = [], []
    for r in rules:
        for k, v in r['decls']:
            refs = var_refs(v, js_vars)
            if refs:
                usages.append({'ctx': r['ctx'], 'selector': r['selector'], 'prop': k, 'var_refs': refs})
                usages_full.append({'ctx': r['ctx'], 'selector': r['selector'], 'decl': k + ':' + v})
    strict['js_var_usages'] = usages
    adv['js_var_usages_full'] = usages_full

    # transitions: geometry end-points (strict) and colour/shadow end-points (advisory)
    geo, col = [], []
    for t in rules:
        props = set()
        for k, v in t['decls']:
            if k == 'transition' or k == 'transition-property':
                for part in re.split(r',(?![^()]*\))', v):
                    part = part.strip()
                    if part:
                        props.add(part.split()[0])
        if not props:
            continue
        base = set(strip_state(s) for s in t['selector'].split(','))

        def related(sel, base=base):
            for s in sel.split(','):
                s = strip_state(s)
                if any(s == b or s.endswith(' ' + b) or s.endswith('>' + b) for b in base):
                    return True
            return False
        gprops = sorted(p for p in props if p not in COLOR_TRANSITION_PROPS
                        and not MOTION_PROP.match(p) and p not in ('all', 'none'))
        cprops = sorted(p for p in props if p in COLOR_TRANSITION_PROPS)
        for r in rules:
            if not related(r['selector']):
                continue
            g = [k + ':' + v for k, v in r['decls'] if any(k == p or k.startswith(p + '-') for p in gprops)]
            c = [k + ':' + v for k, v in r['decls'] if any(k == p or k.startswith(p + '-') for p in cprops)]
            if g:
                geo.append({'transition_on': t['selector'], 'ctx': r['ctx'], 'selector': r['selector'], 'decls': g})
            if c:
                col.append({'transition_on': t['selector'], 'ctx': r['ctx'], 'selector': r['selector'], 'decls': c})

    def dedup(lst):
        seen, out = set(), []
        for x in lst:
            key = json.dumps(x, sort_keys=True, ensure_ascii=False)
            if key not in seen:
                seen.add(key)
                out.append(x)
        return out
    strict['transition_geometry_endpoints'] = dedup(geo)
    adv['transition_color_endpoints'] = dedup(col)

    # keyframes that animate non-standard properties (e.g. background-size/-position):
    # the base declarations of those properties on the animated elements are strict
    kf_props = {}
    for k in keyframes:
        ps = set(re.findall(r'[{;]([a-z-]+):', k['body']))
        extra = sorted(p for p in ps if not MOTION_PROP.match(p) and p != 'filter')
        if extra:
            kf_props.setdefault(k['name'], set()).update(extra)
    bases = []
    for r in rules:
        for k, v in r['decls']:
            if not k.startswith('animation'):
                continue
            for name, extra in sorted(kf_props.items()):
                if not re.search(r'(?<![\w-])' + re.escape(name) + r'(?![\w-])', v):
                    continue
                shorthands = sorted(set(p.split('-')[0] for p in extra))
                targets = set(strip_state(s) for s in r['selector'].split(','))
                for r2 in rules:
                    if not (set(strip_state(s) for s in r2['selector'].split(',')) & targets):
                        continue
                    d = [k2 + ':' + v2 for k2, v2 in r2['decls']
                         if any(k2 == sh or k2.startswith(sh + '-') for sh in shorthands)]
                    if d:
                        bases.append({'keyframes': name, 'animated_props': sorted(extra), 'ctx': r2['ctx'],
                                      'selector': r2['selector'], 'decls': d})
    strict['keyframe_animated_base_values'] = dedup(bases)

    # selector vocabulary of motion rules
    msel = ' '.join(r['selector'] for r in motion_rules) + ' ' + ' '.join(b['body'] for b in rm_blocks)
    msel_nostr = re.sub(r'\[[^\]]*\]', lambda m: m.group(0).replace('.', ' ').replace('#', ' '), msel)
    strict['motion_selector_classes'] = sorted(set(re.findall(r'\.(-?[A-Za-z_][\w-]*)', msel_nostr)))
    strict['motion_selector_ids'] = sorted(set(re.findall(r'#([A-Za-z_][\w-]*)', msel_nostr)))
    strict['motion_selector_attrs'] = sorted(set(re.findall(r'\[[^\]]*\]', msel)))

    all_decl = [(r, k, v) for r in rules for k, v in r['decls']]
    n_tr = sum(1 for r, k, v in all_decl if k.startswith('transition'))
    n_an = sum(1 for r, k, v in all_decl if k.startswith('animation'))
    strict['counts'] = {
        'keyframes_blocks': len(keyframes),
        'keyframes_unique_names': len(set(k['name'] for k in keyframes)),
        'transition_declarations': n_tr,
        'transition_declarations_outside_reduced_motion': sum(
            1 for r, k, v in all_decl if k.startswith('transition') and 'prefers-reduced-motion' not in r['ctx']),
        'animation_declarations': n_an,
        'animation_declarations_outside_reduced_motion': sum(
            1 for r, k, v in all_decl if k.startswith('animation') and 'prefers-reduced-motion' not in r['ctx']),
        'motion_rules': len(motion_rules),
        'reduced_motion_blocks': len(rm_blocks),
        'view_transition_rules': len(strict['view_transition_rules']),
    }

    # advisory: design tokens
    tokens = {}
    for r in rules:
        for k, v in r['decls']:
            if k.startswith('--'):
                tokens.setdefault(r['selector'], {})[k] = v
    adv['token_definitions'] = tokens
    adv['other_at_rules'] = at_other
    cc = {}
    for m in COLOR_RE.finditer(css):
        c = m.group(0).lower()
        cc[c] = cc.get(c, 0) + 1
    adv['hardcoded_color_counts_css'] = cc
    return strict, adv, tokens


# ----------------------------------------------------------------------------- JS
def js_skip(s, i):
    """if a string / template / comment starts at i return the index just after it, else None"""
    c = s[i]
    if c in '"\'':
        j = i + 1
        while j < len(s):
            if s[j] == '\\':
                j += 2
                continue
            if s[j] == c or s[j] == '\n':
                return j + 1
            j += 1
        return j
    if c == '`':
        j = i + 1
        while j < len(s):
            if s[j] == '\\':
                j += 2
                continue
            if s[j] == '`':
                return j + 1
            if s[j] == '$' and s[j + 1:j + 2] == '{':
                j = js_match(s, j + 1) + 1
                continue
            j += 1
        return j
    if c == '/' and s[i + 1:i + 2] == '*':
        j = s.find('*/', i + 2)
        return len(s) if j < 0 else j + 2
    if c == '/' and s[i + 1:i + 2] == '/':
        j = s.find('\n', i)
        return len(s) if j < 0 else j
    return None


def js_match(s, i):
    """s[i] is an opener ( [ { ; return index of its closer"""
    depth = 0
    while i < len(s):
        j = js_skip(s, i)
        if j is not None:
            i = j
            continue
        c = s[i]
        if c in '([{':
            depth += 1
        elif c in ')]}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return len(s) - 1


def js_code_positions(s):
    """set of indices that are real code (not inside strings/comments)"""
    code, i = bytearray(len(s)), 0
    while i < len(s):
        c = s[i]
        if c in '"\'' or (c == '/' and s[i + 1:i + 2] in ('*', '/')):
            i = js_skip(s, i)
            continue
        if c == '`':                      # template: only the ${ } parts are code
            j = i + 1
            while j < len(s):
                if s[j] == '\\':
                    j += 2
                    continue
                if s[j] == '`':
                    j += 1
                    break
                if s[j] == '$' and s[j + 1:j + 2] == '{':
                    e = js_match(s, j + 1)
                    inner = js_code_positions(s[j + 2:e])
                    for k, v in enumerate(inner):
                        code[j + 2 + k] = v
                    j = e + 1
                    continue
                j += 1
            i = j
            continue
        code[i] = 1
        i += 1
    return code


def analyse_js(js, line0, head_scripts):
    strict, adv = {}, {}
    code = js_code_positions(js)

    def lineno(off):
        return line0 + js.count('\n', 0, off)

    # ---- functions
    funcs, ranges = [], []
    for m in re.finditer(r'\bfunction\s+([A-Za-z_$][\w$]*)\s*\(', js):
        if not code[m.start()]:
            continue
        pc = js_match(js, m.end() - 1)
        b = js.find('{', pc)
        e = js_match(js, b)
        funcs.append((m.group(1), m.start(), e + 1))
    for name, a, b in funcs:
        if not any(a2 < a and b <= b2 for _, a2, b2 in funcs):
            ranges.append((a, b))
    motion_f, other_f = {}, {}
    for name, a, b in funcs:
        src = ws(js[a:b])
        key = name if name not in motion_f and name not in other_f else name + '@' + str(len(motion_f) + len(other_f))
        if JS_MOTION.search(src) or name in FORCED_MOTION_FUNCS:
            motion_f[key] = mask_colors(src)
        else:
            other_f[key] = sha(mask_colors(src))
    strict['motion_functions'] = motion_f
    strict['function_names_in_order'] = [f[0] for f in funcs]
    adv['other_functions_sha256'] = other_f

    # ---- call sites
    calls, timing_numbers, per_call_numbers = {}, [], []
    for kind, pat in JS_CALLSITES:
        lst = []
        for m in re.finditer(pat, js):
            if not code[m.start() if js[m.start()] != '.' else m.start() + 1]:
                continue
            if kind in ('anim', 'tween', 'openAnim') and re.search(r'function\s+$', js[max(0, m.start() - 12):m.start()]):
                continue
            a = m.start()
            if js[a] == '.':
                while a > 0 and re.match(r'[\w$.\])]', js[a - 1]):
                    if js[a - 1] in ')]':
                        break
                    a -= 1
            e = js_match(js, m.end() - 1)
            txt = mask_colors(ws(js[a:e + 1]))
            lst.append(txt)
            if kind in TIMING_KINDS:
                nums = NUM_RE.findall(txt)
                per_call_numbers.append({'kind': kind, 'call': txt[:90], 'numbers': nums})
                timing_numbers.extend(nums)
        calls[kind] = lst
    strict['call_sites'] = calls
    strict['timing_numbers_per_call'] = per_call_numbers
    strict['timing_numbers_sorted'] = sorted(timing_numbers, key=lambda x: (float(x), x))

    # ---- top level motion lines (outside any function)
    tl, off = [], 0
    for ln in js.split('\n'):
        if not any(a <= off < b for a, b in ranges) and JS_MOTION.search(ln):
            tl.append(mask_colors(ws(ln)))
        off += len(ln) + 1
    strict['top_level_motion_lines'] = tl
    strict['head_inline_scripts'] = [ws(h) for h in head_scripts]

    # ---- hooks: classes / ids / data-attrs / custom properties referenced from JS
    classes, ids, selectors, data_attrs, css_vars_set = set(), set(), [], set(), set()
    for m in re.finditer(r'classList\.\w+\(\s*([\'"])([^\'"]+)\1', js):
        classes.update(m.group(2).split())
    for m in re.finditer(r'className\s*=\s*([\'"])([^\'"]*)\1', js):
        classes.update(m.group(2).split())

    def lit(i):                                   # string literal starting at i -> text with ${} collapsed
        e = js_skip(js, i)
        body = js[i + 1:e - 1]
        if js[i] == '`':
            out, j = '', 0
            while j < len(body):
                if body[j] == '$' and body[j + 1:j + 2] == '{':
                    j = js_match(body, j + 1) + 1
                    out += '${}'
                    continue
                out += body[j]
                j += 1
            body = out
        return body
    for m in re.finditer(r'(?:(?<![\w$.])\$|\.querySelectorAll|\.querySelector|\.closest|\.matches)\(\s*(?=[\'"`])', js):
        if code[m.start() if js[m.start()] != '.' else m.start() + 1]:
            selectors.append(lit(m.end()))
    for m in re.finditer(r'[\'"`]#[A-Za-z]', js):      # ids handed to helpers: chips('#x'), arcade('#x') ...
        if code[m.start()]:
            s_ = lit(m.start())
            if not COLOR_RE.fullmatch(s_) and s_ not in selectors:
                selectors.append(s_)
    for s_ in selectors:
        bare = re.sub(r'\[[^\]]*\]', '', s_)
        classes.update(re.findall(r'\.(-?[A-Za-z_][\w-]*)', bare))
        ids.update(re.findall(r'#([A-Za-z_][\w-]*-?)', bare))
        data_attrs.update(re.findall(r'\[(data-[\w-]+)', s_))
    class_templates = []
    for m in re.finditer(r'class="([^"]*)"', js):
        raw = m.group(1)
        class_templates.append(ws(raw))
        static = re.sub(r'\$\{[^}]*\}', ' ', raw)
        classes.update(t for t in static.split() if re.fullmatch(r'-?[A-Za-z_][\w-]*', t))
        for t in re.findall(r'[\w-]+\$\{', raw):
            classes.add(t[:-2] + '${}')
        for inner in re.findall(r'\$\{([^}]*)\}', raw):
            for q in re.findall(r'\'([^\']*)\'', inner):
                classes.update(q.split())
    strict['class_attr_templates'] = sorted(set(class_templates))
    for m in re.finditer(r'(?<![\w-])id="([^"${]+)"', js):
        ids.add(m.group(1))
    for m in re.finditer(r'\.id\s*===?\s*\'([^\']+)\'', js):
        ids.add(m.group(1))
    data_attrs.update('data-' + x for x in re.findall(r'(?<![\w-])data-([a-z][\w-]*)=', js))
    data_attrs.update('dataset.' + x for x in re.findall(r'\.dataset\.([A-Za-z_]\w*)', js))
    css_vars_set.update(re.findall(r'setProperty\(\s*\'(--[\w-]+)\'', js))
    style_tpl, style_color = [], []
    for m in re.finditer(r'style="([^"]*)"', js):
        raw = ws(m.group(1))
        names = re.findall(r'(?:^|;)\s*(--[\w-]+)\s*:', raw)
        css_vars_set.update(names)
        if names:
            style_tpl.append(mask_colors(raw))
        if COLOR_RE.search(raw) or 'color' in raw or 'background' in raw:
            style_color.append({'line': lineno(m.start()), 'style': raw})
    strict['classes_referenced'] = sorted(classes)
    strict['ids_referenced'] = sorted(ids)
    strict['selectors_referenced'] = sorted(set(selectors))
    strict['data_attributes_referenced'] = sorted(data_attrs)
    strict['css_vars_set_from_js'] = sorted(css_vars_set)
    strict['inline_style_templates_with_css_vars'] = style_tpl
    strict['css_tokens_referenced_from_js'] = sorted(set(re.findall(r'var\(\s*(--[\w-]+)', js)))
    strict['pathLength_in_js_templates'] = len(re.findall(r'pathLength="1"', js))
    strict['counts'] = {k: len(v) for k, v in calls.items()}
    strict['counts']['functions'] = len(funcs)
    strict['counts']['motion_functions'] = len(motion_f)

    # ---- advisory: hard coded colours in JS, inline styles carrying colours, icon data
    colors = []
    for m in COLOR_RE.finditer(js):
        a = js.rfind('\n', 0, m.start()) + 1
        e = js.find('\n', m.start())
        line = js[a:e if e >= 0 else len(js)]
        col0 = m.start() - a
        colors.append({'line': lineno(m.start()), 'color': m.group(0),
                       'code': ws(line[max(0, col0 - 50):col0 + 40])})
    adv['hardcoded_colors_js'] = colors
    adv['inline_styles_with_color_in_js_templates'] = style_color
    adv['icon_constants_sha256'] = {
        n: sha(ws(mm.group(0))) for n, mm in
        ((n, re.search(r'\b' + n + r'\s*=\s*(\{.*?\n\};|\'[^\']*\')', js, re.S)) for n in ('IC', 'SUN', 'MOON')) if mm}
    adv['script_sha256_color_masked'] = sha(mask_colors(ws(js)))
    return strict, adv, css_vars_set, classes, ids


# ----------------------------------------------------------------------------- HTML
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}


class Tree(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.root = {'tag': '#root', 'attrs': {}, 'children': []}
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        n = {'tag': tag, 'attrs': dict((k, v if v is not None else '') for k, v in attrs), 'children': []}
        self.stack[-1]['children'].append(n)
        if tag not in VOID:
            self.stack.append(n)

    def handle_startendtag(self, tag, attrs):
        n = {'tag': tag, 'attrs': dict((k, v if v is not None else '') for k, v in attrs), 'children': []}
        self.stack[-1]['children'].append(n)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i]['tag'] == tag:
                del self.stack[i:]
                break


def walk_nodes(n):
    yield n
    for c in n['children']:
        for x in walk_nodes(c):
            yield x


def label(n):
    a = n['attrs']
    s = n['tag']
    if a.get('class'):
        s += ''.join('.' + c for c in a['class'].split())
    if a.get('id'):
        s += '#' + a['id']
    for k in ('pathlength', 'hidden', 'data-suf', 'href'):
        if k in a and (k != 'href' or a[k].startswith('#')):
            s += '[' + k + ('=' + a[k] if a[k] else '') + ']'
    return s


def skel(n, depth):
    if depth == 0 or not n['children']:
        return label(n)
    return label(n) + '(' + ' '.join(skel(c, depth - 1) for c in n['children']) + ')'


def has_class(n, c):
    return c in n['attrs'].get('class', '').split()


def analyse_html(html, js_classes, js_ids, css_classes, css_ids):
    strict, adv = {}, {}
    t = Tree()
    t.feed(html)
    nodes = list(walk_nodes(t.root))
    first = lambda pred: next((n for n in nodes if pred(n)), None)
    h = first(lambda n: n['tag'] == 'html')
    strict['html_attrs'] = {k: v for k, v in (h['attrs'] if h else {}).items()}
    strict['external_scripts'] = [n['attrs']['src'] for n in nodes if n['tag'] == 'script' and 'src' in n['attrs']]
    strict['external_stylesheets'] = [n['attrs'].get('href', '') for n in nodes
                                      if n['tag'] == 'link' and n['attrs'].get('rel') == 'stylesheet'
                                      and 'fonts.googleapis' not in n['attrs'].get('href', '')]
    adv['font_stylesheets'] = [n['attrs'].get('href', '') for n in nodes
                               if n['tag'] == 'link' and 'fonts.googleapis' in n['attrs'].get('href', '')]
    roots = {
        'brand': first(lambda n: has_class(n, 'brand')),
        'nav': first(lambda n: n['attrs'].get('id') == 'nav'),
        'themeBtn': first(lambda n: n['attrs'].get('id') == 'themeBtn'),
        'title': first(lambda n: n['attrs'].get('id') == 'title'),
        'toast': first(lambda n: n['attrs'].get('id') == 'toast'),
        'pitch': first(lambda n: has_class(n, 'pitch')),
        'flow': first(lambda n: has_class(n, 'flow')),
        'rail': first(lambda n: has_class(n, 'rail')),
        'app': first(lambda n: has_class(n, 'app')),
    }
    depth = {'rail': 1, 'app': 2}
    strict['skeletons'] = {k: (skel(v, depth.get(k, 99)) if v else None) for k, v in roots.items()}
    strict['views'] = [{'view': label(n), 'children': [skel(c, 2) for c in n['children']]}
                       for n in nodes if n['tag'] == 'section' and has_class(n, 'view')]
    top = first(lambda n: has_class(n, 'top'))
    adv['header_skeleton'] = skel(top, 99) if top else None
    static_ids, static_classes = {}, {}
    for n in nodes:
        if n['attrs'].get('id'):
            static_ids[n['attrs']['id']] = n['tag']
        for c in n['attrs'].get('class', '').split():
            static_classes[c] = static_classes.get(c, 0) + 1
    hook_ids = sorted(set(js_ids) | set(css_ids))
    hook_classes = sorted(c for c in (set(js_classes) | set(css_classes)) if '${}' not in c)
    strict['hook_ids_in_static_html'] = {i: static_ids.get(i) for i in hook_ids}
    strict['hook_class_counts_in_static_html'] = {c: static_classes.get(c, 0) for c in hook_classes}
    strict['pathLength_in_static_html'] = sum(1 for n in nodes if 'pathlength' in n['attrs'])
    strict['inline_styles_with_motion_props'] = [
        label(n) + ' {' + ws(n['attrs']['style']) + '}' for n in nodes
        if 'style' in n['attrs'] and re.search(
            r'(?:^|;)\s*(transition|animation|transform|opacity|will-change|clip-path|--[\w-]+)\s*:',
            n['attrs']['style'])]
    strict['inline_event_handlers'] = [label(n) + ' ' + k + '=' + v for n in nodes
                                       for k, v in sorted(n['attrs'].items()) if k.startswith('on')]
    adv['static_ids'] = sorted(static_ids)
    adv['static_class_counts'] = static_classes
    adv['inline_styles_with_color_in_static_html'] = [
        label(n) + ' {' + ws(n['attrs']['style']) + '}' for n in nodes
        if 'style' in n['attrs'] and ('color' in n['attrs']['style'] or 'background' in n['attrs']['style'])]
    adv['svg_presentation_colors_in_static_html'] = [
        label(n) + ' ' + k + '=' + v for n in nodes for k, v in sorted(n['attrs'].items())
        if k in ('stroke', 'fill') and COLOR_RE.search(v)]
    adv['meta_theme_color'] = [n['attrs'].get('content') for n in nodes
                               if n['tag'] == 'meta' and n['attrs'].get('name') == 'theme-color']
    return strict, adv


# ----------------------------------------------------------------------------- build
def build(path):
    with open(path, 'r', encoding='utf-8', newline='') as f:
        html = f.read().replace('\r\n', '\n').replace('\r', '\n')
    css = '\n'.join(m.group(1) for m in re.finditer(r'<style[^>]*>(.*?)</style>', html, re.S | re.I))
    scripts = [(m.group(1), m.start(1)) for m in re.finditer(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', html, re.S | re.I)]
    body_at = html.lower().find('<body')
    head_scripts = [s for s, off in scripts if off < body_at]
    main = [(s, off) for s, off in scripts if off >= body_at]
    js = '\n'.join(s for s, off in main)
    line0 = html.count('\n', 0, main[0][1]) + 1 if main else 1

    js_strict, js_adv, js_vars, js_classes, js_ids = analyse_js(js, line0, head_scripts)
    css_strict, css_adv, tokens = analyse_css(css, js_vars)
    html_strict, html_adv = analyse_html(html, js_classes, js_ids,
                                         css_strict['motion_selector_classes'], css_strict['motion_selector_ids'])

    # token usage counts over the whole file (var(--x) references, definitions excluded)
    usage = {}
    for sel, d in tokens.items():
        for name in d:
            usage[name] = len(re.findall(r'var\(\s*' + re.escape(name) + r'(?![\w-])', html))
    css_adv['token_usage_counts'] = usage

    sig = {
        'signature_version': SIG_VERSION,
        'strict': {'css': css_strict, 'js': js_strict, 'html': html_strict},
        'advisory': {'css': css_adv, 'js': js_adv, 'html': html_adv},
    }
    sig['strict_sha256'] = sha(json.dumps(sig['strict'], ensure_ascii=False, sort_keys=True))
    return sig


def dump(sig):
    return json.dumps(sig, ensure_ascii=False, sort_keys=True, indent=1) + '\n'


# ----------------------------------------------------------------------------- compare
def drop_lines(x):
    if isinstance(x, dict):
        return {k: drop_lines(v) for k, v in x.items() if k != 'line'}
    if isinstance(x, list):
        return [drop_lines(v) for v in x]
    return x


def short(x, n=260):
    s = x if isinstance(x, str) else json.dumps(x, ensure_ascii=False, sort_keys=True)
    return s if len(s) <= n else s[:n] + ' ...[+%d]' % (len(s) - n)


def diff(a, b, path, out):
    if a == b:
        return
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in b:
                out.append((path + '/' + k, 'REMOVED', short(a[k]), ''))
            elif k not in a:
                out.append((path + '/' + k, 'ADDED', '', short(b[k])))
            else:
                diff(a[k], b[k], path + '/' + k, out)
    elif isinstance(a, list) and isinstance(b, list):
        ja = [json.dumps(x, ensure_ascii=False, sort_keys=True) for x in a]
        jb = [json.dumps(x, ensure_ascii=False, sort_keys=True) for x in b]
        sm = difflib.SequenceMatcher(None, ja, jb, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == 'equal':
                continue
            if tag == 'replace' and i2 - i1 == j2 - j1:
                for k in range(i2 - i1):
                    out.append(('%s[%d]' % (path, i1 + k), 'CHANGED', short(a[i1 + k]), short(b[j1 + k])))
                continue
            for k in range(i1, i2):
                out.append(('%s[%d]' % (path, k), 'REMOVED', short(a[k]), ''))
            for k in range(j1, j2):
                out.append(('%s[%d]' % (path, k), 'ADDED', '', short(b[k])))
    else:
        out.append((path, 'CHANGED', short(a), short(b)))


def compare(a, b):
    w = sys.stdout.write
    s, v = [], []
    diff(a.get('strict'), b.get('strict'), 'strict', s)
    diff(drop_lines(a.get('advisory')), drop_lines(b.get('advisory')), 'advisory', v)
    for name, lst in (('WARN', v), ('FAIL', s)):
        for path, kind, old, new in lst:
            w('%s %s %s\n' % (name, kind, path))
            if old:
                w('    - %s\n' % old)
            if new:
                w('    + %s\n' % new)
    w('\nstrict differences  : %d\nadvisory differences: %d\n' % (len(s), len(v)))
    w('RESULT: %s\n' % ('MOTION CHANGED (strict signature differs)' if s else 'OK - motion signature identical'))
    return 1 if s else 0


def main(argv):
    try:
        sys.stdout.reconfigure(encoding='utf-8', newline='\n')
    except Exception:
        pass
    try:
        if len(argv) == 4 and argv[1] == '--compare':
            with open(argv[2], encoding='utf-8') as f1, open(argv[3], encoding='utf-8') as f2:
                return compare(json.load(f1), json.load(f2))
        if len(argv) == 4 and argv[1] == '--check':
            with open(argv[2], encoding='utf-8') as f1:
                return compare(json.load(f1), json.loads(dump(build(argv[3]))))
        if len(argv) in (2, 3) and not argv[1].startswith('--'):
            text = dump(build(argv[1]))
            if len(argv) == 3:
                with open(argv[2], 'w', encoding='utf-8', newline='\n') as f:
                    f.write(text)
            else:
                sys.stdout.write(text)
            return 0
    except (OSError, ValueError) as e:
        sys.stderr.write('error: %s\n' % e)
        return 2
    sys.stderr.write(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv))
