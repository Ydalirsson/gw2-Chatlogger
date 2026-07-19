// Minimal, self-contained transcription of the parts of unofficial_extras'
// Definitions.h that this addon actually uses.
//
// Struct field layouts match the official header EXACTLY (ABI-critical): the game
// writes/reads these buffers, so any layout mismatch would corrupt the data the
// ChatMessageCallback receives. Callbacks we do not use are kept as void* — a
// function pointer and a void* are the same size on x64, so this preserves struct
// size without pulling in the KeyBinds / Language / magic_enum dependencies of the
// full header.
//
// Source (MIT, Krappa322):
//   https://github.com/Krappa322/arcdps_unofficial_extras_releases/blob/master/Definitions.h
#pragma once

#include <cstdint>

// Whether a message was sent in a party or a squad. Note: party chat sent while in
// a squad is reported as ChannelType::Squad (see the upstream header comment).
enum class ChannelType : uint8_t {
    Party = 0,
    Squad = 1,
    _Reserved = 2,
    Invalid = 3,
};

// A single party/squad chat message. All strings are only valid for the duration
// of the callback, so they must be copied immediately. Lengths are provided and
// should be used (the strings are also null-terminated, but using the length is
// safest).
struct SquadMessageInfo {
    uint32_t ChannelId;         // distinguishes different squads/channels
    ChannelType Type;           // Party or Squad
    uint8_t Subgroup;           // UINT8_MAX if sent to the entire squad
    uint8_t IsBroadcast;        // low bit set => broadcast; upper bits reserved
    uint8_t _Unused1;           // padding

    const char* Timestamp;      // ISO8601, server receive time, e.g. 2022-07-09T11:45:24.888Z
    uint64_t TimestampLength;

    const char* AccountName;    // includes leading ':'
    uint64_t AccountNameLength;

    const char* CharacterName;
    uint64_t CharacterNameLength;

    const char* Text;           // message content
    uint64_t TextLength;
};

// Passed to the subscriber init export by unofficial_extras.
struct ExtrasAddonInfo {
    uint32_t ApiVersion;        // current: 2
    uint32_t MaxInfoVersion;    // highest ExtrasSubscriberInfo version supported (current: 4)
    const char* StringVersion;
    const char* SelfAccountName; // valid only for the duration of the init call
    void* ExtrasHandle;          // HMODULE of the unofficial_extras dll
};

typedef void (*ChatMessageCallbackSignature)(const SquadMessageInfo* pChatMessage);

struct ExtrasSubscriberInfoHeader {
    uint32_t InfoVersion;       // set to the version of the struct you fill in
    uint32_t _Unused1;          // padding
};

// InfoVersion = 1
struct ExtrasSubscriberInfoV1 : ExtrasSubscriberInfoHeader {
    const char* SubscriberName;     // must outlive the addon
    void* SquadUpdateCallback;      // unused
    void* LanguageChangedCallback;  // unused
    void* KeyBindChangedCallback;   // unused
};

// InfoVersion = 2 (adds chat messages)
struct ExtrasSubscriberInfoV2 : ExtrasSubscriberInfoV1 {
    ChatMessageCallbackSignature ChatMessageCallback;
};
