"""Fix mojibake encoding in WAF dashboard template."""
path = r'e:\Datasets\templates\waf\dashboard.html'

with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Each mojibake sequence: UTF-8 bytes misread as Latin-1/Win-1252
replacements = [
    ('\u00e2\u20ac\u201c', '\u2014'),     # â€" -> — (em dash)
    ('\u00e2\u20ac\u00a6', '\u2026'),     # â€¦ -> … (ellipsis)
    ('\u00f0\u009f\u0094\u2019', '\U0001F512'),  # ðŸ"' -> 🔒
    ('\u00f0\u009f\u0094\u00b4', '\U0001F534'),  # ðŸ"´ -> 🔴
    ('\u00f0\u009f\u009a\u00ab', '\U0001F6AB'),  # ðŸš« -> 🚫
    ('\u00f0\u009f\u0094\u00a5', '\U0001F525'),  # ðŸ"¥ -> 🔥
    ('\u00e2\u0153\u00bf\u00ef\u00b8\u008f', '\u2699\ufe0f'),  # âš™ï¸ -> ⚙️
    ('\u00e2\u0094\u0080', '\u2500'),     # â"€ -> ─
    ('\u00c3\u00b3', '\u00f3'),           # Ã³ -> ó
    ('\u00c3\u00ad', '\u00ed'),           # Ã­ -> í
    ('\u00c3\u00ba', '\u00fa'),           # Ãº -> ú
    ('\u00c3\u00a9', '\u00e9'),           # Ã© -> é
    ('\u00c3\u00bc', '\u00fc'),           # Ã¼ -> ü
    ('\u00c2\u00bf', '\u00bf'),           # Â¿ -> ¿
    ('\u00c3\u00a1', '\u00e1'),           # Ã¡ -> á
    ('\u00c3\u00b1', '\u00f1'),           # Ã± -> ñ
    ('\u00c3\u00b2', '\u00f2'),           # Ã² -> ò
]

before = len([c for c in content if ord(c) > 0xC0 and ord(c) < 0xF0])
for bad, good in replacements:
    content = content.replace(bad, good)
after = len([c for c in content if ord(c) > 0xC0 and ord(c) < 0xF0])

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Done. Suspect chars reduced: {before} -> {after}")
# Show some samples
import re
samples = re.findall(r'.{0,20}[🔒🔴🚫🔥⚙—…].{0,20}', content)
for s in samples[:5]:
    print(' >', repr(s))
