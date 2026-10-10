/*
 * Berlin Good - effects chain: Berlin School phaser -> dotted stereo ping-pong delay -> shimmer reverb.
 * Original code for this project (MIT, see LICENSE). Plain C++, no dependencies, per-instance state,
 * 44100 Hz, mono in -> stereo out, float. No allocation after fx_init (all buffers are inside the struct).
 */
#ifndef BERLIN_FX_H
#define BERLIN_FX_H

#include <math.h>
#include <string.h>

#define FX_SR 44100.0f
#define FX_PI 3.14159265358979f
#define FX_CTRL 16 /* control-rate update interval, samples */

static inline float fx_flush(float x) { return (x > -1e-15f && x < 1e-15f) ? 0.0f : x; }
static inline float fx_clampf(float x, float lo, float hi) { return x < lo ? lo : (x > hi ? hi : x); }

/* ---------------- user-facing values (all normalised 0..1 unless noted) ---------------- */
typedef struct {
    float ph_rate, ph_depth, ph_fb, ph_mix;
    int dl_div;           /* 0 1/8. | 1 1/4. | 2 1/16. | 3 1/4 | 4 1/8 */
    float dl_fb, dl_mix, dl_tone;
    int dl_sync;          /* 0 host tempo (falls back to manual), 1 manual */
    float dl_bpm;         /* 0..1 -> 60..180 */
    float sh_decay, sh_shimmer, sh_mix, sh_damp;
} fx_params_t;

/* ---------------- phaser: 6 first-order allpass stages, quadrature LFO for the two sides ---------------- */
#define PH_STAGES 6
typedef struct {
    float lfo_phase;
    float z[2][PH_STAGES];
    float fbs[2];
    float coef[2];
} fx_phaser_t;

/* ---------------- delay ---------------- */
#define DL_LEN 131072 /* power of two, ~2.97 s */
typedef struct {
    float buf[2][DL_LEN];
    int w;
    float cur_delay;   /* smoothed delay in samples */
    float lp[2];
} fx_delay_t;

/* ---------------- shimmer reverb ---------------- */
#define RV_N 4
#define RV_LEN 8192
#define AP_LEN 1024
#define PS_LEN 4096
#define PS_WIN 2048
typedef struct {
    float line[RV_N][RV_LEN];
    int w;
    float damp_z[RV_N];
    float ap[4][AP_LEN];
    int apw[4];
    float lfo;
    /* pitch shifter (+1 octave) */
    float ps[PS_LEN];
    int psw;
    float ps_phase;
    float ps_lp;
    float shim_fb;
} fx_reverb_t;

typedef struct {
    fx_params_t p;
    fx_phaser_t ph;
    fx_delay_t dl;
    fx_reverb_t rv;
    float host_bpm; /* 0 = unknown */
    int tick;
    /* control-rate derived values */
    float ph_rate_hz, ph_depth, ph_fbk, ph_mixv;
    float dl_target, dl_fbk, dl_tonec, dl_mixv;
    float rv_g[RV_N], rv_damp, rv_shim, rv_mixv;
} fx_t;

static const int RV_LENS[RV_N] = {2111, 2749, 3371, 4057};
static const int AP_LENS[4] = {347, 521, 233, 419};

static void fx_init(fx_t *f) {
    memset(f, 0, sizeof(*f));
    f->p.ph_rate = 0.25f; f->p.ph_depth = 0.6f; f->p.ph_fb = 0.4f;
    f->p.dl_fb = 0.4f; f->p.dl_tone = 0.6f; f->p.dl_bpm = 0.5f;
    f->p.sh_decay = 0.5f; f->p.sh_damp = 0.5f;
    f->dl.cur_delay = 0.75f * 0.5f * FX_SR; /* 120 BPM dotted 1/8 */
    f->ph.lfo_phase = 0.0f;
}

static void fx_set_host_bpm(fx_t *f, float bpm) {
    f->host_bpm = (bpm >= 30.0f && bpm <= 300.0f) ? bpm : 0.0f;
}

