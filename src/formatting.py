"""Shared rendering of a chat entry.

Both the Live view (HTML, colour-coded) and a recorded session (plain text) are
produced from the same helpers here so the transcript on disk matches, line for
line, what the monitor shows.
"""
import html


CHANNEL_COLORS = {
    "Party": "#4aa3ff",
    "Squad": "#3fbf6f",
    "Unknown": "#999999",
}
TIME_COLOR = "#888888"
BROADCAST_COLOR = "#f0a030"


def time_hm(recv_time: str) -> str:
    # recv_time is "YYYY-MM-DDTHH:MM:SS"; show HH:MM.
    if len(recv_time) >= 16 and recv_time[10] == "T":
        return recv_time[11:16]
    return recv_time


def channel_tag(entry: dict) -> str:
    """The bracketed label, e.g. 'Party', 'Squad', 'Squad·2'."""
    channel = entry.get("channel", "Unknown")
    tag = channel
    subgroup = entry.get("subgroup")
    if channel == "Squad" and subgroup is not None:
        tag = f"Squad·{subgroup}"
    return tag


def format_text(entry: dict, include_time: bool = True, include_channel: bool = True) -> str:
    """One plain-text transcript line, e.g. '[22:15] ★ [Squad·2] Alaric: stack'.

    include_time / include_channel control whether the [HH:MM] timestamp and the
    [channel] tag are written. The broadcast ★ and 'name: text' are always kept.
    """
    prefix = []
    if include_time:
        prefix.append(f"[{time_hm(str(entry.get('recv_time', '')))}]")
    if entry.get("broadcast"):
        prefix.append("★")
    if include_channel:
        prefix.append(f"[{channel_tag(entry)}]")
    character = entry.get("character") or entry.get("account") or "?"
    prefix.append(f"{character}: {entry.get('text') or ''}")
    return " ".join(prefix)


def format_html(entry: dict) -> str:
    """One colour-coded HTML line for the Live view."""
    channel = entry.get("channel", "Unknown")
    color = CHANNEL_COLORS.get(channel, CHANNEL_COLORS["Unknown"])
    time_str = time_hm(str(entry.get("recv_time", "")))
    character = entry.get("character") or entry.get("account") or "?"
    text = entry.get("text") or ""

    esc = html.escape
    parts = [f'<span style="color:{TIME_COLOR}">[{esc(time_str)}]</span> ']
    if entry.get("broadcast"):
        parts.append(f'<span style="color:{BROADCAST_COLOR}">★</span> ')
    parts.append(
        f'<span style="color:{color};font-weight:bold">'
        f'[{esc(channel_tag(entry))}] {esc(str(character))}:</span> '
    )
    parts.append(f"<span>{esc(str(text))}</span>")
    return "".join(parts)
