#!/usr/bin/env python3
"""Berlin Mood preset bank generator.

Writes src/dsp/presets_berlin.h: 4 hand-made Berlin patches + 256 generated Berlin School patches
(16 families x 16 variations, deterministic: same output every run). Run from the project root:

    python3 tools/gen_presets.py

The parameter ORDER below must match the enum in src/dsp/moog_plugin.cpp (tools/check_order.py checks it).
"""
import os
import random

ORDER = """osc1_wave osc1_volume osc1_range osc2_wave osc2_volume osc2_range osc2_detune
osc3_wave osc3_volume osc3_range osc3_detune osc4_wave osc4_volume osc4_range osc4_detune
noise cutoff resonance contour key_follow attack decay sustain release
f_attack f_decay f_sustain f_release glide volume lfo_rate lfo_pitch lfo_filter
mod_filter mod_pitch bend_range vel_sens
ph_rate ph_depth ph_fb ph_mix dl_div dl_fb dl_mix dl_tone dl_sync dl_bpm
sh_decay sh_shimmer sh_mix sh_damp
dr_on dr_type dr_drive dr_tone dr_mix ph_on dl_on rv_on rv_type
cp_on cp_thresh cp_ratio cp_attack cp_release cp_makeup lm_on lm_ceil lm_release
arp_on arp_hold arp_dir arp_pat arp_rate arp_oct arp_gate""".split()
assert len(ORDER) == 76, len(ORDER)

DEFAULT = dict(
    osc1_wave=1, osc1_volume=0.7, osc1_range=-1, osc2_wave=1, osc2_volume=0.0, osc2_range=-1, osc2_detune=0.5,
    osc3_wave=1, osc3_volume=0.0, osc3_range=-1, osc3_detune=0.5, osc4_wave=0, osc4_volume=0.0, osc4_range=0,
    osc4_detune=0.5, noise=0.0, cutoff=0.6, resonance=0.2, contour=0.3, key_follow=0.0,
    attack=0.01, decay=0.3, sustain=0.7, release=0.2, f_attack=0.01, f_decay=0.3, f_sustain=0.3, f_release=0.2,
    glide=0.0, volume=0.7, lfo_rate=0.3, lfo_pitch=0.0, lfo_filter=0.0, mod_filter=0.7, mod_pitch=0.3,
    bend_range=0.167, vel_sens=0.5,
    ph_rate=0.25, ph_depth=0.6, ph_fb=0.4, ph_mix=0.5, dl_div=0, dl_fb=0.4, dl_mix=0.3, dl_tone=0.6,
    dl_sync=0, dl_bpm=0.5, sh_decay=0.5, sh_shimmer=0.0, sh_mix=0.0, sh_damp=0.5,
    dr_on=0, dr_type=0, dr_drive=0.3, dr_tone=0.6, dr_mix=0.5, ph_on=0, dl_on=0, rv_on=0, rv_type=2,
    cp_on=0, cp_thresh=0.5, cp_ratio=0.4, cp_attack=0.3, cp_release=0.4, cp_makeup=0.2, lm_on=1, lm_ceil=0.85,
    lm_release=0.4, arp_on=0, arp_hold=0, arp_dir=0, arp_pat=0, arp_rate=3, arp_oct=0, arp_gate=0.5)

INT_KEYS = {"osc1_wave", "osc2_wave", "osc3_wave", "osc4_wave", "osc1_range", "osc2_range", "osc3_range",
            "osc4_range", "dl_div", "dl_sync", "dr_on", "dr_type", "ph_on", "dl_on", "rv_on", "rv_type", "cp_on",
            "lm_on", "arp_on", "arp_hold", "arp_dir", "arp_pat", "arp_rate", "arp_oct"}
RANGES = {"osc1_wave": (0, 3), "osc2_wave": (0, 3), "osc3_wave": (0, 3), "osc4_wave": (0, 3),
          "osc1_range": (-2, 2), "osc2_range": (-2, 2), "osc3_range": (-2, 2), "osc4_range": (-2, 2),
          "dl_div": (0, 4), "dl_sync": (0, 1), "dr_on": (0, 1), "dr_type": (0, 2), "ph_on": (0, 1), "dl_on": (0, 1),
          "rv_on": (0, 1), "rv_type": (0, 2), "cp_on": (0, 1), "lm_on": (0, 1), "arp_on": (0, 1), "arp_hold": (0, 1),
          "arp_dir": (0, 3), "arp_pat": (0, 15), "arp_rate": (0, 5), "arp_oct": (0, 2)}

TAGS = ["Amber", "Dusk", "Glass", "Ember", "Frost", "Neon", "Haze", "Iron",
        "Moss", "Tide", "Silk", "Smoke", "Dawn", "Onyx", "Coral", "Static"]


def mk(**kw):
    d = dict(DEFAULT)
    d.update(kw)
    return d


