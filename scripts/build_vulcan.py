"""Vulcan SMD v2 - clean SMD redraw of the Eagle "Vulcan v1 OSHPark" build (the reference that sounds good).
Electrically faithful to Eagle v1 (same refs/values), SMD parts, house-style power / LED / header.
usage: build_vulcan.py <out.kicad_sch>"""
from sch import *
import sys
OUT = sys.argv[1]
g = lambda n: round(n * 2.54, 3)
s = Sheet('Vulcan', 'A3')
FR = 'Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder'
FC = 'Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder'
FC12 = 'Capacitor_SMD:C_1206_3216Metric_Pad1.33x1.80mm_HandSolder'
FPOT = 'UglyFace:Potentiometer_Alpha_16mm_Vertical'
FPAD = 'Connector_Wire:SolderWire-0.5sqmm_1x01_D0.9mm_OD2.1mm'
RL = {'4M7': 'C17674', '1M': 'C17514', '470k': 'C17709', '10k': 'C17414', '4k7': 'C17673', '1k': 'C17513'}
CL = {'100n': 'C49678', '2n2': 'C28260', '22u': 'C12891'}
W = lambda *p: s.wire(*p)
P = s.P
def GND(p): s.power('GND', p)
def V9(p): s.power('+9V', p)
def lab(n, p, side='r'): s.label(n, p, side)
def Rh(ref, v, cx, y, desc=None): s.part(ref, 'Device', 'R', v, cx, y, 90, fp=FR, lcsc=RL[v], desc=desc or f'Resistor {v} 1% 0805', text='t')
def Rv(ref, v, x, cy, side='r', desc=None): s.part(ref, 'Device', 'R', v, x, cy, 0, fp=FR, lcsc=RL[v], desc=desc or f'Resistor {v} 1% 0805', text=side)
def fpc(v): return FC12 if v == '22u' else FC
def Ch(ref, v, cx, y, desc=None): s.part(ref, 'Device', 'C', v, cx, y, 90, fp=fpc(v), lcsc=CL[v], desc=desc or f'Ceramic {v}', text='t')
def Cv(ref, v, x, cy, side='r', desc=None): s.part(ref, 'Device', 'C', v, x, cy, 0, fp=fpc(v), lcsc=CL[v], desc=desc or f'Ceramic {v}', text=side)
def PAD(ref, name, x, y, right=False):
    s.part(ref, 'Connector_Generic', 'Conn_01x01', name, x, y, 0 if right else 180, fp=FPAD, desc=f'Wire pad: {name}', bom=False,
           text=((x + 2.54, y - 1.27), (x + 2.54, y + 1.27), 'left') if right else ((x - 2.54, y - 1.27), (x - 2.54, y + 1.27), 'right'))
    return P(ref, '1')
def POT(ref, v, name, x, y, mirror=None):
    s.part(ref, 'Device', 'R_Potentiometer', v, x, y, 0, mirror=mirror, fp=FPOT, desc=f'{name} pot, 16mm, hand-soldered',
           text=((x + 4.445, y - 1.27), (x + 4.445, y + 1.27), 'left'), extra={'Panel': name}, bom=False)

def stage(n, x, yb, q, d, rp, rb, rc, re, ce):
    """Diode-coupled CE stage. Input node at (x, yb). Returns the collector output point."""
    Rv(rp, '1M', x, yb + 3.81, side='l', desc=f'Stage {n} input node to ground'); GND(P(rp, '2'))
    s.part(d, 'Diode', '1N4148W', '1N4148W', x + g(3.5), yb, 0, fp='Diode_SMD:D_SOD-123', lcsc='C81598',
           desc=f'Stage {n} series input diode (was 1N914): cathode to the input node, anode to the base', text='t')
    W((x, yb), P(d, '1'))
    s.part(q, 'Transistor_BJT', 'MMBT3904', '2N5089', x + g(10), yb, 0, fp='SuperFreq:SOT-23_TO-92_Combo',
           desc=f'Stage {n}: 2N5089 TO-92 (E-B-C row), hand-soldered from stock. SOT-23 pads = optional MMBT5089 (C116160). Fit ONE.',
           text='r', bom=False)
    W(P(d, '2'), (x + g(7), yb), P(q, '1'))
    Rv(rb, '4M7', x + g(7), yb - g(4.5), side='l', desc=f'Stage {n} base bias from +9V'); V9(P(rb, '1'))
    W(P(rb, '2'), (x + g(7), yb))
    Rv(rc, '10k', x + g(11), yb - g(6.5), side='r', desc=f'Stage {n} collector load'); V9(P(rc, '1'))
    W(P(q, '3'), (x + g(11), yb - g(4)), P(rc, '2'))
    W(P(q, '2'), (x + g(11), yb + g(3)), (x + g(14), yb + g(3)))
    Rv(re, '1k', x + g(11), yb + g(4.5), side='l', desc=f'Stage {n} emitter resistor'); GND(P(re, '2'))
    Cv(ce, '22u', x + g(14), yb + g(4.5), side='r', desc=f'Stage {n} emitter bypass (was 22u electrolytic)'); GND(P(ce, '2'))
    return (x + g(11), yb - g(4))

