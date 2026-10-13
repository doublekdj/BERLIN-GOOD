#!/usr/bin/env python3
"""Berlin Mood: generates the FX MOD / FX DYN / ARP pages (SVG backgrounds + layout.conf tabs).
Run from the project root after editing: python3 tools/gen_pages.py
Coordinates in the layout are absolute (art y + 86); inside the SVGs they are art-relative."""
import re, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YO = 86
MONO = "DejaVu Sans Mono,Menlo,monospace"
KS = "strip=images/stitch/knob_1.png frames=64"
HEAD = ('<text x="640" y="25" text-anchor="middle" font-family="%s" font-weight="700" font-size="11" letter-spacing="4" '
        'fill="#e0782a">BERLIN MOOD · DEVELOPED BY ANGELO RAGGI (KK)</text>' % MONO) + \
        '<text x="640" y="619" text-anchor="middle" font-family="%s" font-size="8.5" letter-spacing="1.5" fill="#85827a">ENGINE: RAFFOSYNTH BY N. ROULET &amp; J. PALLADINO (MIT) · MPC PORT: C. VESTAL, S. AUSTIN</text>' % MONO


def svg_open():
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="628" viewBox="0 0 1280 628">\n<defs>\n'
            ' <linearGradient id="bgg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2a1a0f"/><stop offset="1" stop-color="#1c1109"/></linearGradient>\n'
            ' <linearGradient id="ban" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#1b0e05"/><stop offset="1" stop-color="#0d0702"/></linearGradient>\n</defs>\n'
            '<rect x="0" y="0" width="1280" height="628" fill="url(#bgg)"/>\n'
            '<rect x="19" y="36" width="1246" height="590" rx="4" fill="none" stroke="#3a2a1d" stroke-width="2"/>\n' + HEAD + '\n')


