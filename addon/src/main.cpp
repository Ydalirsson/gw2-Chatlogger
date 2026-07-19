// GW2 Chat Logger - arcdps / unofficial_extras addon.
//
// Registers as an arcdps addon and subscribes to unofficial_extras' chat message
// callback. Every party/squad chat message is appended as one JSON object per line
// (JSON Lines) to "gw2chatlogger.jsonl" next to this DLL. A separate PySide6 app
// tails that file and displays it.
//
// Coverage note: unofficial_extras only exposes party/squad (+ NPC) chat. Map,
// whisper, guild and say are not available through this API.

#ifndef _WIN32_WINNT
#define _WIN32_WINNT 0x0601  // Windows 7+: needed for SRWLOCK / GetLocalTime declarations
#endif

#include <windows.h>

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <cwchar>  // _wfopen
#include <string>

#include "arcdps.h"
#include "extras_chat_api.h"

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

static const char* kAddonName = "GW2 Chat Logger";
static const char* kAddonBuild = "0.1.0";
static const uint32_t kAddonSig = 0x8bce1f3a;  // arbitrary unique id for arcdps

static HMODULE g_self = nullptr;
static uint32_t g_imguiversion = 0;
static arcdps_exports g_arc_exports;
static SRWLOCK g_lock = SRWLOCK_INIT;
static std::wstring g_log_path;

// ---------------------------------------------------------------------------
// Logging helpers
// ---------------------------------------------------------------------------

// Path to "gw2chatlogger.jsonl" in the same directory as this DLL.
static std::wstring compute_log_path() {
    wchar_t buf[MAX_PATH];
    DWORD n = GetModuleFileNameW(g_self, buf, MAX_PATH);
    std::wstring path(buf, n);
    size_t slash = path.find_last_of(L"\\/");
    if (slash != std::wstring::npos)
        path.resize(slash + 1);
    else
        path.clear();
    path += L"gw2chatlogger.jsonl";
    return path;
}

// Append `s` (len bytes, UTF-8) to `out` as an escaped JSON string body.
static void json_escape_append(std::string& out, const char* s, size_t len) {
    static const char* hex = "0123456789abcdef";
    for (size_t i = 0; i < len; ++i) {
        unsigned char c = static_cast<unsigned char>(s[i]);
        switch (c) {
            case '"':  out += "\\\""; break;
            case '\\': out += "\\\\"; break;
            case '\b': out += "\\b"; break;
            case '\f': out += "\\f"; break;
            case '\n': out += "\\n"; break;
            case '\r': out += "\\r"; break;
            case '\t': out += "\\t"; break;
            default:
                if (c < 0x20) {
                    out += "\\u00";
                    out += hex[(c >> 4) & 0xF];
                    out += hex[c & 0xF];
                } else {
                    out += static_cast<char>(c);  // pass UTF-8 bytes through unchanged
                }
        }
    }
}

// Emit "key":"value" (or "key":null when val is null). Adds a trailing comma when requested.
static void json_str_field(std::string& out, const char* key, const char* val, uint64_t len, bool comma) {
    out += '"';
    out += key;
    out += "\":";
    if (val) {
        out += '"';
        json_escape_append(out, val, static_cast<size_t>(len));
        out += '"';
    } else {
        out += "null";
    }
    if (comma) out += ',';
}

// Local wall-clock time as ISO8601 (seconds precision), e.g. 2026-07-19T22:15:03.
static std::string local_iso8601_now() {
    SYSTEMTIME st;
    GetLocalTime(&st);
    char buf[32];
    std::snprintf(buf, sizeof(buf), "%04d-%02d-%02dT%02d:%02d:%02d",
                  st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond);
    return std::string(buf);
}

// Append one already-formatted line to the log file. Serialized with an SRW lock so
// the callback stays reentrancy-safe without pulling in winpthread.
static void write_line(const std::string& line) {
    AcquireSRWLockExclusive(&g_lock);
    FILE* f = _wfopen(g_log_path.c_str(), L"ab");
    if (f) {
        fwrite(line.data(), 1, line.size(), f);
        fputc('\n', f);
        fclose(f);
    }
    ReleaseSRWLockExclusive(&g_lock);
}

