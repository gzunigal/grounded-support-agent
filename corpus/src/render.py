import re, sys, html
src = open(sys.argv[1]).read().split('---', 2)[2]  # drop front matter
flyer = len(sys.argv) > 2
out, table, lst = [], [], None
def inline(t):
    t = html.escape(t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    return t
def flush_table():
    global table
    if not table: return
    rows = [r.strip('|').split('|') for r in table if not re.match(r'^\|[-| ]+\|$', r)]
    h = '<tr>' + ''.join(f'<th>{inline(c.strip())}</th>' for c in rows[0]) + '</tr>'
    b = ''.join('<tr>' + ''.join(f'<td>{inline(c.strip())}</td>' for c in r) + '</tr>' for r in rows[1:])
    out.append(f'<table>{h}{b}</table>'); table = []
para = []
def flush_para():
    global para
    if para: out.append('<p>' + inline(' '.join(para)) + '</p>'); para = []
for line in src.splitlines():
    if line.startswith('|'): flush_para(); table.append(line); continue
    flush_table()
    m = re.match(r'^(#+) (.*)', line)
    if m: flush_para(); out.append(f'<h{len(m[1])}>{inline(m[2])}</h{len(m[1])}>'); continue
    m = re.match(r'^(\d+\.|-) (.*)', line)
    if m:
        flush_para(); tag = 'ol' if m[1][0].isdigit() else 'ul'
        if lst != tag: out.append(f'<{tag}>'); lst = tag
        out.append(f'<li>{inline(m[2])}</li>'); continue
    if lst: out.append(f'</{lst}>'); lst = None
    if line.strip(): para.append(line.strip())
    else: flush_para()
flush_para(); flush_table()
if lst: out.append(f'</{lst}>')
css = """body{font-family:Helvetica,Arial,sans-serif;margin:40px;color:#222;line-height:1.5}
h1{font-size:26px;border-bottom:2px solid #444;padding-bottom:6px}h2{font-size:18px;margin-top:22px;break-after:avoid}
table{border-collapse:collapse;margin:10px 0}th,td{border:1px solid #888;padding:6px 10px;text-align:left}th{background:#eee}"""
if flyer: css += """body{margin:0;width:1080px;background:#1b1f3a;color:#f4f4f4;padding:50px;box-sizing:border-box}
h1{font-size:40px;color:#ffd166;border-color:#ffd166}h2{font-size:26px;color:#ffd166}
th,td{border-color:#ccc}th{background:#2e3460}b{color:#ffd166}li,p{font-size:21px}"""
print(f'<!doctype html><meta charset="utf-8"><style>{css}</style>' + '\n'.join(out))
