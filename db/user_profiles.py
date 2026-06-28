import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "profiles.json")


def _load() -> dict:
    if not os.path.exists(DB_PATH):
        return {}
    with open(DB_PATH, "r") as f:
        return json.load(f)


def _save(data: dict):
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2)


def get_profile(user_id: str) -> dict | None:
    return _load().get(user_id)


def save_profile(user_id: str, conditions: list[str]):
    data = _load()
    data[user_id] = {"conditions": conditions}
    _save(data)


def has_profile(user_id: str) -> bool:
    return user_id in _load()


def get_all_profiles() -> dict:
    return _load()