# ---- families: base patch + which arp patterns / rates / directions its variations draw from ----
FAMILIES = [
    ("Phaedra Seq", mk(osc1_volume=0.8, osc2_wave=1, osc2_volume=0.6, osc2_range=-1, osc2_detune=0.53, osc3_wave=2,
        osc3_volume=0.3, osc3_range=-2, cutoff=0.4, resonance=0.35, contour=0.45, attack=0.0, decay=0.22, sustain=0.15,
        release=0.12, f_decay=0.25, f_sustain=0.05, f_release=0.12, ph_on=1, ph_rate=0.2, ph_depth=0.6, ph_fb=0.5,
        ph_mix=0.6, dl_on=1, dl_div=0, dl_fb=0.45, dl_mix=0.35, rv_on=1, rv_type=2, sh_decay=0.5, sh_mix=0.2,
        sh_shimmer=0.15, arp_on=1, arp_hold=1, arp_gate=0.55),
     dict(pats=[4, 5, 3, 2, 6, 9, 11, 14], rates=[3, 3, 1, 3], dirs=[0, 0, 2, 0])),
    ("Rubycon Pad", mk(osc1_volume=0.75, osc1_range=0, osc2_volume=0.7, osc2_range=0, osc2_detune=0.44, osc3_volume=0.6,
        osc3_range=-1, osc3_detune=0.56, cutoff=0.5, resonance=0.15, contour=0.2, attack=0.45, decay=0.5, sustain=0.8,
        release=0.55, f_attack=0.4, f_decay=0.5, f_sustain=0.5, f_release=0.5, lfo_rate=0.12, lfo_filter=0.2,
        ph_on=1, ph_rate=0.12, ph_depth=0.7, ph_fb=0.5, ph_mix=0.5, dl_on=1, dl_div=1, dl_fb=0.4, dl_mix=0.25,
        rv_on=1, rv_type=2, sh_decay=0.7, sh_shimmer=0.5, sh_mix=0.5), None),
    ("Ricochet Lead", mk(osc1_volume=0.8, osc1_range=0, osc2_wave=3, osc2_volume=0.5, osc2_range=0, osc2_detune=0.51,
        glide=0.1, cutoff=0.62, resonance=0.35, contour=0.4, attack=0.02, decay=0.3, sustain=0.7, release=0.25,
        lfo_rate=0.4, lfo_pitch=0.05, ph_on=1, ph_rate=0.3, ph_depth=0.5, ph_fb=0.4, ph_mix=0.4, dl_on=1, dl_div=0,
        dl_fb=0.45, dl_mix=0.4, rv_on=1, rv_type=0, sh_decay=0.4, sh_mix=0.25), None),
    ("Stratos Lead", mk(osc1_volume=0.8, osc1_range=0, osc2_wave=3, osc2_volume=0.55, osc2_range=0, osc2_detune=0.52,
        osc3_volume=0.3, osc3_range=-1, glide=0.2, cutoff=0.55, resonance=0.5, contour=0.5, attack=0.03, decay=0.35,
        sustain=0.75, release=0.3, lfo_rate=0.35, lfo_pitch=0.06, ph_on=1, ph_rate=0.2, ph_depth=0.6, ph_fb=0.5,
        ph_mix=0.5, dl_on=1, dl_div=0, dl_fb=0.5, dl_mix=0.4, rv_on=1, rv_type=2, sh_decay=0.6, sh_shimmer=0.4,
        sh_mix=0.35), None),
    ("Tangram Bass", mk(osc1_volume=0.9, osc1_range=-2, osc2_wave=2, osc2_volume=0.5, osc2_range=-1, osc2_detune=0.5,
        cutoff=0.3, resonance=0.3, contour=0.55, attack=0.0, decay=0.2, sustain=0.35, release=0.12, f_decay=0.2,
        f_sustain=0.05, f_release=0.1, dr_on=1, dr_type=0, dr_drive=0.35, dr_mix=0.5, ph_on=1, ph_rate=0.2,
        ph_mix=0.3, dl_on=1, dl_div=2, dl_fb=0.35, dl_mix=0.25, rv_on=1, rv_type=1, sh_decay=0.3, sh_mix=0.15,
        arp_on=1, arp_hold=1, arp_gate=0.6),
     dict(pats=[7, 1, 3, 2, 13, 4, 8, 14], rates=[3, 3, 1, 3], dirs=[0, 0, 0, 2])),
    ("Cyclone Seq", mk(osc1_volume=0.75, osc1_range=0, osc2_wave=2, osc2_volume=0.55, osc2_range=0, osc2_detune=0.52,
        cutoff=0.55, resonance=0.4, contour=0.5, attack=0.0, decay=0.15, sustain=0.0, release=0.1, f_decay=0.18,
        f_sustain=0.0, f_release=0.1, ph_on=1, ph_rate=0.45, ph_depth=0.6, ph_fb=0.5, ph_mix=0.5, dl_on=1, dl_div=0,
        dl_fb=0.45, dl_mix=0.4, rv_on=1, rv_type=0, sh_decay=0.4, sh_mix=0.2, arp_on=1, arp_hold=1, arp_gate=0.45),
     dict(pats=[8, 4, 6, 11, 9, 10, 14, 3], rates=[3, 3, 4, 3], dirs=[0, 2, 0, 0])),
    ("Force Choir", mk(osc1_wave=3, osc1_volume=0.7, osc1_range=0, osc2_wave=0, osc2_volume=0.6, osc2_range=0,
        osc2_detune=0.49, noise=0.05, cutoff=0.45, resonance=0.45, contour=0.1, attack=0.5, decay=0.4, sustain=0.8,
        release=0.6, f_attack=0.4, lfo_rate=0.15, lfo_filter=0.25, ph_on=1, ph_rate=0.1, ph_depth=0.7, ph_fb=0.5,
        ph_mix=0.4, dl_on=1, dl_div=1, dl_fb=0.35, dl_mix=0.2, rv_on=1, rv_type=2, sh_decay=0.8, sh_shimmer=0.6,
        sh_mix=0.6), None),
    ("Hyper Drone", mk(osc1_volume=0.8, osc1_range=-2, osc2_volume=0.6, osc2_range=-1, osc2_detune=0.52, osc3_wave=0,
        osc3_volume=0.5, osc3_range=-2, cutoff=0.3, resonance=0.2, contour=0.15, attack=0.6, decay=0.5, sustain=1.0,
        release=0.8, f_attack=0.5, f_sustain=0.6, lfo_rate=0.08, lfo_filter=0.3, dr_on=1, dr_type=0, dr_drive=0.2,
        dr_mix=0.4, ph_on=1, ph_rate=0.08, ph_depth=0.8, ph_fb=0.6, ph_mix=0.5, rv_on=1, rv_type=2, sh_decay=0.85,
        sh_shimmer=0.7, sh_mix=0.55), None),
    ("White Bell", mk(osc1_wave=0, osc1_volume=0.8, osc1_range=1, osc2_wave=2, osc2_volume=0.3, osc2_range=2,
        osc2_detune=0.6, cutoff=0.7, resonance=0.25, contour=0.3, attack=0.0, decay=0.45, sustain=0.0, release=0.35,
        f_decay=0.4, f_sustain=0.0, dl_on=1, dl_div=0, dl_fb=0.55, dl_mix=0.45, ph_on=0, rv_on=1, rv_type=2,
        sh_decay=0.7, sh_shimmer=0.6, sh_mix=0.5, arp_gate=0.4),
     dict(pats=[5, 12, 4, 9, 13, 6, 11, 2], rates=[1, 1, 3, 1], dirs=[0, 2, 0, 3])),
    ("Sorcerer Mist", mk(osc1_wave=3, osc1_volume=0.65, osc1_range=-1, osc2_volume=0.5, osc2_range=-1, osc2_detune=0.46,
        cutoff=0.35, resonance=0.5, contour=0.3, attack=0.4, decay=0.5, sustain=0.7, release=0.6, f_attack=0.3,
        f_sustain=0.4, lfo_rate=0.1, lfo_filter=0.2, ph_on=1, ph_rate=0.1, ph_depth=0.85, ph_fb=0.65, ph_mix=0.7,
        dl_on=1, dl_div=1, dl_fb=0.45, dl_mix=0.25, rv_on=1, rv_type=2, sh_decay=0.75, sh_shimmer=0.3, sh_mix=0.5),
     None),
    ("Logos Pulse", mk(osc1_wave=3, osc1_volume=0.8, osc1_range=-1, osc2_wave=2, osc2_volume=0.5, osc2_range=0,
        cutoff=0.45, resonance=0.4, contour=0.4, attack=0.0, decay=0.18, sustain=0.1, release=0.1, f_decay=0.2,
        f_sustain=0.05, f_release=0.1, dr_on=1, dr_type=1, dr_drive=0.35, dr_mix=0.5, ph_on=1, ph_rate=0.25,
        ph_mix=0.4, dl_on=1, dl_div=0, dl_fb=0.4, dl_mix=0.3, rv_on=1, rv_type=1, sh_decay=0.4, sh_mix=0.2,
        arp_on=1, arp_hold=1, arp_gate=0.5),
     dict(pats=[6, 13, 14, 10, 4, 7, 12, 3], rates=[3, 1, 3, 3], dirs=[0, 0, 2, 0])),
    ("Thief Bass", mk(osc1_volume=0.9, osc1_range=-2, osc2_wave=2, osc2_volume=0.6, osc2_range=-1, cutoff=0.28,
        resonance=0.55, contour=0.6, attack=0.0, decay=0.2, sustain=0.3, release=0.1, f_decay=0.18, f_sustain=0.0,
        f_release=0.1, dr_on=1, dr_type=2, dr_drive=0.5, dr_mix=0.6, dr_tone=0.5, cp_on=1, cp_thresh=0.45,
        cp_ratio=0.5, cp_makeup=0.3, lm_on=1, ph_on=0, dl_on=1, dl_div=2, dl_fb=0.3, dl_mix=0.2, rv_on=1, rv_type=1,
        sh_decay=0.25, sh_mix=0.12, arp_on=1, arp_hold=1, arp_gate=0.55),
     dict(pats=[1, 3, 2, 7, 13, 8, 5, 12], rates=[3, 3, 1, 3], dirs=[0, 0, 0, 2])),
    ("Exit Strings", mk(osc1_volume=0.8, osc1_range=0, osc2_volume=0.7, osc2_range=0, osc2_detune=0.45, osc3_volume=0.65,
        osc3_range=-1, osc3_detune=0.55, cutoff=0.55, resonance=0.1, contour=0.15, attack=0.35, decay=0.5, sustain=0.85,
        release=0.5, f_attack=0.3, f_sustain=0.5, lfo_rate=0.2, lfo_pitch=0.02, ph_on=1, ph_rate=0.3, ph_depth=0.7,
        ph_fb=0.45, ph_mix=0.5, dl_on=1, dl_div=1, dl_fb=0.35, dl_mix=0.2, rv_on=1, rv_type=2, sh_decay=0.65,
        sh_shimmer=0.25, sh_mix=0.4), None),
    ("Optic Arp", mk(osc1_volume=0.75, osc1_range=0, osc2_wave=3, osc2_volume=0.5, osc2_range=0, osc2_detune=0.52,
        cutoff=0.5, resonance=0.3, contour=0.45, attack=0.0, decay=0.2, sustain=0.1, release=0.12, f_decay=0.22,
        f_sustain=0.05, ph_on=1, ph_rate=0.3, ph_mix=0.4, dl_on=1, dl_div=0, dl_fb=0.45, dl_mix=0.35, rv_on=1,
        rv_type=0, sh_decay=0.45, sh_mix=0.22, arp_on=1, arp_hold=0, arp_pat=0, arp_gate=0.5),
     dict(pats=[0], rates=[3, 1, 3, 4], dirs=[0, 2, 1, 3], octs=[1, 2, 1, 0])),
    ("Poland Brass", mk(osc1_volume=0.8, osc1_range=0, osc2_volume=0.7, osc2_range=0, osc2_detune=0.52, osc3_wave=2,
        osc3_volume=0.35, osc3_range=-1, cutoff=0.3, resonance=0.2, contour=0.55, attack=0.12, decay=0.4, sustain=0.8,
        release=0.3, f_attack=0.25, f_decay=0.4, f_sustain=0.6, f_release=0.3, dr_on=1, dr_type=0, dr_drive=0.25,
        dr_mix=0.4, ph_on=1, ph_rate=0.2, ph_mix=0.25, dl_on=1, dl_div=1, dl_fb=0.3, dl_mix=0.2, rv_on=1, rv_type=2,
        sh_decay=0.55, sh_mix=0.3), None),
    ("Le Parc Flute", mk(osc1_wave=0, osc1_volume=0.8, osc1_range=1, osc2_wave=3, osc2_volume=0.25, osc2_range=1,
        osc2_detune=0.5, noise=0.04, cutoff=0.6, resonance=0.15, contour=0.15, attack=0.12, decay=0.4, sustain=0.8,
        release=0.3, f_attack=0.1, lfo_rate=0.35, lfo_pitch=0.08, ph_on=0, dl_on=1, dl_div=0, dl_fb=0.4, dl_mix=0.3,
        rv_on=1, rv_type=1, sh_decay=0.5, sh_mix=0.3), None),
    ("Timewind Seq", mk(osc1_volume=0.8, cutoff=0.45, resonance=0.4, contour=0.5, attack=0.0, decay=0.25, sustain=0.15,
        release=0.15, f_decay=0.25, f_sustain=0.1, arp_on=1, arp_gate=0.5),
     dict(pats=[4, 9, 5, 3, 14, 11, 2, 6], dirs=[0, 0, 2, 0])),
    ("Mirage Pad", mk(osc1_volume=0.75, osc1_range=0, cutoff=0.55, resonance=0.2, contour=0.15, attack=0.5,
        decay=0.5, sustain=0.85, release=0.6, f_attack=0.4, f_sustain=0.55, lfo_rate=0.1, lfo_filter=0.2), None),
    ("Moondawn Seq", mk(osc1_volume=0.8, osc1_range=-1, cutoff=0.4, resonance=0.45, contour=0.55, attack=0.0,
        decay=0.2, sustain=0.1, release=0.12, f_decay=0.22, f_sustain=0.05, arp_on=1, arp_gate=0.45),
     dict(pats=[8, 6, 4, 3, 10, 13, 7, 9], dirs=[0, 0, 2, 3])),
    ("Cyborg Arp", mk(osc1_volume=0.75, osc1_range=0, cutoff=0.55, resonance=0.35, contour=0.45, attack=0.0,
        decay=0.18, sustain=0.1, release=0.12, f_decay=0.2, f_sustain=0.05, arp_on=1, arp_gate=0.5),
     dict(pats=[1, 11, 12, 2, 5, 14, 0, 9], dirs=[0, 1, 0, 3], octs=[1, 2, 0, 1])),
    ("Body Love Bass", mk(osc1_volume=0.9, osc1_range=-2, cutoff=0.32, resonance=0.4, contour=0.55, attack=0.0,
        decay=0.22, sustain=0.3, release=0.12, f_decay=0.2, f_sustain=0.05, arp_on=1, arp_gate=0.6),
     dict(pats=[7, 1, 13, 3, 2, 8, 12, 14], dirs=[0, 0, 0, 2])),
    ("Dune Drone", mk(osc1_volume=0.8, osc1_range=-2, cutoff=0.32, resonance=0.2, contour=0.1, attack=0.65,
        decay=0.5, sustain=1.0, release=0.85, f_attack=0.5, f_sustain=0.6, lfo_rate=0.07, lfo_filter=0.3), None),
    ("Picture Music", mk(osc1_volume=0.75, osc1_range=0, cutoff=0.5, resonance=0.25, contour=0.35, attack=0.02,
        decay=0.35, sustain=0.6, release=0.3, lfo_rate=0.3), None),
    ("Trancefer Lead", mk(osc1_volume=0.8, osc1_range=0, cutoff=0.6, resonance=0.35, contour=0.4, attack=0.02,
        decay=0.3, sustain=0.75, release=0.3, glide=0.15), None),
    ("Crystal Lake", mk(osc1_volume=0.75, osc1_range=1, cutoff=0.65, resonance=0.2, contour=0.3, attack=0.0,
        decay=0.4, sustain=0.1, release=0.4, f_decay=0.4, f_sustain=0.1, arp_on=1, arp_gate=0.4),
     dict(pats=[5, 12, 4, 9, 13, 6, 11, 2], dirs=[0, 2, 0, 3], octs=[1, 2, 1, 0])),
    ("Velvet Organ", mk(osc1_volume=0.75, osc1_range=0, cutoff=0.55, resonance=0.1, contour=0.05, attack=0.05,
        decay=0.3, sustain=0.95, release=0.35, f_sustain=0.7), None),
    ("Irrlicht Choir", mk(osc1_volume=0.7, osc1_range=0, cutoff=0.45, resonance=0.4, contour=0.1, attack=0.55,
        decay=0.4, sustain=0.85, release=0.65, f_attack=0.4, lfo_rate=0.12, lfo_filter=0.25), None),
    ("Echoes Bell", mk(osc1_volume=0.8, osc1_range=1, cutoff=0.7, resonance=0.2, contour=0.3, attack=0.0,
        decay=0.5, sustain=0.0, release=0.45, f_decay=0.45, f_sustain=0.0), None),
    ("Ion Pulse", mk(osc1_volume=0.8, osc1_range=-1, cutoff=0.5, resonance=0.4, contour=0.45, attack=0.0, decay=0.18,
        sustain=0.1, release=0.12, f_decay=0.2, f_sustain=0.05, arp_on=1, arp_gate=0.5),
     dict(pats=[6, 13, 14, 10, 4, 7, 12, 3], dirs=[0, 0, 2, 0])),
    ("Aurora Pad", mk(osc1_volume=0.75, osc1_range=0, cutoff=0.6, resonance=0.15, contour=0.15, attack=0.4,
        decay=0.5, sustain=0.85, release=0.55, f_attack=0.35, f_sustain=0.6, lfo_rate=0.15, lfo_filter=0.15), None),
    ("Sequencer Rain", mk(osc1_volume=0.75, osc1_range=1, cutoff=0.6, resonance=0.3, contour=0.4, attack=0.0,
        decay=0.2, sustain=0.1, release=0.15, f_decay=0.22, f_sustain=0.05, arp_on=1, arp_gate=0.4),
     dict(pats=[9, 11, 5, 10, 14, 4, 6, 12], dirs=[0, 2, 0, 3], octs=[1, 0, 2, 1])),
    ("Wave Glass", mk(osc1_volume=0.75, osc1_range=0, cutoff=0.65, resonance=0.3, contour=0.35, attack=0.03,
        decay=0.3, sustain=0.7, release=0.3, lfo_rate=0.35), None),
]

