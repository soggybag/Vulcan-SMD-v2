"""Simulate the Vulcan stages with KiCad's bundled ngspice (libngspice via ctypes) and report harmonic content.
Run with KiCad's python3 (has numpy).  Compares: 1, 2, 3 stages (Eagle v1 values) and a single buffered stage."""
import ctypes as C, numpy as np, sys
LIB = '/Applications/KiCad/KiCad.app/Contents/PlugIns/sim/libngspice.dylib'
ng = C.CDLL(LIB)
PRINT = C.CFUNCTYPE(C.c_int, C.c_char_p, C.c_int, C.c_void_p)
STAT = C.CFUNCTYPE(C.c_int, C.c_char_p, C.c_int, C.c_void_p)
EXIT = C.CFUNCTYPE(C.c_int, C.c_int, C.c_bool, C.c_bool, C.c_int, C.c_void_p)
LOG = []
cb_print = PRINT(lambda s, i, p: (LOG.append(s.decode(errors='ignore')), 0)[1])
cb_stat = STAT(lambda s, i, p: 0)
cb_exit = EXIT(lambda *a: 0)
ng.ngSpice_Init(cb_print, cb_stat, cb_exit, None, None, None, None)
class VI(C.Structure):
    _fields_ = [('v_name', C.c_char_p), ('v_type', C.c_int), ('v_flags', C.c_short), ('v_realdata', C.POINTER(C.c_double)),
                ('v_compdata', C.c_void_p), ('v_length', C.c_int)]
ng.ngGet_Vec_Info.restype = C.POINTER(VI)
def vec(name):
    p = ng.ngGet_Vec_Info(name.encode())
    if not p: raise KeyError(name)
    return np.array(p.contents.v_realdata[:p.contents.v_length])
MODELS = """
.model QN NPN(IS=5.911f XTI=3 EG=1.11 VAF=62.37 BF={bf} NE=1.491 ISE=5.911f IKF=15.4m XTB=1.5 BR=1.262 NC=2 ISC=0 RC=1.61 CJC=4.017p MJC=.3174 VJC=.75 FC=.5 CJE=4.973p MJE=.4146 VJE=.75 TR=4.673n TF=821.7p RB=10)
.model D1N4148 D(IS=2.52n RS=0.568 N=1.752 CJO=4p M=0.4 TT=20n BV=100)
"""
def stage(n, node_in, bias='4.7Meg', rc='10k'):
    return f"""R{n}g {node_in} 0 1Meg
D{n} b{n} {node_in} D1N4148
R{n}b vcc b{n} {bias}
Q{n} c{n} b{n} e{n} QN
R{n}c vcc c{n} {rc}
R{n}e e{n} 0 1k
C{n}e e{n} 0 22u
"""
def netlist(stages, amp, f, bf, gain_frac=0.12, rsrc='10k', buffered=False, rc='10k'):
    s = [f'* vulcan', MODELS.replace('{bf}', str(bf)), 'Vcc vcc 0 8.7', f'Vin src 0 sin(0 {amp} {f})']
    if buffered: s.append('Rs src in 50')                 # ideal-ish buffer drive
    else: s.append(f'Rs src in {rsrc}')                   # guitar pickup source impedance
    s += ['Rin in 0 1Meg', 'C1 in n1 100n', stage(1, 'n1', rc=rc)]
    if stages >= 2:
        ra, rb = 1e6 * (1 - gain_frac), 1e6 * gain_frac  # GAIN A1M wiper
        s += ['C2 c1 g1 100n', f'Rga g1 w {ra:.0f}', f'Rgb w 0 {rb:.0f}', 'C3 w s1 100n', 'C4 s1 n2 2.2n', 'R6 s1 n2 470k', stage(2, 'n2', rc=rc)]
    if stages >= 3:
        s += ['C5 c2 s2 100n', 'R11 s2 n3 470k', stage(3, 'n3', rc=rc)]
    s += ['.options noacct', '.end']
    return '\n'.join(s)
def run(nl, f):
    lines = nl.split('\n')
    arr = (C.c_char_p * (len(lines) + 1))(*[l.encode() for l in lines], None)
    ng.ngSpice_Command(b'destroy all'); ng.ngSpice_Circ(arr)
    per = 1 / f; tstop = 1.2; tstart = tstop - 20 * per
    ng.ngSpice_Command(f'tran {per / 400:.3e} {tstop} 0 {per / 400:.3e} uic'.encode())
    ng.ngSpice_Command(f'linearize'.encode())
    return tstart
def harm(t, v, f, tstart, n=8):
    m = t >= tstart; t, v = t[m], v[m]; v = v - v.mean()
    tt = np.linspace(t[0], t[0] + 20 / f, 8000, endpoint=False); vv = np.interp(tt, t, v)
    sp = np.abs(np.fft.rfft(vv * np.hanning(len(vv)))); k = 20
    h = [sp[k * i - 2:k * i + 3].max() for i in range(1, n + 1)]
    return np.array(h) / h[0], np.ptp(vv)
def report(label, nl, f, nodes):
    ts = run(nl, f); t = vec('time')
    for nd in nodes:
        h, pp = harm(t, vec(nd), f, ts)
        even = np.sqrt(sum(h[i] ** 2 for i in (1, 3, 5, 7))); odd = np.sqrt(sum(h[i] ** 2 for i in (2, 4, 6)))
        print('%-34s %-3s %5.2f Vpp  H2 %6.1f dB  H3 %6.1f dB  even/odd %5.2f' % (label, nd, pp, 20 * np.log10(h[1] + 1e-12), 20 * np.log10(h[2] + 1e-12), even / (odd + 1e-12)))
if __name__ == '__main__':
    f = 196.0   # G3
    for bf in (500, 1000):
        for amp in (0.05, 0.2):
            print(f'--- hFE {bf}, input {amp * 1000:.0f} mV peak, guitar source 10k')
            report('3 stages (Eagle v1), GAIN ~noon', netlist(3, amp, f, bf), f, ('c1', 'c2', 'c3'))
            report('single stage, buffered input', netlist(1, amp, f, bf, buffered=True), f, ('c1',))
