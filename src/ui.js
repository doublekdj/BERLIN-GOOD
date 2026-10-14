/*
 * BERLIN K-MOOD UI for Move Anything
 *
 * Uses shared sound generator UI base for consistent preset browsing.
 * Parameter editing via shadow UI hierarchy when in chain context.
 *
 * MIT License
 */

/* Shared utilities - absolute path for module location independence */
import { createSoundGeneratorUI } from '/data/UserData/schwung/shared/sound_generator_ui.mjs';

/* Create the UI with BERLIN K-MOOD-specific customizations */
const ui = createSoundGeneratorUI({
    moduleName: 'BERLIN K-MOOD',

    onInit: (state) => {
        /* BERLIN K-MOOD initialization */
    },

    onTick: (state) => {
        /* BERLIN K-MOOD per-tick updates */
    },

    onPresetChange: (preset) => {
        /* Reset voices on preset change */
        host_module_set_param('all_notes_off', '1');
    },

    showPolyphony: false,  /* BERLIN K-MOOD is monophonic */
    showOctave: true,
});

/* Export required callbacks */
globalThis.init = ui.init;
globalThis.tick = ui.tick;
globalThis.onMidiMessageInternal = ui.onMidiMessageInternal;
globalThis.onMidiMessageExternal = ui.onMidiMessageExternal;
