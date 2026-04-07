import json
from pathlib import Path
from typing import Any


PROFILE_DIR = Path(__file__).resolve().parent / "profiles"


def load_profile(profile_name: str) -> dict[str, Any]:
    """
    バリデーションを行いつつ，指定されたプロファイル名のNotionプロフィールをロードする．
    """
    profile_path = PROFILE_DIR / f"{profile_name}.json"
    if not profile_path.exists():
        raise FileNotFoundError(f"Profile not found: {profile_path}")

    with profile_path.open("r", encoding="utf-8") as f:
        profile = json.load(f)

    if not isinstance(profile, dict):
        raise ValueError(f"Invalid profile format: {profile_path}")

    required_keys = ["name", "db_id_env_key", "title_property_name", "property_types"]
    for key in required_keys:
        if key not in profile:
            raise ValueError(f"Profile missing required key '{key}': {profile_path}")

    if not isinstance(profile.get("property_types"), dict):
        raise ValueError(f"Profile 'property_types' must be object: {profile_path}")

    return profile
