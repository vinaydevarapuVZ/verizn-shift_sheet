from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "settings" / "roster_config.json"

DEFAULT_MEMBERS = [
    "Alice",
    "Brian",
    "Chris",
    "Diana",
    "Emma",
    "Frank",
    "Grace",
    "Henry",
]

DEFAULT_HOLIDAYS = {
    "2026-10-20": "Company holiday",
    "2026-10-26": "Festival holiday",
}


def load_config(path: str | Path | None = None) -> Dict[str, object]:
    """Load editable member and holiday settings from JSON.

    This is a lightweight override layer. You can edit the JSON file without
    rerunning the scheduler logic, and the app will pick it up on the next run.
    """
    target = Path(path) if path is not None else CONFIG_FILE
    default = {
        "members": list(DEFAULT_MEMBERS),
        "holidays": dict(DEFAULT_HOLIDAYS),
    }

    if not target.exists():
        save_config(default, target)
        return default

    try:
        loaded = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default

    members = loaded.get("members") or list(DEFAULT_MEMBERS)
    holidays = loaded.get("holidays") or dict(DEFAULT_HOLIDAYS)

    return {
        "members": [str(name).strip() for name in members if str(name).strip()],
        "holidays": {str(k).strip(): str(v).strip() for k, v in holidays.items() if str(k).strip()},
    }


def save_config(data: Dict[str, object], path: str | Path | None = None) -> None:
    """Persist the current member/holiday config to disk."""
    target = Path(path) if path is not None else CONFIG_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2), encoding="utf-8")


def add_member(name: str, path: str | Path | None = None) -> List[str]:
    """Add a member name to the config and return the updated list."""
    config = load_config(path)
    cleaned = name.strip()
    if cleaned and cleaned not in config["members"]:
        config["members"].append(cleaned)
        save_config(config, path)
    return list(config["members"])


def remove_member(name: str, path: str | Path | None = None) -> List[str]:
    """Remove a member and save changes."""
    config = load_config(path)
    cleaned = name.strip()
    config["members"] = [item for item in config["members"] if item != cleaned]
    save_config(config, path)
    return list(config["members"])


def add_holiday(date_value: str, reason: str = "Holiday", path: str | Path | None = None) -> Dict[str, str]:
    """Add a holiday date and reason to the config."""
    config = load_config(path)
    key = str(date_value).strip()
    config["holidays"][key] = str(reason).strip() or "Holiday"
    save_config(config, path)
    return dict(config["holidays"])


def remove_holiday(date_value: str, path: str | Path | None = None) -> Dict[str, str]:
    """Remove a holiday date from the config."""
    config = load_config(path)
    key = str(date_value).strip()
    config["holidays"].pop(key, None)
    save_config(config, path)
    return dict(config["holidays"])