# the four hand-made patches that shipped in v1.0 (now with their effects switched on)
HAND = [
    ("Phaedra Seq", mk(osc1_volume=0.8, osc2_volume=0.7, osc2_detune=0.46, osc3_volume=0.5, osc3_range=-2,
        osc3_detune=0.54, cutoff=0.42, resonance=0.35, contour=0.45, attack=0.0, decay=0.3, sustain=0.2, release=0.12,
        f_decay=0.2, f_sustain=0.0, f_release=0.12, ph_on=1, ph_rate=0.18, ph_depth=0.7, ph_fb=0.55, ph_mix=0.75,
        dl_on=1, dl_div=0, dl_fb=0.45, dl_mix=0.4, dl_tone=0.55, rv_on=1, sh_decay=0.55, sh_shimmer=0.15, sh_mix=0.18,
        sh_damp=0.5)),
    ("Rubycon Pad", mk(osc1_volume=0.75, osc1_range=0, osc2_volume=0.7, osc2_range=0, osc2_detune=0.44, osc3_volume=0.6,
        osc3_detune=0.56, osc4_wave=2, osc4_volume=0.2, osc4_range=1, cutoff=0.5, resonance=0.25, contour=0.05,
        attack=0.5, decay=0.5, sustain=0.85, release=0.55, f_attack=0.12, f_decay=0.5, f_sustain=0.5, f_release=0.5,
        lfo_rate=0.25, lfo_pitch=0.05, ph_on=1, ph_rate=0.12, ph_depth=0.8, ph_fb=0.7, ph_mix=0.5, dl_on=1, dl_div=1,
        dl_fb=0.3, dl_mix=0.35, rv_on=1, sh_decay=0.78, sh_shimmer=0.55, sh_mix=0.5, sh_damp=0.45)),
    ("Stratosfear Lead", mk(osc1_volume=0.8, osc1_range=0, osc2_volume=0.6, osc2_range=0, osc2_detune=0.51,
        osc3_wave=2, osc3_volume=0.25, osc3_range=-1, cutoff=0.58, resonance=0.4, contour=0.4, attack=0.02,
        decay=0.3, sustain=0.4, release=0.25, f_attack=0.02, f_decay=0.3, f_sustain=0.4, f_release=0.25, glide=0.12,
        lfo_rate=0.35, lfo_pitch=0.08, vel_sens=0.6, ph_on=1, ph_rate=0.35, ph_depth=0.5, ph_fb=0.55, ph_mix=0.4,
        dl_on=1, dl_div=0, dl_fb=0.45, dl_mix=0.65, dl_tone=0.5, rv_on=1, sh_decay=0.6, sh_shimmer=0.3, sh_mix=0.28,
        sh_damp=0.4)),
    ("Tangram Bass", mk(osc1_volume=0.9, osc1_range=-2, osc2_volume=0.5, osc2_range=-1, osc2_detune=0.52,
        osc3_wave=0, osc3_volume=0.3, osc3_range=-2, cutoff=0.3, resonance=0.45, contour=0.5, attack=0.0, decay=0.25,
        sustain=0.3, release=0.12, f_decay=0.2, f_sustain=0.0, f_release=0.1, ph_on=1, ph_rate=0.12, ph_depth=0.5,
        ph_fb=0.5, ph_mix=0.2, dl_on=1, dl_div=2, dl_fb=0.4, dl_mix=0.22, rv_on=1, rv_type=1, sh_decay=0.4,
        sh_mix=0.1, sh_damp=0.6)),
]


