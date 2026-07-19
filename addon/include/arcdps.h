// Minimal arcdps addon interface.
//
// Only the pieces required to be loaded as an arcdps addon are declared here.
// The arcdps_exports layout is ABI-critical and matches the official arcdps API
// (https://www.deltaconnected.com/arcdps/api/). Field names for the unused
// callback slots are irrelevant to the ABI (each is a pointer at a fixed offset).
#pragma once

#include <cstdint>

typedef struct arcdps_exports {
    uint64_t size;            // set to sizeof(arcdps_exports)
    uint32_t sig;             // unique addon signature (non-zero)
    uint32_t imguivers;       // IMGUI_VERSION_NUM; we echo back what arcdps passed
    const char* out_name;     // shown in arcdps options
    const char* out_build;    // version string
    void* wnd_nofilter;       // unused callback slots (all left null)
    void* combat;
    void* imgui;
    void* options_tab;
    void* combat_local;
    void* wnd_filter;
    void* options_windows;
} arcdps_exports;
