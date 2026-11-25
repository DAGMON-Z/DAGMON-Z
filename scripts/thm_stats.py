"""TryHackMe stats for the profile.

The Profile Sync browser extension (github.com/DAGMON-Z/profile-sync) writes
them to profile-sync/tryhackme-<user>.json whenever they change. This turns
that file into the field names the drawing code uses. data/thm.json keeps
only the settings (user, path, privilege).
"""
import calendar
import json
import re
import time
from pathlib import Path


def load(user):
    path = Path(f"profile-sync/tryhackme-{user.lower()}.json")
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except ValueError:
        return {}
    s = data.get("stats") or {}
    rank = s.get("rank")
    top = None
    if isinstance(rank, str):  # "Top 45%"
        m = re.search(r"(\d+(?:\.\d+)?)\s*%", rank)
        top = float(m.group(1)) if m else None
        top = int(top) if top is not None and top.is_integer() else top
    synced = None
    if data.get("syncedAt"):
        try:
            synced = calendar.timegm(time.strptime(data["syncedAt"][:19], "%Y-%m-%dT%H:%M:%S"))
        except ValueError:
            pass
    stats = {
        "username": data.get("title") or user,
        "level": s.get("level"),
        "rank": rank,
        "topPercentage": top,
        "completedRoomsNumber": s.get("rooms"),
        "badgesNumber": s.get("badges"),
        "totalPoints": s.get("points"),
        "leagueTier": s.get("league"),
        "streak": s.get("streak"),
        "synced": synced,
    }
    return {k: v for k, v in stats.items() if v is not None}