yb = g(28)
# ================================================================ INPUT + STAGE 1
s.box('INPUT + STAGE 1 (Q1)', g(3), g(5), g(38), g(50))
lab('IN', (g(6), yb), 'l'); W((g(6), yb), (g(9), yb))
Rv('R1', '1M', g(9), yb + 3.81, side='l', desc='Input pull-down'); GND(P('R1', '2'))
Ch('C1', '100n', g(13.5), yb, desc='Input coupling'); W((g(9), yb), P('C1', '1'))
W(P('C1', '2'), (g(18), yb))
o = stage(1, g(18), yb, 'Q1', 'D1', 'R2', 'R3', 'R4', 'R5', 'C7')
W(o, (g(34), o[1])); lab('S1_OUT', (g(34), o[1]))

# ================================================================ GAIN + SHELF + STAGE 2
s.box('GAIN + BASS-CUT SHELF + STAGE 2 (Q2)', g(41), g(5), g(98), g(50))
lab('S1_OUT', (g(44), yb - g(4)), 'l')
Ch('C2', '100n', g(48.5), yb - g(4), desc='Stage 1 output coupling'); W((g(44), yb - g(4)), P('C2', '1'))
POT('RV1', 'A1M', 'GAIN', g(53), yb - g(4) + 3.81, mirror='x')
W(P('C2', '2'), P('RV1', '3')); GND(P('RV1', '1'))
yw = P('RV1', '2')[1]
Ch('C3', '100n', g(58.5), yw, desc='Coupling from the GAIN wiper'); W(P('RV1', '2'), P('C3', '1'))
W(P('C3', '2'), (g(61), yw), (g(61), yw + g(3.5)))
Ch('C4', '2n2', g(64.5), yw, desc='Shelf: passes highs around R6 (~150 Hz corner)'); W((g(61), yw), P('C4', '1'))
Rh('R6', '470k', g(64.5), yw + g(3.5), desc='Shelf: lows go through 470k'); W((g(61), yw + g(3.5)), P('R6', '1'))
W(P('C4', '2'), (g(68), yw), (g(68), yb), (g(68), yw + g(3.5))); W((g(68), yb), (g(71), yb)); W(P('R6', '2'), (g(68), yw + g(3.5)))
o = stage(2, g(71), yb, 'Q2', 'D2', 'R7', 'R8', 'R9', 'R10', 'C8')
W(o, (g(94), o[1])); lab('S2_OUT', (g(94), o[1]))

# ================================================================ STAGE 3 + VOLUME
s.box('STAGE 3 (Q3) + VOLUME', g(101), g(5), g(160), g(50))
lab('S2_OUT', (g(104), yb - g(4)), 'l')
Ch('C5', '100n', g(108.5), yb - g(4), desc='Stage 2 output coupling'); W((g(104), yb - g(4)), P('C5', '1'))
Rh('R11', '470k', g(113.5), yb - g(4), desc='Series attenuator into stage 3'); W(P('C5', '2'), P('R11', '1'))
W(P('R11', '2'), (g(118), yb - g(4)), (g(118), yb), (g(120), yb))
o = stage(3, g(120), yb, 'Q3', 'D3', 'R12', 'R13', 'R14', 'R15', 'C9')
Ch('C6', '100n', g(136.5), o[1], desc='Output coupling'); W(o, P('C6', '1'))
POT('RV2', 'A100k', 'VOLUME', g(141), o[1] + 3.81, mirror='x')
W(P('C6', '2'), P('RV2', '3')); GND(P('RV2', '1'))
W(P('RV2', '2'), (g(147), P('RV2', '2')[1])); lab('OUT', (g(147), P('RV2', '2')[1]))
s.text('Each stage: 1M to ground -> series diode (K at node, A at base) -> base biased 4M7 from +9V; 10k collector, 1k + 22u emitter.', g(5), g(94))
s.text('Q1-Q3: 2N5089 in the TO-92 row (E B C), hand-soldered; SOT-23 pads are an optional MMBT5089. Vc ~2-4.5 V with hFE 500-1200.', g(5), g(96))