def clamp(k, v):
    lo, hi = RANGES.get(k, (0.0, 1.0))
    v = max(lo, min(hi, v))
    return int(round(v)) if k in INT_KEYS else round(v, 3)


BRIGHT = {"Phaedra Seq": 0.2, "Rubycon Pad": 0.22, "Ricochet Lead": 0.2, "Stratos Lead": 0.2, "Stratosfear Lead": 0.2,
          "Tangram Bass": 0.12, "Cyclone Seq": 0.2, "Force Choir": 0.22, "Hyper Drone": 0.2, "White Bell": 0.1,
          "Sorcerer Mist": 0.2, "Logos Pulse": 0.18, "Thief Bass": 0.12, "Exit Strings": 0.24, "Optic Arp": 0.2,
          "Poland Brass": 0.18, "Le Parc Flute": 0.14}
PLUCKS = {"Timewind Seq", "Moondawn Seq", "Cyborg Arp", "Ion Pulse", "Sequencer Rain", "Crystal Lake", "Echoes Bell", "Phaedra Seq", "Tangram Bass", "Cyclone Seq", "Logos Pulse", "Thief Bass", "Optic Arp", "White Bell"}
PADS = {"Mirage Pad", "Dune Drone", "Velvet Organ", "Irrlicht Choir", "Aurora Pad", "Rubycon Pad", "Force Choir", "Exit Strings", "Hyper Drone", "Sorcerer Mist"}
BASSES = {"Body Love Bass", "Tangram Bass", "Thief Bass"}
LEADS = {"Trancefer Lead", "Wave Glass", "Picture Music", "Ricochet Lead", "Stratos Lead", "Stratosfear Lead", "Le Parc Flute", "Poland Brass", "Optic Arp"}


