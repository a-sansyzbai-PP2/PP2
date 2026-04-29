"""
db.py — Local JSON persistence (no PostgreSQL required).

Scores are saved to 'scores.json' in the same folder as the game.
If the file doesn't exist it will be created automatically.

Same API as before:
    ensure_schema()
    save_session(username, score, level_reached)
    personal_best(username) -> int
    top10() -> list[dict]
"""

import json
import os
from datetime import datetime

SCORES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scores.json")


def _load() -> dict:
    if os.path.exists(SCORES_FILE):
        try:
            with open(SCORES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            data.setdefault("players", {})
            data.setdefault("sessions", [])
            return data
        except Exception:
            pass
    return {"players": {}, "sessions": []}


def _save(data: dict) -> None:
    try:
        with open(SCORES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[db] Could not save scores: {e}")


def ensure_schema() -> None:
    if not os.path.exists(SCORES_FILE):
        _save({"players": {}, "sessions": []})


def get_or_create_player(username: str) -> int | None:
    data = _load()
    if username in data["players"]:
        return data["players"][username]
    new_id = len(data["players"]) + 1
    data["players"][username] = new_id
    _save(data)
    return new_id


def save_session(username: str, score: int, level_reached: int) -> None:
    pid = get_or_create_player(username)
    if pid is None:
        return
    data = _load()
    data["sessions"].append({
        "player_id":     pid,
        "username":      username,
        "score":         score,
        "level_reached": level_reached,
        "played_at":     datetime.now().strftime("%Y-%m-%d"),
    })
    _save(data)


def personal_best(username: str) -> int:
    data = _load()
    scores = [s["score"] for s in data["sessions"] if s["username"] == username]
    return max(scores, default=0)


def top10() -> list[dict]:
    data = _load()
    sessions = sorted(data["sessions"], key=lambda s: s["score"], reverse=True)
    return [
        {
            "rank":     i + 1,
            "username": s["username"],
            "score":    s["score"],
            "level":    s["level_reached"],
            "date":     s["played_at"],
        }
        for i, s in enumerate(sessions[:10])
    ]