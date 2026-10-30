#include <cstddef>
#include <sound/snd.h>

static_assert(sizeof(snd_dsp_master_params) == 0x60,
              "master DSP parameter layout changed");
static_assert(sizeof(snd_dsp_dynamo_state) == 0xF80,
              "dynamo state layout changed");
static_assert(alignof(snd_dsp_dynamo_state) == 128,
              "dynamo state must remain 128-byte aligned");
static_assert(sizeof(snd_dsp_master_no_voice_state) == 0xF80,
              "master no-voice state layout changed");
static_assert(sizeof(snd_dsp_biquad_state) == 0x20,
              "biquad state layout changed");
static_assert(sizeof(snd_dsp_squelch_state) == 0x08,
              "squelch state layout changed");
static_assert(sizeof(snd_dsp_futz_state) == 0x48,
              "futz state layout changed");
static_assert(sizeof(snd_dsp_master_no_voice_params) == 0x1C,
              "master no-voice parameters layout changed");
static_assert(sizeof(snd_dsp_biquad_coef) == 0x14,
              "biquad coefficient layout changed");
static_assert(sizeof(snd_dsp_master_state) == 0x1000,
              "master state layout changed");
static_assert(offsetof(snd_dsp_master_state, limit) == 0x80,
              "master limiter offset changed");
static_assert(sizeof(snd_dsp_squelch_param) == 0x08,
              "squelch parameter layout changed");
static_assert(sizeof(snd_dsp_futz_param) == 0x34,
              "futz parameter layout changed");
static_assert(sizeof(snd_dsp_source_params) == 0x40,
              "source parameter layout changed");
static_assert(sizeof(snd_dsp_source_state) == 0x4C,
              "source state layout changed");

// A compiled object is sufficient: this test is an ABI/header-layering gate.
int nuke_upstream_snd_dsp_types_probe() {
    return static_cast<int>(sizeof(snd_dsp_source_state));
}
