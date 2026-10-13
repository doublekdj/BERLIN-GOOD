// Berlin Mood level calibration: renders every patch with the current trim, prints the new trim table.
// Used by tools/calibrate.sh (do not run by hand). Target: loudest 200 ms of the patch at TARGET RMS.
#include <initializer_list>
#include "moog_plugin.cpp"
#include <stdio.h>
#include <vector>
int main(int argc, char **argv) {
    double target = argc > 1 ? atof(argv[1]) : 0.17;
    plugin_api_v2_t *api = move_plugin_init_v2(NULL);
    void *in = api->create_instance(".", NULL);
    int n = 14 + BERLIN_PRESET_COUNT;
    std::vector<float> trim(n);
    int16_t out[256];
    double lo = 1e9, hi = 0;
    for (int p = 0; p < n; p++) {
        char b[32]; snprintf(b, 32, "%d", p);
        api->set_param(in, "preset", b);
        api->set_param(in, "lfo_bpm", "120");
        char ar[8]; api->get_param(in, "arp_on", ar, 8);
        bool arp = atof(ar) > 0.5;
        if (arp) { uint8_t c[3][3] = {{0x90, 48, 100}, {0x90, 55, 100}, {0x90, 60, 100}}; for (int k = 0; k < 3; k++) api->on_midi(in, c[k], 3, 0); }
        else { uint8_t c[3] = {0x90, 55, 100}; api->on_midi(in, c, 3, 0); }
        double best = 0, peak = 0, acc = 0; int cnt = 0;
        const int win = 44100 / 5;
        int blocks = 44100 * 6 / 128;
        for (int blk = 0; blk < blocks; blk++) {
            api->render_block(in, out, 128);
            for (int i = 0; i < 256; i++) {
                double v = out[i] / 32768.0;
                acc += v * v; cnt++;
                if (fabs(v) > peak) peak = fabs(v);
            }
            if (cnt >= win * 2) { double r = sqrt(acc / cnt); if (blk * 128 > 4410) if (r > best) best = r; acc = 0; cnt = 0; }
        }
        api->set_param(in, "all_notes_off", "1");
        for (int k = 0; k < 400; k++) api->render_block(in, out, 128);   // let tails die
        double cur = g_preset_trim[p];
        double want = best > 1e-5 ? target / best : 1.0;
        double t = cur * want;
        // the peak after scaling must stay under the soft clip
        if (peak > 1e-5 && peak * want > 0.9) t = cur * 0.9 / peak;
        if (t < 0.01) t = 0.01;
        if (t > 24.0) t = 24.0;
        trim[p] = (float)t; if (getenv("CAL_DEBUG")) fprintf(stderr, "%3d rms %.1f dB peak %.2f trim %.2f -> %.2f\n", p, 20*log10(best+1e-9), peak, cur, t);
        if (best < lo) lo = best; if (best > hi) hi = best;
    }
    fprintf(stderr, "measured loudness range before this pass: %.1f .. %.1f dBFS\n", 20 * log10(lo), 20 * log10(hi));
    printf("/* per-patch level trim, written by tools/calibrate.sh */\nstatic const float g_preset_trim[%d] = {", n);
    for (int p = 0; p < n; p++) printf("%s%.3ff", p ? "," : "", trim[p]);
    printf("};\n");
}
