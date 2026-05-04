#!/usr/bin/env python3
"""OPEncode Token Dashboard — twilight theme + braille / eighth-block visuals"""
import sqlite3, sys, os, re

DB_PATH = os.environ.get("OPENCODE_DB", os.path.expanduser("~/.local/share/opencode/opencode.db"))
ANSI_ENABLED = sys.stdout.isatty() or "FORCE_COLOR" in os.environ

# ── twilight color palette (truecolor ANSI) ──────────────────────

def tcf(r, g, b):
    """truecolor foreground: \033[38;2;R;G;Bm"""
    return f"\033[38;2;{r};{g};{b}m"

def tcb(r, g, b):
    """truecolor background: \033[48;2;R;G;Bm"""
    return f"\033[48;2;{r};{g};{b}m"

C = {
    "RST": "\033[0m", "BOLD": "\033[1m", "DIM": "\033[2m",
    # Twilight accent colours
    "FG":   tcf(200, 184, 152),  # #c8b898  warm beige (primary text)
    "A0":   tcf(117, 135, 166),  # #7587a6  twilight blue
    "A1":   tcf(175, 216, 216),  # #afd8d8  sky cyan
    "A2":   tcf(143, 157, 106),  # #8f9d6a  olive green
    "A3":   tcf(212, 184, 114),  # #d4b872  warm gold
    "A4":   tcf(207, 106, 76),   # #cf6a4c  sunset orange
    "A5":   tcf(204, 102, 102),  # #cc6666  twilight rose
    # Braille spectrum (5-step, mapped to twilight)
    "B0":   tcf(100, 120, 155),  # indigo   (coldest)
    "B1":   tcf(130, 160, 175),  # steel
    "B2":   tcf(160, 175, 135),  # sage
    "B3":   tcf(200, 175, 115),  # wheat
    "B4":   tcf(210, 135, 85),   # copper
    "B5":   tcf(210, 105, 95),   # rose    (hottest)
    # Borders & accents
    "BDR":  tcf(75, 80, 90),     # #4b505a  dim border
    "ACC":  tcf(155, 133, 157),  # #9b859d  purple dusk accent
    "DIM":  tcf(150, 145, 135),  # #969187  dim text (twilight warm gray)
    "PIPE": tcf(120, 115, 108),  # #78736c  pipe grid lines
    # Gauge-specific
    "G1":   tcf(160, 185, 155),  # muted green
    "G2":   tcf(215, 190, 120),  # muted gold
    "G3":   tcf(135, 155, 185),  # muted blue
}

ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')
W = 78
CONTENT_W = W - 6

def c(code):
    return C.get(code, "") if ANSI_ENABLED else ""

def vlen(s):
    return len(ANSI_RE.sub('', s))

# ── alignment-safe helpers ─────────────────────────────────────

def fit(text, width, align='l'):
    text = str(text)
    v = vlen(text)
    if v <= width:
        return text.ljust(width) if align == 'l' else text.rjust(width)
    if width <= 2:
        return text[:width]
    return text[:width - 2] + '..'

def center_text(text, width=CONTENT_W):
    v = vlen(text)
    if v > width:
        return text[:width - 2] + '..'
    if v >= width:
        return text
    pad = (width - v) // 2
    return ' ' * pad + text + ' ' * (width - v - pad)

def build_line(parts, width=CONTENT_W):
    result = []
    visible = 0
    for text, color in parts:
        if color:
            result.append(c(color))
        result.append(text)
        if color:
            result.append(c('RST'))
        visible += vlen(text)
    if visible < width:
        result.append(' ' * (width - visible))
    return ''.join(result)

def hline(left, fill, right, color):
    inner = fill * (W - 4)
    return f"  {c(color)}{left}{inner}{right}{c('RST')}"

# ── formatters (all guaranteed fixed-width) ────────────────────

def fmt_tokens(n):
    if n is None: return "    0"
    n = int(n)
    if n >= 1_000_000_000: return f"{n/1_000_000_000:4.0f}B"[:5]
    if n >= 1_000_000: return f"{n/1_000_000:4.0f}M".rjust(5)
    if n >= 1_000: return f"{n/1_000:4.0f}K"
    return f"{n:5d}"

