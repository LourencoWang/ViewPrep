"""SVG diagram generators in the house style: 440 wide, CSS-variable colours,
Arial labels, class card-diagram. Each returns an SVG string for a card's
`image` field."""
from html import escape as e

STYLE = """  <style>
    .lbl{font:600 10px Arial;fill:var(--ink-faint);text-transform:uppercase;letter-spacing:.04em;}
    .lbl-strong{font:700 11px Arial;fill:var(--ink);}
    .val{font:700 12px Arial;fill:var(--ink);}
    .cap{font:600 9.5px Arial;fill:var(--ink-soft);}
    .op{font:700 16px Arial;fill:var(--ink-faint);}
    .on{fill:var(--contrast);}
    .axis{stroke:var(--line);stroke-width:1;}
  </style>
"""
COL = {'blue': 'var(--blue)', 'amber': 'var(--amber)', 'green': 'var(--green)', 'ink': 'var(--ink)', 'faint': 'var(--ink-faint)', 'line': 'var(--line-soft)'}

def svg(h, body):
    return f'<svg viewBox="0 0 440 {h}" class="card-diagram" xmlns="http://www.w3.org/2000/svg">\n{STYLE}{body}</svg>'

def _c(name): return COL.get(name, name)

def formula(items, result, title=None):
    """items: [(label, colour), op, (label, colour), op, ...]; result: (label lines, colour)."""
    h = 110 if not title else 128
    y0 = 18 if title else 0
    out = ''
    if title: out += f'  <text x="0" y="14" class="lbl">{e(title)}</text>\n'
    boxes = [i for i in items if isinstance(i, tuple)]
    ops = [i for i in items if isinstance(i, str)]
    n = len(boxes) + 1
    gap = 14; opw = 18
    bw = (440 - (n - 1) * (gap + opw + gap)) / n
    x = 0
    for k, (lab, col) in enumerate(boxes):
        lines = lab.split('\n')
        out += f'  <rect x="{x:.0f}" y="{y0+28}" width="{bw:.0f}" height="46" rx="8" fill="var(--surface)" stroke="{_c(col)}" stroke-width="1.5"/>\n'
        for j, ln in enumerate(lines):
            yy = y0 + 28 + 23 + (j - (len(lines) - 1) / 2) * 13 + 4
            out += f'  <text x="{x+bw/2:.0f}" y="{yy:.0f}" text-anchor="middle" class="lbl-strong" style="font-size:10.5px">{e(ln)}</text>\n'
        x += bw + gap
        op = ops[k] if k < len(ops) else '='
        out += f'  <text x="{x+opw/2:.0f}" y="{y0+58}" text-anchor="middle" class="op">{e(op)}</text>\n'
        x += opw + gap
    rl, rc = result
    out += f'  <rect x="{x:.0f}" y="{y0+20}" width="{bw:.0f}" height="62" rx="8" fill="{_c(rc)}"/>\n'
    lines = rl.split('\n')
    for j, ln in enumerate(lines):
        yy = y0 + 20 + 31 + (j - (len(lines) - 1) / 2) * 13 + 4
        out += f'  <text x="{x+bw/2:.0f}" y="{yy:.0f}" text-anchor="middle" class="lbl-strong on" style="font-size:10.5px">{e(ln)}</text>\n'
    return svg(h, out)

def bars(groups, title=None, unit='', h=180):
    """groups: [(label, value, colour)]; values scaled to the max."""
    top = 30 if title else 18; base = h - 34; span = base - top - 14
    mx = max(v for _, v, _ in groups) or 1
    n = len(groups); slot = 440 / n; bw = min(56, slot * 0.5)
    out = f'  <text x="0" y="14" class="lbl">{e(title)}</text>\n' if title else ''
    out += f'  <line x1="0" y1="{base}" x2="440" y2="{base}" class="axis"/>\n'
    for i, (lab, v, col) in enumerate(groups):
        bh = span * v / mx; x = i * slot + (slot - bw) / 2; y = base - bh
        out += f'  <rect x="{x:.0f}" y="{y:.0f}" width="{bw:.0f}" height="{bh:.0f}" rx="4" fill="{_c(col)}"/>\n'
        out += f'  <text x="{x+bw/2:.0f}" y="{y-5:.0f}" text-anchor="middle" class="val">{e(str(v) + unit)}</text>\n'
        for j, ln in enumerate(lab.split('\n')):
            out += f'  <text x="{x+bw/2:.0f}" y="{base+14+j*11}" text-anchor="middle" class="lbl">{e(ln)}</text>\n'
    return svg(h, out)

