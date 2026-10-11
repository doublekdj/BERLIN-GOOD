/*
 * Berlin Mood - effects chain (original code for this project, MIT, see LICENSE).
 *
 *   mono synth -> DRIVE -> PHASER -> DOTTED PING-PONG DELAY -> REVERB (plate/room/hall + shimmer)
 *              -> COMPRESSOR -> LIMITER -> (plugin) continuous soft clip
 *
 * Every block has its own ON/OFF; switching is crossfaded (about 10 ms) so it never clicks, and an effect
 * that is fully off costs no CPU. Plain C++, no dependencies, per-instance state, 44100 Hz, no allocation.
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

/* Continuous soft clip: linear up to 0.6, then a smooth knee that never reaches 1.0 (no steps, no overs). */
static inline float fx_softclip(float x) {
    float a = x < 0.0f ? -x : x;
    if (a <= 0.6f) return x;
    float y = 0.6f + 0.4f * tanhf((a - 0.6f) * (1.0f / 0.4f));
    return x < 0.0f ? -y : y;
}

/* ---------------- user-facing values (normalised 0..1 unless noted) ---------------- */
typedef struct {
    int dr_on, ph_on, dl_on, rv_on, cp_on, lm_on;
    int dr_type;          /* 0 saturator | 1 overdrive | 2 distortion */
    float dr_drive, dr_tone, dr_mix;
    float ph_rate, ph_depth, ph_fb, ph_mix;
    int dl_div;           /* 0 1/8. | 1 1/4. | 2 1/16. | 3 1/4 | 4 1/8 */
    float dl_fb, dl_mix, dl_tone;
    int dl_sync;          /* 0 host tempo (falls back to manual), 1 manual */
    float dl_bpm;         /* 0..1 -> 60..180 */
    int rv_type;          /* 0 plate | 1 room | 2 hall */
    float sh_decay, sh_shimmer, sh_mix, sh_damp;
    float cp_thresh, cp_ratio, cp_attack, cp_release, cp_makeup;
    float lm_ceil, lm_release;
} fx_params_t;

/* ---------------- drive ---------------- */
typedef struct { float lp, dc_x, dc_y; } fx_drive_t;

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

/* ---------------- reverb (FDN) with shimmer ---------------- */
#define RV_N 4
#define RV_LEN 8192
#define AP_LEN 1024
#define PS_LEN 4096
#define PS_WIN 2048
typedef struct {
    float line[RV_N][RV_LEN];
    int w;
    float damp_z[RV_N];
    float ap[2][AP_LEN];
    int apw[2];
    float lfo;
    float ps[PS_LEN];  /* pitch shifter (+1 octave) */
    int psw;
    float ps_phase;
    float ps_lp;
    float shim_fb;
    int last_type;
} fx_reverb_t;

/* ---------------- compressor + limiter ---------------- */
#define LM_N 32
typedef struct {
    float env, gain_cur, gain_tgt;
} fx_comp_t;
typedef struct {
    float dl[2][LM_N];
    float gbuf[LM_N];
    float gsum, env_g;
    int w;
} fx_limiter_t;

typedef struct {
    fx_params_t p;
    fx_drive_t dr;
    fx_phaser_t ph;
    fx_delay_t dl;
    fx_reverb_t rv;
    fx_comp_t cp;
    fx_limiter_t lm;
    float host_bpm; /* 0 = unknown */
    int tick, inited;
    float en[6];    /* smoothed enables: drive, phaser, delay, reverb, comp, limiter */
    /* control-rate derived (smoothed where a jump would click) */
    float dr_g, dr_comp, dr_tonec, dr_mixv;
    float ph_rate_hz, ph_depth, ph_fbk, ph_mixv;
    float dl_target, dl_fbk, dl_tonec, dl_mixv;
    float rv_g[RV_N], rv_damp, rv_shim, rv_mixv, rv_apg;
    int rv_lens[RV_N];
    float cp_thr_db, cp_ratio, cp_atk, cp_rel, cp_mk_db;
    float lm_ceil, lm_relc;
} fx_t;

/* reverb room sizes: 0 plate, 1 room, 2 hall (delay lengths in samples) */
static const int RV_LENS_T[3][RV_N] = {
    {1161, 1512, 1854, 2231},
    {601, 787, 959, 1153},
    {2111, 2749, 3371, 4057},
};
static const int AP_LENS[2] = {347, 521};

