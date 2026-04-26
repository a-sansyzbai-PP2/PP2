"""
persistence.py — Save / load leaderboard and settings to JSON files.
"""

import json
import os

LEADERBOARD_FILE = "leaderboard.json"
SETTINGS_FILE    = "settings.json"

# ── Default settings ──────────────────────────────────────────────────────────
DEFAULT_SETTINGS = {
    "sound":       True,
    "car_color":   "blue",   # blue | red | green | orange | purple
    "difficulty":  "normal", # easy | normal | hard
}

# ── Settings ──────────────────────────────────────────────────────────────────

def load_settings() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
            # Fill in any missing keys with defaults
            for k, v in DEFAULT_SETTINGS.items():
                data.setdefault(k, v)
            return data
        except Exception:
            pass
    return dict(DEFAULT_SETTINGS)


def save_settings(settings: dict) -> None:
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


# ── Leaderboard ───────────────────────────────────────────────────────────────

def load_leaderboard() -> list:
    """Return list of dicts: [{name, score, distance, coins}, ...]"""
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, "r") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
        except Exception:
            pass
    return []


def save_leaderboard(entries: list) -> None:
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(entries, f, indent=2)


def add_entry(name: str, score: int, distance: int, coins: int) -> list:
    """Add a new entry, keep top-10 sorted by score, return updated list."""
    entries = load_leaderboard()
    entries.append({"name": name, "score": score,
                    "distance": distance, "coins": coins})
    entries.sort(key=lambda e: e["score"], reverse=True)
    entries = entries[:10]
    save_leaderboard(entries)
    return entries