def fmt_cost(cst):
    if cst is None or cst == 0:
        return "free  "
    s = f"${cst:.2f}"
    if len(s) > 6: s = f"${cst:.1f}"
    if len(s) > 6: s = f"${cst:.0f}"
    if len(s) > 6: s = f"${cst/1000:.1f}K"
    if len(s) > 6: s = f"${cst/1_000_000:.1f}M"
    return s.ljust(6)

def fmt_pct(val, total):
    if total == 0: return "   -"
    pct = val / total * 100
    if pct >= 99.95: return " 100%"
    return f"{pct:4.1f}%"

# ── novel visual components (no bar charts!) ────────────────────

# Braille density characters (9 levels, bottom-to-top fill)
BRAILLE_LEVELS = ['⠀','⡀','⡄','⡆','⡇','⣇','⣧','⣷','⣿']
BRAILLE_COLORS = ['B0', 'B1', 'B2', 'B3', 'B4', 'B5']

def braille_wave(value, max_val, width):
    """Braille dot-matrix wave — 8-level fill per character, color gradient."""
    if max_val == 0 or width == 0:
        return ' ' * width
    pct = min(value / max_val, 1.0)
    total_levels = width * 8
    filled = max(1, int(pct * total_levels))

    result = []
    for i in range(width):
        remaining = filled - i * 8
        if remaining <= 0:
            level = 0
        elif remaining >= 8:
            level = 8
        else:
            level = remaining
        # Color from position along bar (cold → hot)
        ci = min(int(i / width * len(BRAILLE_COLORS)), len(BRAILLE_COLORS) - 1)
        result.append(c(BRAILLE_COLORS[ci]) + BRAILLE_LEVELS[level] + c('RST'))
    return ''.join(result)

# Left-eighth blocks for finer resolution
EIGHTHS = [' ', '▏', '▎', '▍', '▌', '▋', '▊', '▉', '█']
EIGHTH_COLORS = ['B0', 'B1', 'B2', 'B3', 'B4', 'B5']

def eighth_bar(value, max_val, width):
    """Left-eighth block density bar — 8× resolution of full blocks, color per column."""
    if max_val == 0 or width == 0:
        return ' ' * width
    pct = min(value / max_val, 1.0)
    total_units = width * 8
    filled = max(1, int(pct * total_units))

    result = []
    for i in range(width):
        remaining = filled - i * 8
        if remaining <= 0:
            el = 0
        elif remaining >= 8:
            el = 8
        else:
            el = remaining
        ci = min(int(i / width * len(EIGHTH_COLORS)), len(EIGHTH_COLORS) - 1)
        result.append(c(EIGHTH_COLORS[ci]) + EIGHTHS[el] + c('RST'))
    return ''.join(result)

# Circle-dot gauge (replaces gauge_bar)
CIRCLE_LEVELS = ['○', '◌', '◍', '◎', '●']

def circle_gauge(value, max_val, count, label, color):
    """Mini circle-dot indicator row: ●●●◌○○ label pct%"""
    if max_val == 0:
        pct = 0
        filled = 0
    else:
        pct = value / max_val
        filled = int(pct * count)
    dots = c(color) + '●' * filled + c('DIM') + '○' * (count - filled) + c('RST')
    pct_str = f"{pct*100:4.1f}%"
    return f"  {dots}  {label}  {pct_str}"

# ── database ───────────────────────────────────────────────────