static void fx_update_ctrl(fx_t *f) {
    const fx_params_t *p = &f->p;
    /* phaser: 0.03 .. 3 Hz exponential */
    f->ph_rate_hz = 0.03f * powf(100.0f, p->ph_rate);
    f->ph_depth = p->ph_depth;
    f->ph_fbk = p->ph_fb * 0.9f;
    f->ph_mixv = p->ph_mix;

    float bpm = (f->host_bpm > 0.0f && p->dl_sync == 0) ? f->host_bpm : (60.0f + p->dl_bpm * 120.0f);
    static const float beats[5] = {0.75f, 1.5f, 0.375f, 1.0f, 0.5f};
    int d = p->dl_div < 0 ? 0 : (p->dl_div > 4 ? 4 : p->dl_div);
    float t = beats[d] * 60.0f / bpm * FX_SR;
    while (t > (float)(DL_LEN - 8)) t *= 0.5f; /* too slow: halve until it fits */
    if (t < 64.0f) t = 64.0f;
    f->dl_target = t;
    f->dl_fbk = p->dl_fb * 0.92f;
    float fc = 800.0f * powf(15.0f, p->dl_tone); /* 800 Hz .. 12 kHz */
    f->dl_tonec = 1.0f - expf(-2.0f * FX_PI * fc / FX_SR);
    f->dl_mixv = p->dl_mix;

    float t60 = 1.2f * powf(16.0f, p->sh_decay); /* 1.2 s .. 19 s */
    for (int i = 0; i < RV_N; i++)
        f->rv_g[i] = powf(10.0f, -3.0f * (float)RV_LENS[i] / (FX_SR * t60));
    float dc = 1500.0f * powf(8.0f, 1.0f - p->sh_damp); /* damp=0 bright (12k) .. damp=1 dark (1.5k) */
    f->rv_damp = 1.0f - expf(-2.0f * FX_PI * dc / FX_SR);
    /* loop gain must stay under the reverb's own sustain: the stable limit falls roughly as 1/T60 */
    f->rv_shim = p->sh_shimmer * 0.55f / t60;
    f->rv_mixv = p->sh_mix;
}

static inline float fx_ap(float *buf, int *w, int len, float x, float g) {
    float d = buf[*w];
    float y = d - g * x;
    buf[*w] = x + g * y;
    if (++(*w) >= len) *w = 0;
    return y;
}