static void fx_init(fx_t *f) {
    memset(f, 0, sizeof(*f));
    f->p.dr_type = 0; f->p.dr_drive = 0.3f; f->p.dr_tone = 0.6f; f->p.dr_mix = 0.5f;
    f->p.ph_rate = 0.25f; f->p.ph_depth = 0.6f; f->p.ph_fb = 0.4f;
    f->p.dl_fb = 0.4f; f->p.dl_tone = 0.6f; f->p.dl_bpm = 0.5f;
    f->p.rv_type = 2; f->p.sh_decay = 0.5f; f->p.sh_damp = 0.5f;
    f->p.cp_thresh = 0.5f; f->p.cp_ratio = 0.4f; f->p.cp_attack = 0.3f; f->p.cp_release = 0.4f;
    f->p.lm_ceil = 0.8f; f->p.lm_release = 0.4f;
    f->dl.cur_delay = 0.75f * 0.5f * FX_SR; /* 120 BPM dotted 1/8 */
    f->cp.gain_cur = f->cp.gain_tgt = 1.0f;
    f->lm.env_g = 1.0f; f->lm.gsum = (float)LM_N;
    for (int i = 0; i < LM_N; i++) f->lm.gbuf[i] = 1.0f;
    f->rv.last_type = -1;
    for (int i = 0; i < RV_N; i++) f->rv_lens[i] = RV_LENS_T[2][i];
}

static void fx_set_host_bpm(fx_t *f, float bpm) {
    f->host_bpm = (bpm >= 30.0f && bpm <= 300.0f) ? bpm : 0.0f;
}

/* tempo used by the delay and the arpeggiator: host tempo when SYNC=HOST and the host sent one, else manual */
static float fx_get_bpm(const fx_t *f) {
    return (f->host_bpm > 0.0f && f->p.dl_sync == 0) ? f->host_bpm : (60.0f + f->p.dl_bpm * 120.0f);
}

#define FX_SM(cur, tgt) ((cur) += ((tgt) - (cur)) * 0.25f)

static void fx_update_ctrl(fx_t *f) {
    const fx_params_t *p = &f->p;
    float t;

    /* drive */
    t = powf(30.0f, p->dr_drive);
    FX_SM(f->dr_g, t);
    f->dr_comp = 1.0f / (1.0f + 0.1f * (f->dr_g - 1.0f));
    {
        float fc = 1000.0f * powf(16.0f, p->dr_tone);
        f->dr_tonec = 1.0f - expf(-2.0f * FX_PI * fc / FX_SR);
    }
    FX_SM(f->dr_mixv, p->dr_mix);

    /* phaser: 0.03 .. 3 Hz exponential */
    f->ph_rate_hz = 0.03f * powf(100.0f, p->ph_rate);
    FX_SM(f->ph_depth, p->ph_depth);
    FX_SM(f->ph_fbk, p->ph_fb * 0.9f);
    FX_SM(f->ph_mixv, p->ph_mix);

    /* delay */
    {
        static const float beats[5] = {0.75f, 1.5f, 0.375f, 1.0f, 0.5f};
        int d = p->dl_div < 0 ? 0 : (p->dl_div > 4 ? 4 : p->dl_div);
        t = beats[d] * 60.0f / fx_get_bpm(f) * FX_SR;
        while (t > (float)(DL_LEN - 8)) t *= 0.5f; /* too slow: halve until it fits */
        if (t < 64.0f) t = 64.0f;
        f->dl_target = t;
    }
    FX_SM(f->dl_fbk, p->dl_fb * 0.92f);
    {
        float fc = 800.0f * powf(15.0f, p->dl_tone); /* 800 Hz .. 12 kHz */
        f->dl_tonec = 1.0f - expf(-2.0f * FX_PI * fc / FX_SR);
    }
    FX_SM(f->dl_mixv, p->dl_mix);

    /* reverb: type sets room size, decay range, brightness and diffusion */
    {
        int ty = p->rv_type < 0 ? 0 : (p->rv_type > 2 ? 2 : p->rv_type);
        float t60, dbase, apg;
        if (ty == 0)      { t60 = 0.5f * powf(12.0f, p->sh_decay);  dbase = 2400.0f; apg = 0.72f; }
        else if (ty == 1) { t60 = 0.15f * powf(14.0f, p->sh_decay); dbase = 1000.0f; apg = 0.5f; }
        else              { t60 = 1.2f * powf(16.0f, p->sh_decay);  dbase = 1500.0f; apg = 0.6f; }
        for (int i = 0; i < RV_N; i++) {
            f->rv_lens[i] = RV_LENS_T[ty][i];
            f->rv_g[i] = powf(10.0f, -3.0f * (float)f->rv_lens[i] / (FX_SR * t60));
        }
        float dc = dbase * powf(8.0f, 1.0f - p->sh_damp);
        if (dc > 18000.0f) dc = 18000.0f;
        f->rv_damp = 1.0f - expf(-2.0f * FX_PI * dc / FX_SR);
        f->rv_apg = apg;
        /* loop gain must stay under the reverb's own sustain: the stable limit falls roughly as 1/T60 */
        f->rv_shim = p->sh_shimmer * 0.55f / t60;
        FX_SM(f->rv_mixv, p->sh_mix);
        if (f->rv.last_type != ty) {   /* different room: start from silence, no click from re-tapped lines */
            memset(f->rv.line, 0, sizeof(f->rv.line));
            memset(f->rv.damp_z, 0, sizeof(f->rv.damp_z));
            memset(f->rv.ap, 0, sizeof(f->rv.ap));
            f->rv.last_type = ty;
        }
    }

    /* compressor */
    f->cp_thr_db = -40.0f + 40.0f * p->cp_thresh;
    f->cp_ratio = 1.5f * powf(20.0f / 3.0f, p->cp_ratio);                 /* 1.5:1 .. 10:1 */
    f->cp_atk = 1.0f - expf(-1.0f / (0.001f * 0.5f * powf(120.0f, p->cp_attack) * FX_SR));   /* 0.5 .. 60 ms */
    f->cp_rel = 1.0f - expf(-1.0f / (0.001f * 20.0f * powf(40.0f, p->cp_release) * FX_SR));  /* 20 .. 800 ms */
    f->cp_mk_db = 18.0f * p->cp_makeup;

    /* limiter */
    f->lm_ceil = powf(10.0f, (-12.0f + 12.0f * p->lm_ceil) / 20.0f);
    f->lm_relc = 1.0f - expf(-1.0f / (0.001f * 20.0f * powf(25.0f, p->lm_release) * FX_SR));  /* 20 .. 500 ms */

    /* compressor gain from the envelope, at control rate */
    {
        float env_db = 20.0f * log10f(f->cp.env + 1e-9f);
        float over = env_db - f->cp_thr_db, gr;
        float slope = 1.0f - 1.0f / f->cp_ratio;
        if (over <= -3.0f) gr = 0.0f;
        else if (over >= 3.0f) gr = over * slope;
        else gr = slope * (over + 3.0f) * (over + 3.0f) / 12.0f;
        f->cp.gain_tgt = powf(10.0f, (f->cp_mk_db - gr) / 20.0f);
    }
}

