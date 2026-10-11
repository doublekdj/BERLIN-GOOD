/*
 * Berlin Mood - arpeggiator / sequencer (original code for this project, MIT, see LICENSE).
 *
 * Plays the notes you hold as an arpeggio (CHORD) or runs a fixed Berlin School sequence from the lowest held
 * note. Direction: UP, DOWN, UP/DOWN, RANDOM. Rate and gate are set per patch; tempo comes from the host
 * (or the manual BPM). HOLD latches the notes so the sequence keeps running with your hands off.
 *
 * Usage (one instance per plugin instance): feed note on/off to arp_note_on/arp_note_off, then once per audio
 * block call arp_process() and play the returned events at their sample offsets.
 */
#ifndef BERLIN_ARP_H
#define BERLIN_ARP_H

#include <stdint.h>
#include <string.h>

#define ARP_MAX_HELD 16
#define ARP_MAX_STEPS 64
#define ARP_REST (-128)
#define ARP_SR 44100.0

enum { ARP_UP = 0, ARP_DOWN, ARP_BOTH, ARP_RANDOM };

typedef struct {
    int on, dir, pat, rate, oct, hold;   /* oct: 0..2 (1 to 3 octaves) */
    float gate;                          /* 0..1 -> 10% .. 100% of a step */
    int held[ARP_MAX_HELD], held_vel[ARP_MAX_HELD], nheld;   /* sorted ascending */
    int keys_down;
    int running, idx, dirsign, cur_note;
    double step_in, gate_in;             /* samples until the next step / the gate end (gate_in < 0: no note) */
    uint32_t rng;
} arp_t;

typedef struct { int at; int on; int note; int vel; } arp_event_t;

/* index 0 is CHORD (no table); 1.. are fixed sequences, offsets in semitones from the lowest held note */
#define ARP_PATTERNS 16
static const signed char ARP_SEQ[ARP_PATTERNS][16] = {
    {0},
    {0, 0, 0, 0, 0, 0, 0, 0},                                    /* 1  PULSE */
    {0, 12, 0, 12, 0, 12, 0, 12},                                /* 2  OCTAVES */
    {0, 7, 0, 7, 12, 7, 0, 7},                                   /* 3  FIFTHS */
    {0, 7, 12, 15, 19, 15, 12, 7},                               /* 4  PHAEDRA */
    {0, 3, 7, 12, 7, 3, 0, 7},                                   /* 5  RUBYCON */
    {0, 7, 10, 12, 10, 7, 5, 7},                                 /* 6  STRATOS */
    {0, 0, 12, 0, 7, 0, 10, 0},                                  /* 7  TANGRAM */
    {0, 12, 7, 12, 0, 12, 3, 12},                                /* 8  CYCLONE */
    {0, 3, 7, 10, 12, 15, 19, 22},                               /* 9  MINOR CLIMB */
    {0, 2, 3, 5, 7, 9, 10, 12},                                  /* 10 DORIAN */
    {0, 7, 3, 10, 7, 12, 10, 15},                                /* 11 OPTIC */
    {0, ARP_REST, 7, ARP_REST, 12, ARP_REST, 7, ARP_REST},       /* 12 GAPPED */
    {0, ARP_REST, 0, 7, ARP_REST, 12, ARP_REST, 7},              /* 13 SYNCOPATED */
    {0, 0, 7, 0, 12, 0, 7, 0, 3, 3, 10, 3, 15, 3, 10, 3},        /* 14 16 STEP */
    {24, 19, 15, 12, 7, 3, 0, -5},                               /* 15 DESCENT */
};
static const int ARP_SEQ_LEN[ARP_PATTERNS] = {0, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 16, 8};

static const double ARP_BEATS[6] = {1.0, 0.5, 1.0 / 3.0, 0.25, 1.0 / 6.0, 0.125};   /* 1/4 1/8 1/8T 1/16 1/16T 1/32 */

static void arp_init(arp_t *a) {
    memset(a, 0, sizeof(*a));
    a->rate = 3; a->gate = 0.5f; a->rng = 0x1234567u; a->gate_in = -1.0; a->cur_note = -1; a->dirsign = 1;
}

static uint32_t arp_rand(arp_t *a) {
    uint32_t x = a->rng;
    x ^= x << 13; x ^= x >> 17; x ^= x << 5;
    return a->rng = x;
}

static int arp_seq_len(const arp_t *a) {
    if (a->nheld == 0) return 0;
    if (a->pat > 0 && a->pat < ARP_PATTERNS) return ARP_SEQ_LEN[a->pat];
    int o = a->oct < 0 ? 0 : (a->oct > 2 ? 2 : a->oct);
    return a->nheld * (o + 1);
}

/* note at sequence position i, or ARP_REST */
static int arp_seq_note(const arp_t *a, int i, int *vel) {
    if (a->pat > 0 && a->pat < ARP_PATTERNS) {
        int off = ARP_SEQ[a->pat][i];
        *vel = a->held_vel[0];
        if (off == ARP_REST) return ARP_REST;
        int n = a->held[0] + off;
        return n < 0 ? 0 : (n > 127 ? 127 : n);
    }
    int k = i % a->nheld, o = i / a->nheld;
    *vel = a->held_vel[k];
    int n = a->held[k] + 12 * o;
    return n > 127 ? 127 : n;
}