def panel(x, w, title, sub):
    return ('<rect x="%d" y="52" width="%d" height="448" rx="6" fill="#131313" stroke="#3c3c3c" stroke-width="1.5"/>\n'
            '<text x="%d" y="73" font-family="%s" font-size="12" font-weight="700" letter-spacing="2.2" fill="#e0782a">%s</text>\n'
            '<text x="%d" y="98" text-anchor="middle" font-family="%s" font-size="11" letter-spacing="1.6" fill="#85827a">%s</text>\n'
            % (x, w, x + 14, MONO, title, x + w // 2, MONO, sub))


def label(cx, abs_y, txt):
    return ('<text x="%d" y="%d" text-anchor="middle" font-family="%s" font-size="11" font-weight="700" letter-spacing="2" '
            'fill="#e0782a">%s</text>\n' % (cx, abs_y - YO, MONO, txt))


def banner(txt="Berlin Mood"):
    return ('<rect x="38" y="516" width="1210" height="84" rx="6" fill="url(#ban)" stroke="#3c3c3c" stroke-width="1.5"/>\n'
            '<text x="643" y="568" text-anchor="middle" font-family="Georgia,Times New Roman,serif" font-style="italic" font-weight="700" font-size="46" fill="#f4f3ef">Berlin Mood</text>\n'
            '<text x="643" y="590" text-anchor="middle" font-family="%s" font-size="10" letter-spacing="3" fill="#85827a">%s</text>\n</svg>\n'
            % (MONO, txt))


def knob(cx, cy, label_, key):
    return 'knob cx=%d cy=%d r=36 label="%s" key=%s %s' % (cx, cy, label_, key, KS)


R1, R2, RT = 262, 410, 540   # abs rows: knob row 1, knob row 2, toggle row
out = {}

# ---------------- FX MOD: phaser | delay | reverb ----------------
s = svg_open() + panel(38, 340, "PHASER // BERLIN SCHOOL", "6-STAGE ALLPASS · SLOW SWEEP")
s += panel(398, 490, "DELAY // DOTTED PING-PONG", "TEMPO-LOCKED · STEREO · HOST BPM")
s += label(478, 200, "DIVISION") + label(478, 372, "TEMPO")
s += panel(908, 340, "REVERB // PLATE · ROOM · HALL", "+1 OCT SHIMMER FEEDBACK · FDN") + label(978, 502, "TYPE")
s += banner("DEVELOPED BY ANGELO RAGGI (KK)")
out["images/fx_mod_bg.svg"] = s
L = ['[tab FX MOD]', 'art file=images/fx_mod_bg.svg x=0 y=86 w=1280 h=628',
     knob(136, R1, "RATE", "ph_rate"), knob(280, R1, "DEPTH", "ph_depth"),
     knob(136, R2, "FEEDBACK", "ph_fb"), knob(280, R2, "MIX", "ph_mix"),
     'toggle cx=208 cy=%d label="PHASER" key=ph_on' % RT,
     knob(652, R1, "FEEDBACK", "dl_fb"), knob(796, R1, "TONE", "dl_tone"),
     knob(652, R2, "MIX", "dl_mix"), knob(796, R2, "BPM", "dl_bpm"),
     'enum_v cx=478 cy=284 label="" key=dl_div sw=110 sh=26',
     'enum_v cx=478 cy=414 label="" key=dl_sync sw=110 sh=26',
     'toggle cx=643 cy=%d label="DELAY" key=dl_on' % RT,
     knob(978, R1, "DECAY", "sh_decay"), knob(1122, R1, "SHIMMER", "sh_shimmer"),
     knob(978, R2, "DAMP", "sh_damp"), knob(1122, R2, "MIX", "sh_mix"),
     'enum_v cx=978 cy=542 label="" key=rv_type sw=100 sh=22',
     'toggle cx=1122 cy=%d label="REVERB" key=rv_on' % RT,
     'qlinks "FX MOD" = ph_rate,ph_depth,ph_fb,ph_mix,dl_div,dl_fb,dl_tone,dl_mix,sh_decay,sh_shimmer,sh_damp,sh_mix,ph_on,dl_on,rv_on,rv_type', '']
tabs = L

# ---------------- FX DYN: drive | compressor | limiter ----------------
s = svg_open() + panel(38, 400, "DRIVE // SATURATOR · OVERDRIVE · DISTORTION", "") .replace('></text>', '></text>')
s = svg_open() + panel(38, 400, "DRIVE", "SATURATOR · OVERDRIVE · DISTORTION")
s += label(288, 360, "TYPE")
s += panel(458, 520, "COMPRESSOR", "LINKED STEREO · SOFT KNEE · MAKE-UP GAIN")
s += panel(998, 250, "LIMITER", "LOOKAHEAD · FINAL OUTPUT")
s += banner("DEVELOPED BY ANGELO RAGGI (KK)")
out["images/fx_dyn_bg.svg"] = s
L = ['[tab FX DYN]', 'art file=images/fx_dyn_bg.svg x=0 y=86 w=1280 h=628',
     knob(138, R1, "DRIVE", "dr_drive"), knob(288, R1, "TONE", "dr_tone"),
     knob(138, R2, "MIX", "dr_mix"),
     'enum_v cx=288 cy=422 label="" key=dr_type sw=130 sh=26',
     'toggle cx=213 cy=%d label="DRIVE" key=dr_on' % RT,
     knob(545, R1, "THRESHOLD", "cp_thresh"), knob(718, R1, "RATIO", "cp_ratio"), knob(891, R1, "MAKE-UP", "cp_makeup"),
     knob(545, R2, "ATTACK", "cp_attack"), knob(718, R2, "RELEASE", "cp_release"),
     'toggle cx=718 cy=%d label="COMP" key=cp_on' % RT,
     knob(1123, R1, "CEILING", "lm_ceil"), knob(1123, R2, "RELEASE", "lm_release"),
     'toggle cx=1123 cy=%d label="LIMITER" key=lm_on' % RT,
     'qlinks "FX DYN" = dr_drive,dr_tone,dr_mix,dr_type,cp_thresh,cp_ratio,cp_attack,cp_release,cp_makeup,lm_ceil,lm_release,-,dr_on,cp_on,lm_on,-', '']
tabs += L

# ---------------- ARP ----------------
s = svg_open() + panel(38, 360, "ARPEGGIATOR", "FIXED SEQUENCES · 4 DIRECTIONS")
s += label(118, 330, "DIRECTION") + label(318, 454, "OCTAVES")
s += panel(418, 580, "PATTERN // BERLIN SEQUENCES", "1 NOTE: SEQUENCE · SEVERAL NOTES: SEQUENCE ON YOUR CHORD")
s += panel(1018, 230, "TIMING", "TEMPO: HOST OR FX MOD")
s += label(1133, 206, "RATE")
s += banner("DEVELOPED BY ANGELO RAGGI (KK)")
out["images/arp_bg.svg"] = s
L = ['[tab ARP]', 'art file=images/arp_bg.svg x=0 y=86 w=1280 h=628',
     'toggle cx=118 cy=230 label="ARP" key=arp_on', 'toggle cx=318 cy=230 label="HOLD" key=arp_hold',
     'enum_v cx=118 cy=415 label="" key=arp_dir sw=130 sh=30',
     knob(318, 338, "GATE", "arp_gate"),
     'enum_v cx=318 cy=506 label="" key=arp_oct sw=110 sh=26',
     'enum_h cx=708 cy=330 label="" key=arp_pat sw=134 sh=44 rows=4',
     'enum_v cx=1133 cy=345 label="" key=arp_rate sw=120 sh=34',
     'qlinks "ARP" = arp_dir,arp_rate,arp_oct,arp_gate,arp_pat,arp_on,arp_hold,-', '']
tabs += L

for k, v in out.items():
    open(os.path.join(ROOT, k), "w").write(v)
lay = open(os.path.join(ROOT, "layout.conf")).read()
i = lay.index("[tab FX")
open(os.path.join(ROOT, "layout.conf"), "w").write(lay[:i] + "\n".join(tabs))
print("pages written")