static inline float fx_ap(float *buf, int *w, int len, float x, float g) {
    float d = buf[*w];
    float y = d - g * x;
    buf[*w] = x + g * y;
    if (++(*w) >= len) *w = 0;
    return y;
}

static inline float fx_drive_shape(const fx_t *f, float x) {
    float g = f->dr_g;
    switch (f->p.dr_type) {
        case 0: return tanhf(g * x + 0.15f) - 0.14888f;                           /* saturator: soft, slight even harmonics */
        case 1: return x >= 0.0f ? tanhf(g * x) : tanhf(0.7f * g * x);            /* overdrive: asymmetric */
        default: {                                                                  /* distortion: hard clip, cubic edge */
            float v = fx_clampf(g * x * 2.0f, -1.0f, 1.0f);
            return 1.5f * v - 0.5f * v * v * v;
        }
    }
}

/* process n frames: in = mono, out = stereo (the plugin applies its own gain before and a soft clip after) */
static void fx_process(fx_t *f, const float *in, float *outL, float *outR, int n) {
    fx_drive_t *dr = &f->dr;
    fx_phaser_t *ph = &f->ph;
    fx_delay_t *dl = &f->dl;
    fx_reverb_t *rv = &f->rv;
    fx_comp_t *cp = &f->cp;
    fx_limiter_t *lm = &f->lm;
    const int ons[6] = {f->p.dr_on, f->p.ph_on, f->p.dl_on, f->p.rv_on, f->p.cp_on, f->p.lm_on};

    if (!f->inited) { for (int k = 0; k < 6; k++) f->en[k] = ons[k] ? 1.0f : 0.0f; f->inited = 1; }   /* first block: no fade-in from zero */
    for (int i = 0; i < n; i++) {
        if ((f->tick++ % FX_CTRL) == 0) {
            fx_update_ctrl(f);
            for (int s = 0; s < 2; s++) {   /* phaser coefficients, two sides 90 degrees apart */
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
        for (int k = 0; k < 6; k++) f->en[k] += ((float)(ons[k] ? 1 : 0) - f->en[k]) * 0.003f;
        const float e_dr = f->en[0], e_ph = f->en[1], e_dl = f->en[2], e_rv = f->en[3], e_cp = f->en[4], e_lm = f->en[5];

        float x = in[i];
        if (!(x > -50.0f && x < 50.0f)) x = 0.0f;   /* NaN/inf guard */

        /* ---- drive ---- */
        if (e_dr > 0.0005f) {
            float w = fx_drive_shape(f, x) * f->dr_comp;
            dr->lp += (w - dr->lp) * f->dr_tonec; dr->lp = fx_flush(dr->lp);
            float y = dr->lp;
            float hp = y - dr->dc_x + 0.995f * dr->dc_y;   /* remove the DC the asymmetric shapers make */
            dr->dc_x = y; dr->dc_y = fx_flush(hp);
            x = x + (hp - x) * f->dr_mixv * e_dr;
        }

        /* ---- phaser ---- */
        float pl = x, pr = x;
        if (e_ph > 0.0005f) {
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
                o[s] = x + (y - x) * 0.5f * f->ph_mixv * e_ph;
            }
            pl = o[0]; pr = o[1];
        }

        /* ---- dotted stereo ping-pong delay ---- */
        float dlL = pl, dlR = pr;
        if (e_dl > 0.0005f || f->p.dl_on) {
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
            dlL = pl + yl * f->dl_mixv * e_dl;
            dlR = pr + yr * f->dl_mixv * e_dl;
        } else if (dl->w != 0 || dl->lp[0] != 0.0f) {
            memset(dl->buf, 0, sizeof(dl->buf));   /* fully off: drop the tail so it doesn't come back stale */
            dl->w = 0; dl->lp[0] = dl->lp[1] = 0.0f;
        }

        /* ---- reverb with shimmer ---- */
        float rl = dlL, rr = dlR;
        if (e_rv > 0.0005f || f->p.rv_on) {
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
            inj = fx_ap(rv->ap[0], &rv->apw[0], AP_LENS[0], inj, f->rv_apg);
            inj = fx_ap(rv->ap[1], &rv->apw[1], AP_LENS[1], inj, f->rv_apg);

            float r[RV_N];
            float m = sinf(2.0f * FX_PI * rv->lfo) * (f->p.rv_type == 1 ? 2.0f : 6.0f);
            for (int k = 0; k < RV_N; k++) {
                float mod = (k & 1) ? -m : m;
                float rp = (float)rv->w - (float)f->rv_lens[k] - mod;
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
            rl = dlL + wl * f->rv_mixv * e_rv;
            rr = dlR + wr * f->rv_mixv * e_rv;
        } else if (rv->w != 0 || rv->shim_fb != 0.0f) {
            memset(rv->line, 0, sizeof(rv->line)); memset(rv->damp_z, 0, sizeof(rv->damp_z));
            memset(rv->ap, 0, sizeof(rv->ap)); memset(rv->ps, 0, sizeof(rv->ps));
            rv->w = 0; rv->shim_fb = 0.0f; rv->ps_lp = 0.0f;
        }

        /* ---- compressor (stereo linked) ---- */
        {
            float pk = fabsf(rl) > fabsf(rr) ? fabsf(rl) : fabsf(rr);
            cp->env += (pk - cp->env) * (pk > cp->env ? f->cp_atk : f->cp_rel);
            cp->env = fx_flush(cp->env);
            cp->gain_cur += (cp->gain_tgt - cp->gain_cur) * 0.02f;
            float g = 1.0f + (cp->gain_cur - 1.0f) * e_cp;
            rl *= g; rr *= g;
        }

        /* ---- limiter (lookahead 32 samples) ---- */
        {
            float pk = fabsf(rl) > fabsf(rr) ? fabsf(rl) : fabsf(rr);
            float tg = pk > f->lm_ceil ? f->lm_ceil / pk : 1.0f;
            if (tg < lm->env_g) lm->env_g = tg;
            else lm->env_g += (1.0f - lm->env_g) * f->lm_relc;
            lm->gsum += lm->env_g - lm->gbuf[lm->w];
            lm->gbuf[lm->w] = lm->env_g;
            if (lm->w == 0) { float sm = 0.0f; for (int q = 0; q < LM_N; q++) sm += lm->gbuf[q]; lm->gsum = sm; }   /* no drift */
            float gs = lm->gsum * (1.0f / (float)LM_N);
            float dl_l = lm->dl[0][lm->w], dl_r = lm->dl[1][lm->w];   /* the sample from LM_N frames ago */
            lm->dl[0][lm->w] = rl; lm->dl[1][lm->w] = rr;
            lm->w = (lm->w + 1) % LM_N;
            float ge = 1.0f + (gs - 1.0f) * e_lm;
            if (e_lm > 0.0005f || f->p.lm_on) { rl = dl_l * ge; rr = dl_r * ge; }
            else { rl = dl_l; rr = dl_r; }   /* the 32-sample delay stays constant, so toggling never shifts the sound */
        }

        outL[i] = rl;
        outR[i] = rr;
    }
}

#endif