static void arp_note_on(arp_t *a, int note, int vel) {
    if (a->hold && a->keys_down == 0) a->nheld = 0;   /* a new chord replaces the latched one */
    a->keys_down++;
    for (int i = 0; i < a->nheld; i++)
        if (a->held[i] == note) { a->held_vel[i] = vel; return; }
    if (a->nheld >= ARP_MAX_HELD) return;
    int p = a->nheld;
    while (p > 0 && a->held[p - 1] > note) { a->held[p] = a->held[p - 1]; a->held_vel[p] = a->held_vel[p - 1]; p--; }
    a->held[p] = note; a->held_vel[p] = vel;
    a->nheld++;
}

static void arp_note_off(arp_t *a, int note) {
    if (a->keys_down > 0) a->keys_down--;
    if (a->hold) return;
    for (int i = 0; i < a->nheld; i++)
        if (a->held[i] == note) {
            for (int j = i; j < a->nheld - 1; j++) { a->held[j] = a->held[j + 1]; a->held_vel[j] = a->held_vel[j + 1]; }
            a->nheld--;
            return;
        }
}

/* stop playing and forget the held notes; returns 1 if a note was sounding (the caller sends note-off for *note) */
static int arp_reset(arp_t *a, int *note) {
    int sounding = a->gate_in >= 0.0 && a->cur_note >= 0;
    if (note) *note = a->cur_note;
    a->nheld = 0; a->keys_down = 0; a->running = 0; a->gate_in = -1.0; a->cur_note = -1; a->step_in = 0.0;
    return sounding;
}

static void arp_start_index(arp_t *a, int n) {
    a->dirsign = 1;
    if (a->dir == ARP_DOWN) a->idx = n - 1;
    else if (a->dir == ARP_RANDOM) a->idx = (int)(arp_rand(a) % (uint32_t)n);
    else a->idx = 0;
}

static void arp_advance(arp_t *a, int n) {
    switch (a->dir) {
        case ARP_DOWN: a->idx = (a->idx - 1 + n) % n; break;
        case ARP_BOTH:
            if (n <= 1) { a->idx = 0; break; }
            if (a->idx + a->dirsign >= n || a->idx + a->dirsign < 0) a->dirsign = -a->dirsign;
            a->idx += a->dirsign;
            break;
        case ARP_RANDOM:
            if (n > 1) { int j = (int)(arp_rand(a) % (uint32_t)(n - 1)); a->idx = j >= a->idx ? j + 1 : j; }
            else a->idx = 0;
            break;
        default: a->idx = (a->idx + 1) % n; break;
    }
}

/* One audio block. Fills ev[] (at most max), time-ordered, with note on/off at sample offsets in [0, frames). */
static int arp_process(arp_t *a, int frames, double bpm, arp_event_t *ev, int max) {
    int ne = 0;
    if (bpm < 20.0) bpm = 20.0;
    int r = a->rate < 0 ? 0 : (a->rate > 5 ? 5 : a->rate);
    double step_len = ARP_SR * 60.0 / bpm * ARP_BEATS[r];
    double gate_len = step_len * (0.1 + 0.9 * (double)a->gate);
    if (gate_len < 1.0) gate_len = 1.0;
    int n = arp_seq_len(a);

    if (n == 0) {   /* nothing held */
        if (a->running) {
            if (a->gate_in >= 0.0 && a->cur_note >= 0 && ne < max) { ev[ne].at = 0; ev[ne].on = 0; ev[ne].note = a->cur_note; ev[ne].vel = 0; ne++; }
            a->running = 0; a->gate_in = -1.0; a->cur_note = -1;
        }
        return ne;
    }
    if (!a->running) { a->running = 1; a->step_in = 0.0; a->gate_in = -1.0; arp_start_index(a, n); }
    if (a->idx >= n) a->idx = n - 1;

    double t = 0.0;
    for (;;) {
        double next_gate = a->gate_in >= 0.0 ? a->gate_in : 1e18;
        double next_step = a->step_in;
        double nt = next_gate <= next_step ? next_gate : next_step;   /* ties: gate end first */
        if (nt >= (double)frames - t) break;
        t += nt;
        a->step_in -= nt;
        if (a->gate_in >= 0.0) a->gate_in -= nt;
        int at = (int)t; if (at >= frames) at = frames - 1;
        if (next_gate <= next_step) {
            if (ne < max) { ev[ne].at = at; ev[ne].on = 0; ev[ne].note = a->cur_note; ev[ne].vel = 0; ne++; }
            a->gate_in = -1.0; a->cur_note = -1;
        } else {
            n = arp_seq_len(a); if (n == 0) break;
            if (a->idx >= n) a->idx = n - 1;
            int vel = 100;
            int note = arp_seq_note(a, a->idx, &vel);
            if (a->gate_in >= 0.0 && a->cur_note >= 0 && ne < max) {   /* still sounding: close it before the next */
                ev[ne].at = at; ev[ne].on = 0; ev[ne].note = a->cur_note; ev[ne].vel = 0; ne++;
            }
            a->gate_in = -1.0; a->cur_note = -1;
            if (note != ARP_REST) {
                if (ne < max) { ev[ne].at = at; ev[ne].on = 1; ev[ne].note = note; ev[ne].vel = vel; ne++; }
                a->cur_note = note; a->gate_in = gate_len;
            }
            a->step_in += step_len;
            arp_advance(a, n);
        }
    }
    double rest = (double)frames - t;
    a->step_in -= rest;
    if (a->gate_in >= 0.0) a->gate_in -= rest;
    return ne;
}

#endif