// ---------------------------------------------------------------------------
// unofficial_extras chat callback
// ---------------------------------------------------------------------------

static void chat_message_callback(const SquadMessageInfo* m) {
    if (!m) return;

    std::string out;
    out.reserve(256);
    out += '{';

    const std::string recv = local_iso8601_now();
    json_str_field(out, "recv_time", recv.c_str(), recv.size(), true);

    const char* channel = (m->Type == ChannelType::Squad) ? "Squad"
                        : (m->Type == ChannelType::Party) ? "Party"
                        : "Unknown";
    json_str_field(out, "channel", channel, std::strlen(channel), true);

    out += "\"channel_id\":";
    out += std::to_string(m->ChannelId);
    out += ',';

    out += "\"subgroup\":";
    if (m->Subgroup == UINT8_MAX)
        out += "null";
    else
        out += std::to_string(static_cast<unsigned>(m->Subgroup));
    out += ',';

    out += "\"broadcast\":";
    out += (m->IsBroadcast & 1) ? "true" : "false";
    out += ',';

    json_str_field(out, "timestamp", m->Timestamp, m->TimestampLength, true);
    json_str_field(out, "account", m->AccountName, m->AccountNameLength, true);
    json_str_field(out, "character", m->CharacterName, m->CharacterNameLength, true);
    json_str_field(out, "text", m->Text, m->TextLength, false);

    out += '}';
    write_line(out);
}

// ---------------------------------------------------------------------------
// arcdps addon interface
// ---------------------------------------------------------------------------

static arcdps_exports* mod_init() {
    std::memset(&g_arc_exports, 0, sizeof(g_arc_exports));
    g_arc_exports.size = sizeof(arcdps_exports);
    g_arc_exports.sig = kAddonSig;
    g_arc_exports.imguivers = g_imguiversion;  // echo arcdps' version back; we draw no UI
    g_arc_exports.out_name = kAddonName;
    g_arc_exports.out_build = kAddonBuild;
    return &g_arc_exports;
}

static void mod_release() {
    // Nothing persistent to release: the log file is opened per write.
}

extern "C" __declspec(dllexport) void* get_init_addr(
        char* arcversionstr, void* imguicontext, void* id3dptr,
        HANDLE arcdll, void* mallocfn, void* freefn, uint32_t imguiversion) {
    (void)arcversionstr; (void)imguicontext; (void)id3dptr;
    (void)arcdll; (void)mallocfn; (void)freefn;
    g_imguiversion = imguiversion;
    return reinterpret_cast<void*>(mod_init);
}

extern "C" __declspec(dllexport) void* get_release_addr() {
    return reinterpret_cast<void*>(mod_release);
}

// ---------------------------------------------------------------------------
// unofficial_extras subscriber interface
// ---------------------------------------------------------------------------

extern "C" __declspec(dllexport) void arcdps_unofficial_extras_subscriber_init(
        const ExtrasAddonInfo* pExtrasInfo, void* pSubscriberInfo) {
    if (!pExtrasInfo || !pSubscriberInfo) return;

    // Written against ApiVersion 2. The API contract requires verifying the version
    // (ApiVersion changes are breaking) and that the buffer is large enough for the
    // ExtrasSubscriberInfo version we intend to write.
    if (pExtrasInfo->ApiVersion != 2) return;
    if (pExtrasInfo->MaxInfoVersion < 2) return;

    ExtrasSubscriberInfoV2* sub = static_cast<ExtrasSubscriberInfoV2*>(pSubscriberInfo);
    sub->InfoVersion = 2;
    sub->_Unused1 = 0;
    sub->SubscriberName = "gw2chatlogger";
    sub->SquadUpdateCallback = nullptr;
    sub->LanguageChangedCallback = nullptr;
    sub->KeyBindChangedCallback = nullptr;
    sub->ChatMessageCallback = &chat_message_callback;
}

// ---------------------------------------------------------------------------
// DLL entry
// ---------------------------------------------------------------------------

BOOL APIENTRY DllMain(HMODULE hModule, DWORD reason, LPVOID reserved) {
    (void)reserved;
    if (reason == DLL_PROCESS_ATTACH) {
        g_self = hModule;
        DisableThreadLibraryCalls(hModule);
        g_log_path = compute_log_path();
    }
    return TRUE;
}