def query_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT date(time_created/1000, 'unixepoch') as day,
               COUNT(*) as cnt,
               SUM(CAST(json_extract(data, '$.tokens.total') AS INTEGER)) as total,
               SUM(CAST(json_extract(data, '$.tokens.input') AS INTEGER)) as input_t,
               SUM(CAST(json_extract(data, '$.tokens.output') AS INTEGER)) as output_t,
               SUM(CAST(json_extract(data, '$.tokens.cache.read') AS INTEGER)) as cache_read,
               SUM(CAST(json_extract(data, '$.cost') AS REAL)) as cost
        FROM message 
        WHERE json_extract(data, '$.tokens') IS NOT NULL
        AND json_extract(data, '$.role') = 'assistant'
        GROUP BY day ORDER BY day
    """)
    trends = [dict(r) for r in cur.fetchall()]

    cur.execute("""
        SELECT COALESCE(json_extract(data, '$.providerID'),'?') || '/' || 
               COALESCE(json_extract(data, '$.modelID'),'?') as model,
               COUNT(*) as cnt,
               SUM(CAST(json_extract(data, '$.tokens.total') AS INTEGER)) as total,
               SUM(CAST(json_extract(data, '$.cost') AS REAL)) as cost
        FROM message 
        WHERE json_extract(data, '$.tokens') IS NOT NULL
        AND json_extract(data, '$.role') = 'assistant'
        GROUP BY model ORDER BY total DESC
    """)
    models = [dict(r) for r in cur.fetchall()]

    conn.close()
    return trends, models

# ── render ─────────────────────────────────────────────────────

def render(trends, models):
    lines = []
    total_tokens = sum(t['total'] or 0 for t in trends)
    total_cost = sum(t['cost'] or 0 for t in trends)
    total_msgs = sum(t['cnt'] for t in trends)
    total_input = sum(t['input_t'] or 0 for t in trends)
    total_output = sum(t['output_t'] or 0 for t in trends)
    total_cache = sum(t['cache_read'] or 0 for t in trends)
    total_days = len(trends)
    io_total = total_input + total_output + total_cache

    # ════════════ 1. HEADER + COMPOSITION ════════════
    lines.append("")
    lines.append(hline('╭', '─', '╮', 'BDR'))

    # Title
    title = center_text('OP  encode  ·  token  dashboard')
    lines.append(f"  {c('BDR')}│{c('RST')} {c('A0')}{c('BOLD')}{title}{c('RST')} {c('BDR')}│{c('RST')}")

    # Summary
    sum_text = f"{fmt_tokens(total_tokens)}  ·  ${total_cost:.2f}  ·  {total_days}d  ·  {total_msgs} calls"
    centered = center_text(sum_text)
    lines.append(f"  {c('BDR')}│{c('RST')} {c('FG')}{centered}{c('RST')} {c('BDR')}│{c('RST')}")

    # IO composition gauges
    sep = build_line([('─' * CONTENT_W, 'DIM')])
    lines.append(f"  {c('BDR')}│{c('RST')} {sep} {c('BDR')}│{c('RST')}")
    if io_total > 0:
        for label, val, clr in [('input ', total_input, 'G1'), ('output', total_output, 'G2'), ('cache ', total_cache, 'G3')]:
            g = circle_gauge(val, io_total, 20, label, clr)
            gpad = ' ' * max(0, CONTENT_W - vlen(g))
            lines.append(f"  {c('BDR')}│{c('RST')} {g}{gpad} {c('BDR')}│{c('RST')}")
    lines.append(hline('╰', '─', '╯', 'BDR'))
    lines.append("")

    # ════════════ 2. CALENDAR HEATMAP ════════════
    lines.append(hline('╭', '─', '╮', 'BDR'))
    label = build_line([(' calendar heatmap ', 'DIM')])
    lines.append(f"  {c('BDR')}│{c('RST')} {label} {c('BDR')}│{c('RST')}")
    lines.append(f"  {c('BDR')}│{c('RST')} {build_line([('─' * CONTENT_W, 'DIM')])} {c('BDR')}│{c('RST')}")

    if trends:
        from datetime import date, timedelta
        day_map = {}
        max_t = max(t['total'] or 0 for t in trends)
        for t in trends:
            day_map[t['day']] = {
                'total': t['total'] or 0,
                'input': t.get('input_t') or 0,
                'output': t.get('output_t') or 0,
                'cache': t.get('cache_read') or 0,
            }

        # Smooth color: interpolate between 6 twilight stops
        STOPS = [
            (100, 120, 155),   # B0 indigo
            (130, 160, 175),   # B1 steel
            (160, 175, 135),   # B2 sage
            (200, 175, 115),   # B3 wheat
            (210, 135, 85),    # B4 copper
            (210, 105, 95),    # B5 rose
        ]
        def heat_color(pct):
            """Return tcf(r,g,b) for a percentage [0.0, 1.0]."""
            p = min(max(pct, 0.0), 1.0)
            f = p * (len(STOPS) - 1)
            i = int(f)
            t = f - i
            if i >= len(STOPS) - 1:
                r, g, b = STOPS[-1]
            else:
                r0, g0, b0 = STOPS[i]
                r1, g1, b1 = STOPS[i + 1]
                r = int(r0 + (r1 - r0) * t)
                g = int(g0 + (g1 - g0) * t)
                b = int(b0 + (b1 - b0) * t)
            return tcf(r, g, b)

        # Mahjong circle tiles: 🀙🀚🀛🀜🀝🀞 — natural 1→6 dot density progression
        symbols = ['🀙', '🀚', '🀛', '🀜', '🀝', '🀞']

        all_dates = sorted(day_map.keys())
        if all_dates:
            start = date.fromisoformat(all_dates[0])
            end = date.fromisoformat(all_dates[-1])
            start -= timedelta(days=start.weekday())
            end += timedelta(days=6 - end.weekday())

            weeks = []
            cur = start
            while cur <= end:
                weeks.append(cur)
                cur += timedelta(days=7)

            # Transposed: column headers = Mon-Sun
            day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            hdr_parts = [('       ', 'DIM')]
            for dn in day_names:
                hdr_parts.append((f' {dn} ', 'DIM'))
            lines.append(f"  {c('BDR')}│{c('RST')} {build_line(hdr_parts)} {c('BDR')}│{c('RST')}")
            lines.append(f"  {c('BDR')}│{c('RST')} {build_line([('─' * CONTENT_W, 'DIM')])} {c('BDR')}│{c('RST')}")

            # Collect which dice levels actually appear
            used_levels = set()
            week_totals = []

            # Fixed widths for sparkline + number column
            SPARK_COL_W = 10  # " ▃  48M"
            LEFT_FIXED_W = 8 + 7 * 6  # date(" Apr 20 ") + 7 days(6 each) = 50
            SPARK_PAD = CONTENT_W - LEFT_FIXED_W - SPARK_COL_W  # 72-50-10 = 12

            # Each row = one week
            for w in weeks:
                row_parts = [(f' {w.strftime("%b %d")} ', 'A0')]
                week_sum = 0
                for di in range(7):
                    d = w + timedelta(days=di)
                    if d < date.fromisoformat(all_dates[0]) or d > date.fromisoformat(all_dates[-1]):
                        row_parts.append(('      ', None))
                    elif d.isoformat() not in day_map or day_map[d.isoformat()]['total'] == 0:
                        row_parts.append((f' {c("DIM")}·{c("RST")}    ', None))
                    else:
                        val = day_map[d.isoformat()]['total']
                        week_sum += val
                        pct = min(val / max_t, 1.0)
                        level = min(int(pct * 6), 5)
                        used_levels.add(level)
                        color = heat_color(pct)
                        row_parts.append((f' {color}{symbols[level]}{c("RST")}   ', None))
                # Build left side (fixed 50w)
                left_line = build_line(row_parts, width=LEFT_FIXED_W)
                # Build right side: sparkline + week total
                if week_sum > 0:
                    w_pct = week_sum / (max_t * 7) if max_t > 0 else 0
                    w_bar = '▁▂▃▄▅▆▇█'
                    w_level = min(int(w_pct * 8), 7)
                    w_sym = w_bar[w_level]
                    w_color = heat_color(min(w_pct * 7, 1.0))
                    week_str = fmt_tokens(week_sum)
                    right_text = f'{w_color}{w_sym}{c("RST")}  {week_str}'
                else:
                    right_text = ''
                right_vlen = vlen(right_text)
                # Ensure right side fits in SPARK_COL_W
                if right_vlen > SPARK_COL_W:
                    week_str = week_str[:max(1, SPARK_COL_W - 3)]
                    right_text = f'{w_color}{w_sym}{c("RST")}  {week_str}'
                    right_vlen = vlen(right_text)
                # Spacer pushes sparkline to the right edge
                spacer = ' ' * (CONTENT_W - LEFT_FIXED_W - right_vlen)
                full_line = left_line + spacer + right_text
                week_totals.append(week_sum)
                lines.append(f"  {c('BDR')}│{c('RST')} {full_line} {c('BDR')}│{c('RST')}")

            # ── Compact spectrum legend bar (48w + pad to 72w) ──
            bar_w = 48

            # 1. The gradient bar
            spectrum_parts = []
            for i in range(bar_w):
                color = heat_color(i / (bar_w - 1))
                spectrum_parts.append((f'{color}▮{c("RST")}', None))
            # Pad right to CONTENT_W
            spectrum_parts.append((' ' * (CONTENT_W - bar_w), None))
            spectrum_line = build_line(spectrum_parts)
            lines.append(f"  {c('BDR')}│{c('RST')} {spectrum_line} {c('BDR')}│{c('RST')}")

            # 2. Annotations beneath
            if max_t > 0:
                labels = {}
                for i in range(6):
                    th = int(max_t * i / 5)
                    if th >= 1_000_000:
                        th_str = f'{th/1_000_000:.0f}M'
                    elif th >= 1_000:
                        th_str = f'{th/1_000:.0f}K'
                    else:
                        th_str = str(th)
                    labels[i] = f'{symbols[i]} {th_str}'

                display_levels = sorted(set(list(used_levels) + [0, 5]))

                annotations = []
                for lvl in display_levels:
                    pos = int(bar_w * lvl / 5)
                    if lvl == 5:
                        pos = bar_w - 1
                    text = labels[lvl]
                    text_len = len(text)
                    text_start = max(0, pos - text_len // 2)
                    if text_start + text_len > bar_w:
                        text_start = bar_w - text_len
                    text_start = max(0, text_start)
                    annotations.append({
                        'pos': pos,
                        'text': text,
                        'text_start': text_start,
                        'text_end': text_start + text_len,
                        'row': 1,
                    })

                # Resolve overlaps
                for i in range(len(annotations)):
                    for j in range(i + 1, len(annotations)):
                        a, b = annotations[i], annotations[j]
                        overlap = max(a['text_start'], b['text_start']) < min(a['text_end'], b['text_end'])
                        if overlap and b['row'] == a['row']:
                            b['row'] = 1 - b['row']

                # Build annotation rows (48w, then pad to 72w)
                row1 = [' '] * bar_w
                row2 = [' '] * bar_w

                for ann in annotations:
                    pos = ann['pos']
                    text = ann['text']
                    start = ann['text_start']

                    if ann['row'] == 1:
                        row1[pos] = '↓'
                        for k, ch in enumerate(text):
                            if start + k < bar_w:
                                row2[start + k] = ch
                    else:
                        for k, ch in enumerate(text):
                            if start + k < bar_w:
                                row1[start + k] = ch
                        row2[pos] = '↑'

                # Pad to CONTENT_W and output
                r1_padded = ''.join(row1) + ' ' * (CONTENT_W - bar_w)
                r2_padded = ''.join(row2) + ' ' * (CONTENT_W - bar_w)
                lines.append(f"  {c('BDR')}│{c('RST')} {r1_padded} {c('BDR')}│{c('RST')}")
                lines.append(f"  {c('BDR')}│{c('RST')} {r2_padded} {c('BDR')}│{c('RST')}")

            # ── Daily breakdown (last 5 active days) ──
            active_days = [(d, day_map[d]) for d in all_dates if day_map[d]['total'] > 0]
            recent_days = active_days[-5:]  # last 5
            if recent_days:
                lines.append(f"  {c('BDR')}│{c('RST')} {build_line([('─' * CONTENT_W, 'DIM')])} {c('BDR')}│{c('RST')}")
                title = build_line([(' daily breakdown (last 5 active) ', 'DIM')])
                lines.append(f"  {c('BDR')}│{c('RST')} {title} {c('BDR')}│{c('RST')}")
                lines.append(f"  {c('BDR')}│{c('RST')} {build_line([('─' * CONTENT_W, 'DIM')])} {c('BDR')}│{c('RST')}")
                # Legend for daily breakdown
                legend = build_line([
                    (' ', None),
                    (f'{c("G1")}→{c("RST")} input  ', None),
                    (f'{c("G2")}←{c("RST")} output  ', None),
                    (f'{c("G3")}⛁{c("RST")} cache  ', None),
                    (f'{c("DIM")}─{c("RST")} total', None),
                ])
                lines.append(f"  {c('BDR')}│{c('RST')} {legend} {c('BDR')}│{c('RST')}")
                lines.append(f"  {c('BDR')}│{c('RST')} {build_line([('─' * CONTENT_W, 'DIM')])} {c('BDR')}│{c('RST')}")

                for d_str, data in recent_days:
                    d_obj = date.fromisoformat(d_str)
                    date_label = d_obj.strftime('%b %d')
                    inp = data['input']
                    out = data['output']
                    cache = data['cache']
                    tot = data['total']

                    detail = build_line([
                        (f' {date_label}  ', 'A0'),
                        (f'{c("G1")}→{c("RST")} ', None),
                        (fit(fmt_tokens(inp), 6, 'r'), None),
                        ('   ', None),
                        (f'{c("G2")}←{c("RST")} ', None),
                        (fit(fmt_tokens(out), 6, 'r'), None),
                        ('   ', None),
                        (f'{c("G3")}⛁{c("RST")} ', None),
                        (fit(fmt_tokens(cache), 6, 'r'), None),
                        ('   ', None),
                        (f'{c("DIM")}─{c("RST")} ', None),
                        (fit(fmt_tokens(tot), 7, 'r'), 'BOLD'),
                    ])
                    lines.append(f"  {c('BDR')}│{c('RST')} {detail} {c('BDR')}│{c('RST')}")

    lines.append(hline('╰', '─', '╯', 'BDR'))
    lines.append("")

    # ════════════ 3. MODEL DISTRIBUTION ════════════
    lines.append(hline('╭', '─', '╮', 'BDR'))
    label = build_line([(' model distribution ', 'DIM')])
    lines.append(f"  {c('BDR')}│{c('RST')} {label} {c('BDR')}│{c('RST')}")
    lines.append(f"  {c('BDR')}│{c('RST')} {build_line([('─' * CONTENT_W, 'DIM')])} {c('BDR')}│{c('RST')}")

    max_m = max(m['total'] or 0 for m in models) if models else 0
    NAME_W = 28
    BAR_W = 23

    hdr = build_line([
        (fit('model', NAME_W), 'DIM'), (' ', None),
        (fit('eighth-bar', BAR_W, 'l'), 'DIM'), (' ', None),
        (fit('tokens', 6, 'r'), 'DIM'), (' ', None),
        (fit('pct', 5, 'r'), 'DIM'), (' ', None),
        (fit('cost', 6, 'r'), 'DIM'),
    ])
    lines.append(f"  {c('BDR')}│{c('RST')} {hdr} {c('BDR')}│{c('RST')}")
    lines.append(f"  {c('BDR')}│{c('RST')} {build_line([('─' * CONTENT_W, 'DIM')])} {c('BDR')}│{c('RST')}")

    for m in models[:10]:
        name = m['model']
        total = m['total'] or 0
        pct = fmt_pct(total, total_tokens)
        cost_str = fmt_cost(m['cost'])
        eb = eighth_bar(total, max_m, BAR_W)
        line = build_line([
            (fit(name, NAME_W), 'FG'), (' ', None),
            (eb, None), (' ', None),
            (fit(fmt_tokens(total), 6, 'r'), None), (' ', None),
            (fit(pct, 5, 'r'), 'BOLD'), (' ', None),
            (fit(cost_str, 6), 'A3'),
        ])
        lines.append(f"  {c('BDR')}│{c('RST')} {line} {c('BDR')}│{c('RST')}")
    lines.append(hline('╰', '─', '╯', 'BDR'))
    lines.append("")

    footer = f"opencode db @ {DB_PATH}"
    lines.append(f"  {c('DIM')}{footer}{' ' * (76 - vlen(footer))}{c('RST')}")
    lines.append("")

    return "\n".join(lines)

# ── main ───────────────────────────────────────────────────────

def main():
    trends, models = query_db()
    print(render(trends, models))

if __name__ == "__main__":
    main()