def brighten(name, p):
    """The filter must stay open while a note is held: higher cutoff, and for leads the filter envelope
    settles high (small contour, high sustain) so the sound does not close down."""
    p["cutoff"] = min(0.95, p["cutoff"] + BRIGHT.get(name, 0.12))
    if name in LEADS:
        p["f_sustain"] = max(p["f_sustain"], 0.65)
        p["contour"] = min(p["contour"], 0.3)
    else:
        p["f_sustain"] = max(p["f_sustain"], 0.35)
    if name in PLUCKS:   # plucks and sequence sounds: longer body, filter that stays open and a real release
        p["decay"] = max(p["decay"], 0.4)
        p["sustain"] = max(p["sustain"], 0.3)
        p["release"] = max(p["release"], 0.32)
        p["f_decay"] = max(p["f_decay"], 0.42)
        p["f_sustain"] = max(p["f_sustain"], 0.5)
        p["f_release"] = max(p["f_release"], 0.32)
    if name in PADS:
        p["f_sustain"] = max(p["f_sustain"], 0.55)
        p["contour"] = min(p["contour"], 0.3)
    p["arp_hold"] = 0


def pick(r, items):
    return items[r.randrange(len(items))]


def role_of(name):
    if name in BASSES or name == "Body Love Bass":
        return "bass"
    if name in PADS:
        return "pad"
    if name in LEADS:
        return "lead"
    if name in PLUCKS:
        return "pluck"
    return "other"