def hbars(rows, title=None, unit='', h=None, mx=None):
    """rows: [(label, value, colour, note)] horizontal, label left, value right."""
    h = h or 24 + 30 * len(rows) + (16 if title else 0)
    top = 26 if title else 8
    mx = mx or max(abs(v) for _, v, _, _ in rows) or 1
    out = f'  <text x="0" y="14" class="lbl">{e(title)}</text>\n' if title else ''
    for i, (lab, v, col, note) in enumerate(rows):
        y = top + i * 30
        out += f'  <text x="0" y="{y+13}" class="lbl-strong" style="font-size:10px">{e(lab)}</text>\n'
        w = 220 * abs(v) / mx
        out += f'  <rect x="140" y="{y}" width="{w:.0f}" height="18" rx="4" fill="{_c(col)}"/>\n'
        out += f'  <text x="{140+w+6:.0f}" y="{y+13}" class="val">{e(str(v)+unit)}</text>\n'
        if note: out += f'  <text x="440" y="{y+13}" text-anchor="end" class="cap">{e(note)}</text>\n'
    return svg(h, out)

def flow(steps, title=None, colours=None, h=None):
    """steps: list of labels (\\n allowed); boxes joined by arrows, wraps to two rows if > 4."""
    rows = [steps] if len(steps) <= 4 else [steps[:len(steps)//2 + len(steps)%2], steps[len(steps)//2 + len(steps)%2:]]
    h = h or (20 if title else 0) + 70 * len(rows) + 10
    out = f'  <text x="0" y="14" class="lbl">{e(title)}</text>\n' if title else ''
    y0 = 24 if title else 6
    for r, row in enumerate(rows):
        n = len(row); aw = 22; bw = (440 - (n - 1) * aw) / n; y = y0 + r * 70
        for i, lab in enumerate(row):
            x = i * (bw + aw)
            col = (colours or ['blue', 'amber', 'green', 'ink'])[(r * 4 + i) % 4] if colours != 'plain' else 'line'
            out += f'  <rect x="{x:.0f}" y="{y}" width="{bw:.0f}" height="50" rx="8" fill="var(--surface)" stroke="{_c(col)}" stroke-width="1.5"/>\n'
            lines = lab.split('\n')
            for j, ln in enumerate(lines):
                yy = y + 25 + (j - (len(lines) - 1) / 2) * 12 + 4
                out += f'  <text x="{x+bw/2:.0f}" y="{yy:.0f}" text-anchor="middle" class="lbl-strong" style="font-size:10px">{e(ln)}</text>\n'
            if i < n - 1:
                ax = x + bw
                out += f'  <path d="M{ax+4:.0f} {y+25} L{ax+aw-6:.0f} {y+25} M{ax+aw-11:.0f} {y+20} L{ax+aw-6:.0f} {y+25} L{ax+aw-11:.0f} {y+30}" fill="none" stroke="var(--ink-faint)" stroke-width="1.5"/>\n'
    return svg(h, out)

def waterfall(start, steps, end, title=None, h=190):
    """start: (label, value); steps: [(label, delta, colour)]; end: (label, value)."""
    top = 30 if title else 16; base = h - 34
    vals = [start[1]]; run = start[1]
    for _, dl, _ in steps: run += dl; vals.append(run)
    vals.append(end[1]); mx = max(vals + [start[1], end[1]]) or 1
    sc = (base - top - 16) / mx
    n = len(steps) + 2; slot = 440 / n; bw = min(52, slot * 0.6)
    out = f'  <text x="0" y="14" class="lbl">{e(title)}</text>\n' if title else ''
    out += f'  <line x1="0" y1="{base}" x2="440" y2="{base}" class="axis"/>\n'
    def bar(i, y1, y2, col, lab, txt):
        x = i * slot + (slot - bw) / 2; y = base - max(y1, y2) * sc; hh = abs(y1 - y2) * sc
        s = f'  <rect x="{x:.0f}" y="{y:.0f}" width="{bw:.0f}" height="{max(hh,2):.0f}" rx="3" fill="{_c(col)}"/>\n'
        s += f'  <text x="{x+bw/2:.0f}" y="{y-5:.0f}" text-anchor="middle" class="val">{e(txt)}</text>\n'
        for j, ln in enumerate(lab.split('\n')):
            s += f'  <text x="{x+bw/2:.0f}" y="{base+14+j*11}" text-anchor="middle" class="lbl">{e(ln)}</text>\n'
        return s
    out += bar(0, 0, start[1], 'ink', start[0], str(start[1]))
    run = start[1]
    for i, (lab, dl, col) in enumerate(steps, 1):
        out += bar(i, run, run + dl, col, lab, ('+' if dl > 0 else '−') + str(abs(dl)))
        run += dl
    out += bar(n - 1, 0, end[1], 'ink', end[0], str(end[1]))
    return svg(h, out)

def table(headers, rows, title=None, widths=None, h=None):
    """Small grid. headers: list; rows: list of lists; first column bold."""
    n = len(rows) + 1; rh = 22
    h = h or (20 if title else 0) + n * rh + 14
    y0 = 22 if title else 6
    widths = widths or [440 / len(headers)] * len(headers)
    out = f'  <text x="0" y="14" class="lbl">{e(title)}</text>\n' if title else ''
    xs = [sum(widths[:i]) for i in range(len(widths))]
    out += f'  <rect x="0" y="{y0}" width="440" height="{rh}" rx="4" fill="var(--surface-strong)"/>\n'
    for i, hd in enumerate(headers):
        anchor = 'start' if i == 0 else 'middle'; x = xs[i] + 6 if i == 0 else xs[i] + widths[i] / 2
        out += f'  <text x="{x:.0f}" y="{y0+15}" text-anchor="{anchor}" class="lbl">{e(hd)}</text>\n'
    for r, row in enumerate(rows, 1):
        y = y0 + r * rh
        out += f'  <line x1="0" y1="{y+rh}" x2="440" y2="{y+rh}" class="axis"/>\n'
        for i, cell in enumerate(row):
            anchor = 'start' if i == 0 else 'middle'; x = xs[i] + 6 if i == 0 else xs[i] + widths[i] / 2
            cls = 'lbl-strong' if i == 0 else 'val'
            out += f'  <text x="{x:.0f}" y="{y+15}" text-anchor="{anchor}" class="{cls}" style="font-size:10.5px">{e(str(cell))}</text>\n'
    return svg(h, out)

def spectrum(left, right, markers, title=None, h=100):
    """A line with labelled ends and markers: [(label, position 0..1, colour)]."""
    y = 52 if title else 40
    out = f'  <text x="0" y="14" class="lbl">{e(title)}</text>\n' if title else ''
    out += f'  <line x1="20" y1="{y}" x2="420" y2="{y}" stroke="var(--line)" stroke-width="2"/>\n'
    out += f'  <text x="20" y="{y+26}" class="lbl">{e(left)}</text>\n  <text x="420" y="{y+26}" text-anchor="end" class="lbl">{e(right)}</text>\n'
    for lab, pos, col in markers:
        x = 20 + 400 * pos
        out += f'  <circle cx="{x:.0f}" cy="{y}" r="7" fill="{_c(col)}"/>\n  <text x="{x:.0f}" y="{y-14}" text-anchor="middle" class="lbl-strong" style="font-size:10px">{e(lab)}</text>\n'
    return svg(h, out)

def pyramid(levels, h=170):
    """levels: [(label, colour)] top to bottom, widening."""
    n = len(levels); lh = (h - 10) / n
    out = ''
    for i, (lab, col) in enumerate(levels):
        w = 120 + (320 - 120) * i / max(1, n - 1); x = (440 - w) / 2; y = 4 + i * lh
        out += f'  <rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{lh-6:.0f}" rx="6" fill="{_c(col)}"/>\n'
        out += f'  <text x="220" y="{y+lh/2+1:.0f}" text-anchor="middle" class="lbl-strong on" style="font-size:10.5px">{e(lab)}</text>\n'
    return svg(h, out)

def line(series, xlabels, title=None, h=180, ylab=None):
    """series: [(name, [values], colour)] on a shared axis."""
    top = 30 if title else 16; base = h - 30; left = 30; right = 430
    allv = [v for _, vs, _ in series for v in vs]; mx = max(allv) or 1; mn = min(0, min(allv))
    sc = (base - top - 10) / (mx - mn)
    out = f'  <text x="0" y="14" class="lbl">{e(title)}</text>\n' if title else ''
    out += f'  <line x1="{left}" y1="{base}" x2="{right}" y2="{base}" class="axis"/>\n  <line x1="{left}" y1="{top}" x2="{left}" y2="{base}" class="axis"/>\n'
    n = len(xlabels)
    for i, xl in enumerate(xlabels):
        x = left + (right - left) * i / max(1, n - 1)
        out += f'  <text x="{x:.0f}" y="{base+14}" text-anchor="middle" class="lbl">{e(xl)}</text>\n'
    for k, (name, vs, col) in enumerate(series):
        pts = ' '.join(f'{left + (right-left)*i/max(1,n-1):.0f},{base - (v-mn)*sc:.0f}' for i, v in enumerate(vs))
        out += f'  <polyline points="{pts}" fill="none" stroke="{_c(col)}" stroke-width="2.5" stroke-linejoin="round"/>\n'
        lx = right; ly = base - (vs[-1] - mn) * sc
        out += f'  <text x="{lx}" y="{ly-8:.0f}" text-anchor="end" class="lbl-strong" style="font-size:10px;fill:{_c(col)}">{e(name)}</text>\n'
    if ylab: out += f'  <text x="{left+4}" y="{top-4}" class="cap">{e(ylab)}</text>\n'
    return svg(h, out)

def split(left_title, left_lines, right_title, right_lines, lcol='blue', rcol='amber', h=None):
    """Two side-by-side panels of short lines."""
    n = max(len(left_lines), len(right_lines)); h = h or 40 + n * 16 + 12
    out = ''
    for x, t, lines, col in [(0, left_title, left_lines, lcol), (226, right_title, right_lines, rcol)]:
        out += f'  <rect x="{x}" y="4" width="214" height="{h-8}" rx="8" fill="var(--surface)" stroke="{_c(col)}" stroke-width="1.5"/>\n'
        out += f'  <text x="{x+12}" y="24" class="lbl-strong" style="fill:{_c(col)}">{e(t)}</text>\n'
        for j, ln in enumerate(lines):
            out += f'  <text x="{x+12}" y="{42+j*16}" class="cap" style="font-size:10px;fill:var(--ink)">{e(ln)}</text>\n'
    return svg(h, out)

def ranges(rows, lo, hi, title=None, unit='x', h=None):
    """Football-field style: rows [(label, from, to, colour)] on a shared scale lo..hi."""
    h = h or 30 + 30 * len(rows) + (16 if title else 0)
    top = 26 if title else 8; L, R = 130, 430
    out = f'  <text x="0" y="14" class="lbl">{e(title)}</text>\n' if title else ''
    for i, (lab, a, b, col) in enumerate(rows):
        y = top + i * 30
        x1 = L + (R - L) * (a - lo) / (hi - lo); x2 = L + (R - L) * (b - lo) / (hi - lo)
        out += f'  <text x="0" y="{y+13}" class="lbl-strong" style="font-size:10px">{e(lab)}</text>\n'
        out += f'  <line x1="{L}" y1="{y+9}" x2="{R}" y2="{y+9}" class="axis"/>\n'
        out += f'  <rect x="{x1:.0f}" y="{y}" width="{max(x2-x1,3):.0f}" height="18" rx="4" fill="{_c(col)}"/>\n'
        out += f'  <text x="{x1-4:.0f}" y="{y+13}" text-anchor="end" class="cap">{a}{unit}</text>\n  <text x="{x2+4:.0f}" y="{y+13}" class="cap">{b}{unit}</text>\n'
    return svg(h, out)

def truncated_axis():
    out = ''
    for px, start, title in [(0, 90, 'Axis starts at 90'), (226, 0, 'Axis starts at 0')]:
        out += f'  <text x="{px}" y="14" class="lbl">{title}</text>\n'
        base = 150; top = 30; span = base - top
        for i, (lab, v, col) in enumerate([('Last year', 92, 'blue'), ('This year', 95, 'amber')]):
            frac = (v - start) / (100 - start); bh = span * frac; x = px + 30 + i * 90
            out += f'  <rect x="{x}" y="{base-bh:.0f}" width="60" height="{bh:.0f}" rx="4" fill="{_c(col)}"/>\n'
            out += f'  <text x="{x+30}" y="{base-bh-5:.0f}" text-anchor="middle" class="val">{v}</text>\n'
            out += f'  <text x="{x+30}" y="{base+14}" text-anchor="middle" class="lbl">{lab}</text>\n'
        out += f'  <line x1="{px+20}" y1="{base}" x2="{px+214}" y2="{base}" class="axis"/>\n'
    return svg(170, out)

def scatter():
    import random
    r = random.Random(7); out = '  <text x="0" y="14" class="lbl">Staff per store vs sales, one dot per store</text>\n'
    L, R, T, B = 30, 430, 26, 150
    out += f'  <line x1="{L}" y1="{B}" x2="{R}" y2="{B}" class="axis"/>\n  <line x1="{L}" y1="{T}" x2="{L}" y2="{B}" class="axis"/>\n'
    for i in range(16):
        x = L + 20 + i * 23 + r.randint(-6, 6); y = B - 15 - i * 6.5 + r.randint(-14, 14)
        out += f'  <circle cx="{x:.0f}" cy="{y:.0f}" r="4.5" fill="var(--blue)" style="opacity:.8"/>\n'
    out += f'  <line x1="{L+15}" y1="{B-12}" x2="{R-10}" y2="{B-15-15*6.5}" stroke="var(--amber)" stroke-width="2" stroke-dasharray="6 4"/>\n'
    out += f'  <text x="{L+4}" y="{T-2}" class="cap">Sales</text>\n  <text x="{R}" y="{B+14}" text-anchor="end" class="lbl">Staff</text>\n'
    out += f'  <text x="{R-8}" y="{T+16}" text-anchor="end" class="lbl-strong" style="font-size:10px;fill:var(--amber)">Correlation. Not proof of cause.</text>\n'
    return svg(170, out)