/* process n frames: in = mono, out = interleaved-free stereo */
static void fx_process(fx_t *f, const float *in, float *outL, float *outR, int n) {
    fx_phaser_t *ph = &f->ph;
    fx_delay_t *dl = &f->dl;
    fx_reverb_t *rv = &f->rv;

    for (int i = 0; i < n; i++) {
        if ((f->tick++ % FX_CTRL) == 0) {
            fx_update_ctrl(f);
            /* phaser coefficients (two sides, 90 degrees apart) */
            for (int s = 0; s < 2; s++) {
                float ph_s = ph->lfo_phase + 0.25f * s;
                ph_s -= floorf(ph_s);
                float lfo = 0.5f - 0.5f * cosf(2.0f * FX_PI * ph_s); /* 0..1 */
                float fmin = 180.0f, fmax = 180.0f + 5200.0f * f->ph_depth;
                float fr = fmin * powf(fmax / fmin, lfo);
                float tn = tanf(FX_PI * fr / FX_SR);
                ph->coef[s] = (tn - 1.0f) / (tn + 1.0f);
            }
            ph->lfo_phase += f->ph_rate_hz * (float)FX_CTRL / FX_SR;
            if (ph->lfo_phase >= 1.0f) ph->lfo_phase -= 1.0f;
            rv->lfo += 0.31f * (float)FX_CTRL / FX_SR;
            if (rv->lfo >= 1.0f) rv->lfo -= 1.0f;
        }

        float x = in[i];

        /* ---- phaser ---- */
        float pl, pr;
        {
            float o[2];
            for (int s = 0; s < 2; s++) {
                float y = x + ph->fbs[s] * f->ph_fbk;
                for (int k = 0; k < PH_STAGES; k++) {
                    float a = ph->coef[s];
                    float z = ph->z[s][k];
                    float out = a * y + z;
                    ph->z[s][k] = fx_flush(y - a * out);
                    y = out;
                }
                ph->fbs[s] = fx_flush(y);
                o[s] = x + (y - x) * 0.5f * f->ph_mixv;
            }
            pl = o[0]; pr = o[1];
        }

        /* ---- dotted stereo ping-pong delay ---- */
        float dlL, dlR;
        {
            dl->cur_delay += (f->dl_target - dl->cur_delay) * 0.0006f;
            float rp = (float)dl->w - dl->cur_delay;
            while (rp < 0.0f) rp += (float)DL_LEN;
            int i0 = (int)rp;
            float fr = rp - (float)i0;
            int i1 = (i0 + 1) & (DL_LEN - 1);
            i0 &= (DL_LEN - 1);
            float yl = dl->buf[0][i0] + (dl->buf[0][i1] - dl->buf[0][i0]) * fr;
            float yr = dl->buf[1][i0] + (dl->buf[1][i1] - dl->buf[1][i0]) * fr;
            dl->lp[0] += (yl - dl->lp[0]) * f->dl_tonec; dl->lp[0] = fx_flush(dl->lp[0]);
            dl->lp[1] += (yr - dl->lp[1]) * f->dl_tonec; dl->lp[1] = fx_flush(dl->lp[1]);
            float mono = 0.5f * (pl + pr);
            /* input goes into the left line; each side feeds the other */
            dl->buf[0][dl->w] = mono + f->dl_fbk * dl->lp[1];
            dl->buf[1][dl->w] = f->dl_fbk * dl->lp[0];
            dl->w = (dl->w + 1) & (DL_LEN - 1);
            dlL = pl + yl * f->dl_mixv;
            dlR = pr + yr * f->dl_mixv;
        }

        /* ---- shimmer reverb ---- */
        float rl, rr;
        {
            float inm = 0.5f * (dlL + dlR);
            /* pitch-shifted (+1 octave) feedback from the previous output */
            float shifted;
            {
                rv->ps[rv->psw] = rv->shim_fb;
                float ph1 = rv->ps_phase, ph2 = ph1 + 0.5f;
                if (ph2 >= 1.0f) ph2 -= 1.0f;
                float d1 = (1.0f - ph1) * (float)PS_WIN + 2.0f, d2 = (1.0f - ph2) * (float)PS_WIN + 2.0f;
                float s1, s2;
                {
                    float rp = (float)rv->psw - d1; if (rp < 0) rp += PS_LEN;
                    int a = (int)rp; float fr = rp - a; int b = (a + 1) & (PS_LEN - 1); a &= (PS_LEN - 1);
                    s1 = rv->ps[a] + (rv->ps[b] - rv->ps[a]) * fr;
                }
                {
                    float rp = (float)rv->psw - d2; if (rp < 0) rp += PS_LEN;
                    int a = (int)rp; float fr = rp - a; int b = (a + 1) & (PS_LEN - 1); a &= (PS_LEN - 1);
                    s2 = rv->ps[a] + (rv->ps[b] - rv->ps[a]) * fr;
                }
                float w1 = sinf(FX_PI * ph1), w2 = sinf(FX_PI * ph2);
                shifted = s1 * w1 * w1 + s2 * w2 * w2;
                rv->psw = (rv->psw + 1) & (PS_LEN - 1);
                rv->ps_phase += 1.0f / (float)PS_WIN; /* ratio 2 -> read head gains 1 sample per sample */
                if (rv->ps_phase >= 1.0f) rv->ps_phase -= 1.0f;
                rv->ps_lp += (shifted - rv->ps_lp) * 0.35f; /* tame the grain edges */
                rv->ps_lp = fx_flush(rv->ps_lp);
                shifted = rv->ps_lp;
            }
            float inj = inm * 0.35f + tanhf(shifted * f->rv_shim);
            /* input diffusion */
            inj = fx_ap(rv->ap[0], &rv->apw[0], AP_LENS[0], inj, 0.6f);
            inj = fx_ap(rv->ap[1], &rv->apw[1], AP_LENS[1], inj, 0.6f);

            /* FDN: read (slightly modulated), damp, Hadamard mix, write */
            float r[RV_N];
            float m = sinf(2.0f * FX_PI * rv->lfo) * 6.0f;
            for (int k = 0; k < RV_N; k++) {
                float mod = (k & 1) ? -m : m;
                float rp = (float)rv->w - (float)RV_LENS[k] - mod;
                while (rp < 0.0f) rp += (float)RV_LEN;
                int a = (int)rp; float fr = rp - (float)a; int b = (a + 1) & (RV_LEN - 1); a &= (RV_LEN - 1);
                float v = rv->line[k][a] + (rv->line[k][b] - rv->line[k][a]) * fr;
                rv->damp_z[k] += (v - rv->damp_z[k]) * f->rv_damp;
                rv->damp_z[k] = fx_flush(rv->damp_z[k]);
                r[k] = rv->damp_z[k] * f->rv_g[k];
            }
            float h0 = 0.5f * (r[0] + r[1] + r[2] + r[3]);
            float h1 = 0.5f * (r[0] - r[1] + r[2] - r[3]);
            float h2 = 0.5f * (r[0] + r[1] - r[2] - r[3]);
            float h3 = 0.5f * (r[0] - r[1] - r[2] + r[3]);
            rv->line[0][rv->w] = h0 + inj;
            rv->line[1][rv->w] = h1 + inj;
            rv->line[2][rv->w] = h2 + inj * 0.7f;
            rv->line[3][rv->w] = h3 + inj * 0.7f;
            rv->w = (rv->w + 1) & (RV_LEN - 1);

            float wl = 0.6f * (r[0] - r[1] + r[2] - r[3]);
            float wr = 0.6f * (r[0] + r[1] - r[2] - r[3]);
            rv->shim_fb = 0.5f * (wl + wr);
            rl = dlL + wl * f->rv_mixv;
            rr = dlR + wr * f->rv_mixv;
        }

        outL[i] = rl;
        outR[i] = rr;
    }
}

#endif