WM = [1, 2, 4, 3, 5, 6, 7, 1, 2, 4, 3, 1]   # wheel destination bitmask (cutoff always): 1 reverb, 2 delay, 4 phaser


def variant(fi, vi, name, base, arp):
    n = fi * 16 + vi
    r = random.Random(7919 * (n + 1))
    p = dict(base)
    role = role_of(name)

    # ---- timbre: all four oscillators, random waves / octaves / detune / levels ----
    nosc = pick(r, [1, 2, 2, 2, 3, 3, 3, 4, 4])
    if role == "pad":
        nosc = max(nosc, 2)
    waves = [pick(r, [1, 1, 1, 2, 2, 3, 3, 0]) for _ in range(4)]
    if nosc > 1 and waves[1] == waves[0] and r.random() < 0.7:
        waves[1] = pick(r, [w for w in (0, 1, 2, 3) if w != waves[0]])
    lo, hi = {"bass": (-2, -1), "lead": (-1, 1), "pad": (-1, 1)}.get(role, (-2, 1))
    r1 = max(lo, min(hi, p["osc1_range"] + pick(r, [0, 0, 0, -1, 1])))
    offs = [0, pick(r, [0, 0, -1, 1, 1, 2, -2]), pick(r, [0, -1, -1, 1, 2, -2]), pick(r, [0, 1, 2, -1, -2])]
    dets = [0.5, pick(r, [0.5, 0.46, 0.54, 0.42, 0.58, 0.37, 0.63]), pick(r, [0.5, 0.45, 0.55, 0.4, 0.6]),
            pick(r, [0.5, 0.48, 0.52, 0.44, 0.56])]
    p["osc1_wave"], p["osc1_range"] = waves[0], r1
    p["osc1_volume"] = r.uniform(0.6, 0.9)
    for k in (1, 2, 3):
        key = "osc%d_" % (k + 1)
        if k >= nosc:
            p[key + "volume"] = 0.0
            p[key + "wave"] = waves[k]
            continue
        p[key + "wave"] = waves[k]
        p[key + "range"] = max(-2, min(2, r1 + offs[k]))
        d = dets[k] + r.uniform(-0.014, 0.014)                       # analog oscillators never sit exactly in tune
        if r.random() < 0.3:
            d += pick(r, [-1, 1]) * r.uniform(0.03, 0.07)             # clearly detuned (fat) patches
        p[key + "detune"] = max(0.36, min(0.64, d))
        p[key + "volume"] = r.uniform(0.3, 0.75) if k < 3 else r.uniform(0.25, 0.55)
    p["noise"] = r.uniform(0.03, 0.1) if r.random() < 0.1 else 0.0

    # ---- filter / envelopes ----
    p["cutoff"] = max(0.3, min(0.9, p["cutoff"] + r.uniform(-0.12, 0.2)))
    p["resonance"] = r.uniform(0.05, 0.62)
    p["contour"] = max(0.0, min(0.75, p["contour"] + r.uniform(-0.2, 0.2)))
    p["key_follow"] = pick(r, [0.0, 0.0, 0.3, 0.5, 0.7])
    for k in ("decay", "release", "f_decay", "f_release"):
        p[k] = max(0.0, min(1.0, p[k] * r.uniform(0.7, 1.4)))
    if p["attack"] > 0.2:
        p["attack"] = max(0.12, min(0.7, p["attack"] * r.uniform(0.6, 1.4)))
    if role == "lead":
        p["glide"] = pick(r, [0.0, 0.08, 0.15, 0.25])
    if r.random() < 0.4:
        p["lfo_filter"] = r.uniform(0.1, 0.4)
        p["lfo_rate"] = r.uniform(0.06, 0.55)
    p["lfo_pitch"] = 0.0
    p["mod_filter"] = r.uniform(0.75, 1.0)    # mod wheel -> cutoff
    p["mod_pitch"] = 0.0                      # no pitch movement from the wheel
    brighten(name, p)
    # brightness: a spread from warm to bright instead of everything open; VCF envelope varied per patch
    cls = (n * 7 + fi) % 10
    if cls < 3:      # warm
        cut = r.uniform(0.34, 0.5); p["contour"] = min(p["contour"], 0.35)
    elif cls < 7:    # medium
        cut = r.uniform(0.5, 0.64); p["contour"] = min(p["contour"], 0.5)
    else:            # bright
        cut = r.uniform(0.64, 0.78); p["contour"] = min(p["contour"], 0.4)
    cut += {"bass": -0.08, "pad": 0.02, "lead": 0.03}.get(role, 0.0)
    hi_r = max([p["osc1_range"]] + [p["osc%d_range" % k] for k in (2, 3, 4) if p["osc%d_volume" % k] > 0])
    lo_r = min([p["osc1_range"]] + [p["osc%d_range" % k] for k in (2, 3, 4) if p["osc%d_volume" % k] > 0])
    floor = 0.4 + 0.065 * (lo_r + 2) if role != "bass" else 0.28   # the filter must stay above the notes
    p["cutoff"] = max(0.28, floor, min(0.85, cut))
    p["f_decay"] = r.uniform(0.15, 0.8)
    p["f_sustain"] = r.uniform(0.1, 0.9)
    p["f_release"] = r.uniform(0.1, 0.8)
    if role in ("pluck",):
        p["f_sustain"] = max(p["f_sustain"], 0.3); p["f_release"] = max(p["f_release"], 0.3)
    if role == "lead":
        p["f_sustain"] = max(p["f_sustain"], 0.45)   # the filter must not close on a held lead
    p["f_attack"] = r.uniform(0.0, 0.35) if role in ("pad", "other") and r.random() < 0.5 else p["f_attack"]

    # ---- effects ----
    dry_ref = (n % 64 == 0)
    # reverb: plate/room/hall, shimmer on about a third of the bank
    shim = (n % 20) < 7
    p["rv_on"] = 0 if (n % 17 == 5) else 1
    p["rv_type"] = (n // 3) % 3
    if shim:
        p["sh_shimmer"] = r.uniform(0.45, 0.9)
        p["sh_mix"] = r.uniform(0.4, 0.8)
        p["sh_decay"] = r.uniform(0.6, 0.95)
    else:
        p["sh_shimmer"] = pick(r, [0.0, 0.0, 0.1, 0.2])
        p["sh_mix"] = pick(r, [0.15, 0.25, 0.35, 0.45, 0.55, 0.65])
        p["sh_decay"] = r.uniform(0.25, 0.85)
    if role in ("pad", "other") and not shim:
        p["sh_mix"] = max(p["sh_mix"], 0.35)
    p["sh_damp"] = r.uniform(0.3, 0.7)
    # delay: dotted eighth for arps
    p["dl_on"] = 0 if (n % 9 in (3, 7)) else 1
    if arp:
        p["dl_on"] = 1 if (n % 9 != 3) else 0
        p["dl_div"] = 0 if r.random() < 0.8 else pick(r, [1, 3])
    else:
        p["dl_div"] = pick(r, [0, 0, 1, 0, 3, 2, 4])
    p["dl_mix"] = r.uniform(0.2, 0.6)
    p["dl_fb"] = r.uniform(0.3, 0.62)
    p["dl_tone"] = r.uniform(0.4, 0.75)
    p["dl_sync"] = 0
    # phaser in 30% of the bank
    p["ph_on"] = 1 if (n % 5) in (1, 3) else 0
    p["ph_mix"] = r.uniform(0.5, 0.9)
    p["ph_rate"] = r.uniform(0.08, 0.5)
    p["ph_depth"] = r.uniform(0.5, 0.95)
    p["ph_fb"] = r.uniform(0.3, 0.7)
    # drive in about a quarter
    p["dr_on"] = 1 if (n % 4 == 2) else 0
    p["dr_type"] = (n // 4) % 3
    p["dr_drive"] = r.uniform(0.3, 0.7)
    p["dr_mix"] = r.uniform(0.45, 0.8)
    p["dr_tone"] = r.uniform(0.45, 0.75)
    if dry_ref:
        for key in ("rv_on", "dl_on", "ph_on", "dr_on"):
            p[key] = 0
    if n % 9 == 8:
        p["cp_on"] = 1
        p["cp_makeup"] = 0.25

    # ---- arpeggiator: mostly eighth notes with dotted-eighth delay ----
    if arp:
        p["arp_on"] = 1
        p["arp_pat"] = arp["pats"][vi % len(arp["pats"])]
        slot = (vi * 3 + fi) % 10
        p["arp_rate"] = 1 if slot < 8 else (0 if slot == 8 else 2)    # 80% 1/8, 10% 1/4, 10% 1/8T
        p["arp_dir"] = arp["dirs"][(vi // 3) % len(arp["dirs"])]
        p["arp_gate"] = max(0.3, min(0.9, p["arp_gate"] + r.uniform(-0.1, 0.2)))
        if "octs" in arp:
            p["arp_oct"] = arp["octs"][vi % len(arp["octs"])]
        if vi % 7 == 6:
            p["arp_dir"] = 3
    else:
        p["arp_on"] = 0
    p["arp_hold"] = 0
    p["lm_on"] = 1
    wheel = WM[(n * 5 + fi) % len(WM)]
    return ("%s %s" % (name, TAGS[vi]), p, wheel)


def build():
    out = []
    for fi, (name, base, arp) in enumerate(FAMILIES):
        for vi in range(16):
            out.append(variant(fi, vi, name, base, arp))
    return out


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    presets = build()
    names = [n for n, _, _ in presets]
    assert len(presets) == 512, len(presets)
    assert len(set(names)) == len(names), "preset names must be unique"
    for n in names:
        assert len(n) <= 31, n
    lines = ["/* GENERATED by tools/gen_presets.py - do not edit. %d Berlin Mood presets. */" % len(presets),
             "#define BERLIN_PRESET_COUNT %d" % len(presets),
             "#define BERLIN_PRESET_VALUES %d" % len(ORDER),
             "static const struct { const char *name; float v[BERLIN_PRESET_VALUES]; } g_berlin_presets[BERLIN_PRESET_COUNT] = {"]
    for n, p, _ in presets:
        vals = ", ".join(("%d" % clamp(k, p[k])) if k in INT_KEYS else ("%.3ff" % clamp(k, p[k])) for k in ORDER)
        lines.append('    {"%s", {%s}},' % (n, vals))
    lines.append("};")
    lines.append("/* mod wheel destinations besides cutoff: bit0 reverb, bit1 delay, bit2 phaser */")
    lines.append("static const unsigned char g_berlin_wheel[BERLIN_PRESET_COUNT] = {")
    ws = [str(w) for _, _, w in presets]
    for i in range(0, len(ws), 32):
        lines.append("    " + ",".join(ws[i:i + 32]) + ",")
    lines.append("};")
    with open(os.path.join(root, "src", "dsp", "presets_berlin.h"), "w") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(root, "PRESETS.txt"), "w") as f:
        f.write("Berlin Mood presets (patch number = position in the list, counting from 1 after the 14 RaffoSynth patches)\n")
        for i, n in enumerate(names):
            f.write("%3d  %s\n" % (15 + i, n))
    ph = sum(p["ph_on"] for _, p, _ in presets); ar = [p for _, p, _ in presets if p["arp_on"]]
    print("wrote %d presets, %d values each; phaser %d, arp %d (1/8: %d)" % (
        len(presets), len(ORDER), ph, len(ar), sum(1 for p in ar if p["arp_rate"] == 1)))


if __name__ == "__main__":
    main()
