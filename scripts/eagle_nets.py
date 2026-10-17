"""Print nets from an Eagle .brd (contactrefs) or .sch (pinrefs mapped to pads via device connects)."""
import sys, xml.etree.ElementTree as ET
t = ET.parse(sys.argv[1]).getroot()
nets = {}
if sys.argv[1].endswith('.brd'):
    for s in t.iter('signal'):
        nodes = sorted((c.get('element'), c.get('pad')) for c in s.findall('contactref'))
        if nodes: nets[s.get('name')] = nodes
    parts = {e.get('name'): (e.get('value'), e.get('package')) for e in t.iter('element')}
else:
    # map part -> (library, deviceset, device) -> connects gate/pin -> pad
    libs = {}
    for lib in t.iter('library'):
        for ds in lib.iter('deviceset'):
            for dv in ds.iter('device'):
                cm = {}
                for c in dv.iter('connect'):
                    for pad in c.get('pad').split(): cm.setdefault((c.get('gate'), c.get('pin')), []).append(pad)
                libs[(lib.get('name'), ds.get('name'), dv.get('name'))] = cm
    pm = {}; parts = {}
    for p in t.iter('part'):
        pm[p.get('name')] = libs.get((p.get('library'), p.get('deviceset'), p.get('device')), {})
        parts[p.get('name')] = (p.get('value') or p.get('deviceset'), p.get('deviceset') + p.get('device'))
    for sh in t.iter('sheet'):
        for n in sh.iter('net'):
            nodes = nets.setdefault(n.get('name'), [])
            for pr in n.iter('pinref'):
                pads = pm[pr.get('part')].get((pr.get('gate'), pr.get('pin')), [pr.get('pin') + '?'])
                for pad in pads: nodes.append((pr.get('part'), pad))
    nets = {k: sorted(set(v)) for k, v in nets.items() if v}
if len(sys.argv) > 2 and sys.argv[2] == 'parts':
    for k in sorted(parts): print(k, parts[k])
for k in sorted(nets): print(k, ' '.join(f'{a}.{b}' for a, b in nets[k]))
