"""Compare the KiCad netlist with the Eagle v1 board (eagle_brd_nets.txt). Power input, LED, supply caps and pads
are excluded on purpose (redesigned in house style); everything in the signal path must match."""
import re, sys
MAP = {'GAIN': 'RV1', 'VOL': 'RV2'}
QPAD = {'1': '3', '2': '1', '3': '2'}          # Eagle 2N5089 pads C,B,E -> SOT-23 symbol pins
DPAD = {'A': '2', 'C': '1'}
EPAD = {'+': '1', '-': '2'}
SKIP = re.compile(r'^(IN|OUT|IG|OG|SG|SW|V\+|V-|RLED|R16|D4|D5|C10|C11|J\d+)$')
NONPOL = re.compile(r'^(R\d+|C\d+)$')
def eag(ref, pad):
    r = MAP.get(ref, ref)
    if ref.startswith('Q'): pad = QPAD[pad]
    elif ref.startswith('D'): pad = DPAD.get(pad, pad)
    elif ref in ('C7', 'C8', 'C9'): pad = EPAD.get(pad, pad)
    return r, pad
def norm(nets):
    out = []
    for n in nets:
        n = frozenset((r, '*' if NONPOL.match(r) else p) for r, p in n if not SKIP.match(r))
        if len(n) > 1: out.append(tuple(sorted(n)))
    return sorted(out)
E_ = []
for l in open(sys.argv[1]):
    q = l.split()
    if len(q) < 2 or "('" in l: continue
    E_.append([eag(*x.rsplit('.', 1)) for x in q[1:]])
K_ = [re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"', b) for b in re.split(r'\(net\s*\(code', open(sys.argv[2]).read())[1:]]
a, b = norm(E_), norm(K_)
print('signal path matches Eagle v1:', a == b)
for x in a:
    if x not in b: print(' eagle only:', x)
for x in b:
    if x not in a: print(' kicad only:', x)
