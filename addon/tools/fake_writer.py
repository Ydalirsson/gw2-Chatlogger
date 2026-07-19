#!/usr/bin/env python3
"""Append sample GW2 chat lines (JSON Lines) to a file, to exercise the viewer
without running the game/addon.

Usage:
    python fake_writer.py [path] [--interval SECONDS] [--once]

Default path mirrors where the addon writes during a real build:
    <repo>/addon/build/gw2chatlogger.jsonl
"""
import argparse
import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path

# (channel, text, account, character, subgroup [255 = whole squad], broadcast)
SAMPLES = [
    ("Squad", "commander stack on me", ":Kevin.1234", "Kevin Stormcaller", 255, True),
    ("Squad", "mesmer port is up", ":Aria.5678", "Aria Nightsong", 1, False),
    ("Party", "need a heal please", ":Tom.4210", "Tom Ironfist", 0, False),
    ("Squad", "reflects for the bullets", ":Lena.9012", "Lena Windrunner", 2, False),
    ("Party", "gg wp everyone \U0001F389", ":Sam.3344", "Sam Brightblade", 0, False),
    ('Squad', 'edge case: "quotes", back\\slash, ümlauts', ":Uwe.7788", "Ûwe Groß", 3, False),
]


def make_entry(sample):
    channel, text, account, character, subgroup, broadcast = sample
    now = datetime.now()
    return {
        "recv_time": now.strftime("%Y-%m-%dT%H:%M:%S"),
        "channel": channel,
        "channel_id": 1,
        "subgroup": None if subgroup == 255 else subgroup,
        "broadcast": broadcast,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "account": account,
        "character": character,
        "text": text,
    }


def append(path, sample):
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(make_entry(sample), ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    default = Path(__file__).resolve().parents[1] / "build" / "gw2chatlogger.jsonl"
    parser.add_argument("path", nargs="?", default=str(default))
    parser.add_argument("--interval", type=float, default=1.5, help="seconds between lines")
    parser.add_argument("--once", action="store_true", help="write each sample once and exit")
    args = parser.parse_args()

    path = Path(args.path)
    path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Appending sample chat to {path}")

    if args.once:
        for sample in SAMPLES:
            append(path, sample)
        print(f"Wrote {len(SAMPLES)} lines.")
        return

    print("Streaming (Ctrl+C to stop)...")
    try:
        while True:
            sample = random.choice(SAMPLES)
            append(path, sample)
            print(f"  + [{sample[0]}] {sample[3]}: {sample[1]}")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