# ================================================================ POWER, LED, PADS
s.box('POWER, LED & OFF-BOARD WIRING', g(3), g(54), g(160), g(100))
ry = g(62)
PAD('J3', '9V', g(8), ry)
s.part('D5', 'Diode', 'SS14', 'SS14', g(15), ry, 180, fp='Diode_SMD:D_SMA_Handsoldering', lcsc='C2480', desc='Series polarity protection (was 1N5817)', text='t')
W(P('J3', '1'), P('D5', '2'))
W(P('D5', '1'), (g(20), ry), (g(24), ry), (g(29), ry), (g(34), ry), (g(40), ry))
V9((g(20), ry)); s.power('PWR_FLAG', (g(24), ry))
Cv('C10', '22u', g(29), ry + 3.81, desc='+9V bulk (was 100u electrolytic)'); GND(P('C10', '2'))
Cv('C11', '100n', g(34), ry + 3.81, desc='+9V decoupling (was 47n film)'); GND(P('C11', '2'))
Rv('R16', '4k7', g(40), ry + 3.81, side='r', desc='LED current (was RLED 1k from raw V+); now after D5')
s.part('D4', 'Device', 'LED', 'LED', g(40), ry + g(7), 90, fp='LED_THT:LED_D3.0mm', desc='3mm status LED, hand-soldered', text='r', bom=False)
W(P('R16', '2'), P('D4', '2'))
W(P('D4', '1'), (g(40), ry + g(10.5))); lab('LED_K', (g(40), ry + g(10.5)), 'r')
s.part('J9', 'Connector_Generic', 'Conn_01x04', 'IN/LED/GND/OUT', g(80), g(64), 0, fp='Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical',
       desc='Ribbon header 0.1": IN, LED-, GND, OUT (hand-soldered)', text=((g(82), g(63)), (g(82), g(64.5)), 'left'), bom=False)
for pn, nm in (('1', 'IN'), ('2', 'LED_K'), ('4', 'OUT')):
    q = P('J9', pn); W(q, (q[0] - g(4), q[1])); lab(nm, (q[0] - g(4), q[1]), 'l')
q = P('J9', '3'); W(q, (q[0] - g(2), q[1]))
s.power('GND', (q[0] - g(2), q[1])); sym = s.syms[-1]; find1(sym, 'at')[3] = 270
for pr in find(sym, 'property'):
    if pr[1] == 'Value':
        find1(pr, 'at')[1:4] = [q[0] - g(2) - 2.6, q[1], 90]; find1(pr, 'effects').append([Sym('justify'), Sym('left')])
for i_, (ref, name) in enumerate((('J4', 'G'), ('J5', 'IG'), ('J6', 'OG'))):
    y = g(76) + i_ * g(3.5)
    j = PAD(ref, name, g(80), y); W(j, (g(84), y)); GND((g(84), y))
    if ref == 'J4': s.power('PWR_FLAG', (g(83), y))

s.write(OUT, {'title': 'Vulcan SMD v2', 'date': '2026-09-29', 'rev': '2.0 draft',
              'company': 'Super-Freq',
              'comments': ['Clean SMD redraw of Eagle "Vulcan v1 OSHPark" (same refs and values)',
                           'Three diode-coupled 2N5089 stages (TO-92 EBC or SOT-23); GAIN, VOLUME',
                           'SS14, LED after the diode, ceramic caps, ribbon header']})
print('ok', len(s.syms), 'symbols')
