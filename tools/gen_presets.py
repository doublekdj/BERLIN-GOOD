#!/usr/bin/env python3
"""Berlin Mood preset bank generator.

Writes src/dsp/presets_berlin.h: 4 hand-made Berlin patches + 494 generated Berlin School patches
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
PLUCKS = {"Phaedra Seq", "Tangram Bass", "Cyclone Seq", "Logos Pulse", "Thief Bass", "Optic Arp", "White Bell"}
PADS = {"Rubycon Pad", "Force Choir", "Exit Strings", "Hyper Drone", "Sorcerer Mist"}
BASSES = {"Tangram Bass", "Thief Bass"}
LEADS = {"Ricochet Lead", "Stratos Lead", "Stratosfear Lead", "Le Parc Flute", "Poland Brass", "Optic Arp"}


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


# effect profiles: 16 steps, each family walks through them in a different order, so every family has dry,
# medium and very wet patches, with and without phaser / drive / delay
RV_MIX = [0.0, 0.3, 0.5, 0.7, 0.35, 0.6, 0.0, 0.45, 0.8, 0.25, 0.55, 0.4, 0.65, 0.3, 0.5, 0.75]
DL_MIX = [0.0, 0.25, 0.4, 0.55, 0.0, 0.35, 0.5, 0.3, 0.6, 0.0, 0.45, 0.35, 0.5, 0.25, 0.0, 0.4]
PH_MIX = [0.0, 0.6, 0.8, 0.0, 0.7, 0.9, 0.5, 0.0, 0.75, 0.65, 0.0, 0.85, 0.55, 0.7, 0.0, 0.8]
DR_AMT = [0.0, 0.0, 0.4, 0.0, 0.0, 0.55, 0.0, 0.3, 0.0, 0.0, 0.7, 0.0, 0.45, 0.0, 0.0, 0.6]


# oscillator recipes: (wave1, wave2, wave3, octave offset of osc2, of osc3, detune2, detune3); wave 0 triangle, 1 saw,
# 2 square, 3 pulse. A None wave switches that oscillator off.
RECIPES = [(1, 1, None, 0, 0, 0.54, 0.5), (2, 1, 2, 0, -1, 0.5, 0.5), (1, 2, None, 1, 0, 0.5, 0.5),
           (3, 1, 1, 0, -1, 0.47, 0.53), (2, 2, 1, 0, 1, 0.52, 0.5), (1, 0, 2, -1, -1, 0.5, 0.5),
           (0, 1, None, 0, 0, 0.5, 0.5), (2, None, None, 0, 0, 0.5, 0.5), (1, None, None, 0, 0, 0.5, 0.5),
           (1, 1, 1, 0, -1, 0.45, 0.55), (2, 3, None, 1, 0, 0.5, 0.5), (3, 2, None, 0, 0, 0.53, 0.5),
           (1, 2, 2, -1, 0, 0.5, 0.5), (2, 1, None, 1, 0, 0.56, 0.5), (3, None, None, 0, 0, 0.5, 0.5),
           (1, 3, 0, 0, -1, 0.49, 0.5)]
SHIFT = [0, 0, 1, 0, -1, 0, 1, 0, 0, -1, 1, 0, 0, 1, -1, 0]


def apply_recipe(fi, vi, name, p):
    w1, w2, w3, o2, o3, d2, d3 = RECIPES[(vi * 5 + fi * 3) % 16]
    lo, hi = (-2, -1) if name in BASSES else ((-1, 1) if name in LEADS else (-2, 1))
    r1 = max(lo, min(hi, p["osc1_range"] + SHIFT[(vi * 3 + fi) % 16]))
    p["osc1_wave"], p["osc1_range"] = w1, r1
    for n_, w, o, d, v in ((2, w2, o2, d2, 0.55), (3, w3, o3, d3, 0.4)):
        if w is None:
            p["osc%d_volume" % n_] = 0.0
            continue
        p["osc%d_wave" % n_] = w
        p["osc%d_range" % n_] = max(-2, min(2, r1 + o))
        p["osc%d_detune" % n_] = d
        p["osc%d_volume" % n_] = max(p["osc%d_volume" % n_], v)


def variant(fi, vi, name, base, arp):
    r = random.Random(1000 * (fi + 1) + vi)
    p = dict(base)

    def jit(k, amt, lo=0.0, hi=1.0):
        p[k] = max(lo, min(hi, p[k] + r.uniform(-amt, amt)))

    # tone and envelopes
    p["cutoff"] = max(0.22, min(0.92, p["cutoff"] + ((vi % 5) - 2) * 0.03 + r.uniform(-0.03, 0.03)))
    jit("resonance", 0.1, 0.05, 0.7)
    jit("contour", 0.12)
    for k in ("decay", "release", "f_decay", "f_release"):
        p[k] = max(0.0, min(1.0, p[k] * r.uniform(0.75, 1.3)))
    if p["attack"] > 0.2:
        p["attack"] = max(0.15, min(0.65, p["attack"] * r.uniform(0.7, 1.35)))
    for k in ("osc2_detune", "osc3_detune"):
        if p[k.replace("detune", "volume")] > 0:
            jit(k, 0.035, 0.38, 0.62)
    apply_recipe(fi, vi, name, p)
    if vi % 6 == 1 and p["lfo_filter"] < 0.05:
        p["lfo_filter"] = 0.12
        p["lfo_rate"] = 0.12 + 0.05 * (vi % 4)
    brighten(name, p)

    # effects
    k = (vi + fi * 5) % 16
    rv = RV_MIX[k]
    p["rv_on"] = 1 if rv > 0 else 0
    p["sh_mix"] = rv
    p["rv_type"] = (fi + vi) % 3
    p["sh_decay"] = max(0.15, min(0.95, 0.3 + 0.045 * ((vi * 7 + fi) % 16)))
    p["sh_shimmer"] = [0.0, 0.0, 0.25, 0.45, 0.0, 0.6, 0.15, 0.0][(vi + fi) % 8]
    p["sh_damp"] = 0.3 + 0.04 * ((vi * 3 + fi) % 10)
    k = (vi * 3 + fi) % 16
    dm = DL_MIX[k]
    p["dl_on"] = 1 if dm > 0 else 0
    p["dl_mix"] = dm
    p["dl_div"] = [0, 0, 1, 2, 4, 0, 3, 1][(vi + fi) % 8]
    p["dl_fb"] = 0.3 + 0.05 * ((vi + fi) % 6)
    p["dl_tone"] = 0.4 + 0.05 * ((vi * 2 + fi) % 8)
    k = (vi * 7 + fi * 3) % 16
    pm = PH_MIX[k]
    p["ph_on"] = 1 if pm > 0 else 0
    p["ph_mix"] = pm
    p["ph_rate"] = 0.08 + 0.05 * ((vi * 5 + fi) % 9)
    p["ph_depth"] = 0.5 + 0.05 * ((vi + fi * 2) % 9)
    p["ph_fb"] = 0.3 + 0.05 * ((vi * 3 + fi) % 8)
    k = (vi * 5 + fi * 7) % 16
    da = DR_AMT[k]
    p["dr_on"] = 1 if da > 0 else 0
    p["dr_type"] = (vi + fi) % 3
    p["dr_drive"] = da
    p["dr_mix"] = 0.5 + 0.05 * (vi % 7)
    p["dr_tone"] = 0.45 + 0.04 * (vi % 8)
    if vi in (0, 9):   # fully dry reference patches
        for key in ("rv_on", "dl_on", "ph_on", "dr_on"):
            p[key] = 0
    if vi % 9 == 8:
        p["cp_on"] = 1
        p["cp_makeup"] = 0.25
    # arpeggiator / sequencer
    if arp:
        pats = arp["pats"]
        p["arp_on"] = 1
        p["arp_pat"] = pats[vi % len(pats)]
        p["arp_rate"] = arp["rates"][(vi // 2) % len(arp["rates"])]
        p["arp_dir"] = arp["dirs"][(vi // 3) % len(arp["dirs"])]
        p["arp_gate"] = max(0.25, min(0.9, p["arp_gate"] + r.uniform(-0.15, 0.2)))
        if "octs" in arp:
            p["arp_oct"] = arp["octs"][vi % len(arp["octs"])]
        if vi % 7 == 6:
            p["arp_dir"] = 3  # random every now and then
    else:
        p["arp_on"] = 0
    p["arp_hold"] = 0
    p["lm_on"] = 1
    return ("%s %s%02d" % (name, TAGS[vi % len(TAGS)], vi + 1), p)


def build():
    out = []
    for n, p in HAND:
        p = dict(p)
        brighten(n, p)
        out.append((n, p))
    for fi, (name, base, arp) in enumerate(FAMILIES):
        for vi in range(31 if fi < 14 else 30):
            out.append(variant(fi, vi, name, base, arp))
    return out


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    presets = build()
    names = [n for n, _ in presets]
    assert len(presets) == 498, "Berlin bank must contain 498 patches so the 14 factory patches make 512 total"
    assert len(set(names[4:])) == 494, "preset names must be unique"
    for n in names:
        assert len(n) <= 31, n
    lines = ["/* GENERATED by tools/gen_presets.py - do not edit. %d BERLIN K-MOOD presets. */" % len(presets),
             "#define BERLIN_PRESET_COUNT %d" % len(presets),
             "#define BERLIN_PRESET_VALUES %d" % len(ORDER),
             "static const struct { const char *name; float v[BERLIN_PRESET_VALUES]; } g_berlin_presets[BERLIN_PRESET_COUNT] = {"]
    for n, p in presets:
        vals = ", ".join(("%d" % clamp(k, p[k])) if k in INT_KEYS else ("%.3ff" % clamp(k, p[k])) for k in ORDER)
        lines.append('    {"%s", {%s}},' % (n, vals))
    lines.append("};")
    with open(os.path.join(root, "src", "dsp", "presets_berlin.h"), "w") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(root, "PRESETS.txt"), "w") as f:
        f.write("Berlin Mood presets (patch number = position in the list, counting from 1 after the 14 RaffoSynth patches)\n")
        for i, n in enumerate(names):
            f.write("%3d  %s\n" % (15 + i, n))
    print("wrote %d presets, %d values each" % (len(presets), len(ORDER)))


if __name__ == "__main__":
    main()
