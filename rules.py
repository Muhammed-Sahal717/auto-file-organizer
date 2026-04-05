import json
from copy import deepcopy

from utils import expand_path, get_app_root, get_extension

DEFAULT_CONFIG = {
    "rules": {
        "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"],
        "PDFs": [".pdf"],
        "Videos": [".mp4", ".mov", ".avi", ".mkv", ".webm"],
        "Documents": [".doc", ".docx", ".txt", ".rtf", ".odt"],
        "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
    },
    "default_category": "Others",
    "ignored_extensions": [".tmp", ".crdownload", ".swp", ".part"],
    "stability": {
        "checks": 3,
        "delay_seconds": 0.5,
    },
}


def _normalize_rules(rules):
    normalized = {}
    for category, extensions in rules.items():
        normalized[category] = sorted(
            {ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in extensions}
        )
    return normalized


def _merge_config(base, overrides):
    merged = deepcopy(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key].update(value)
        else:
            merged[key] = value
    return merged


def load_config(config_path=None):
    default_path = get_app_root() / "config.json"
    path = expand_path(config_path) if config_path else default_path

    config = deepcopy(DEFAULT_CONFIG)
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as handle:
                loaded = json.load(handle)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON config at {path}: {exc}") from exc
        config = _merge_config(config, loaded)
    elif config_path:
        raise FileNotFoundError(f"Config file not found: {path}")

    config["rules"] = _normalize_rules(config["rules"])
    config["default_category"] = config.get("default_category", "Others")
    config["ignored_extensions"] = [
        ext.lower() if ext.startswith(".") else f".{ext.lower()}"
        for ext in config.get("ignored_extensions", [])
    ]
    config["stability"]["checks"] = int(config["stability"].get("checks", 3))
    config["stability"]["delay_seconds"] = float(
        config["stability"].get("delay_seconds", 0.5)
    )
    return config


class RuleEngine:
    def __init__(self, rules, default_category="Others", ignored_extensions=None):
        self.rules = _normalize_rules(rules)
        self.default_category = default_category
        self.ignored_extensions = {
            ext.lower() if ext.startswith(".") else f".{ext.lower()}"
            for ext in (ignored_extensions or [])
        }
        self._extension_map = {}
        for category, extensions in self.rules.items():
            for extension in extensions:
                self._extension_map[extension] = category

    def category_for(self, file_path) -> str:
        extension = get_extension(file_path)
        return self._extension_map.get(extension, self.default_category)

    def should_ignore(self, file_name) -> bool:
        return get_extension(file_name) in self.ignored_extensions
