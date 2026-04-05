import shutil
from pathlib import Path


def _split_name(file_path: Path) -> tuple[str, str]:
    suffix = "".join(file_path.suffixes)
    if suffix:
        stem = file_path.name[: -len(suffix)]
    else:
        stem = file_path.name
    return stem, suffix


def resolve_duplicate_path(destination_path: Path) -> Path:
    if not destination_path.exists():
        return destination_path

    stem, suffix = _split_name(destination_path)
    counter = 1

    while True:
        candidate = destination_path.with_name(f"{stem}({counter}){suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def move_file(src_path, destination_root, category, dry_run=False) -> Path:
    src = Path(src_path)
    if not src.exists():
        raise FileNotFoundError(src)

    destination_dir = Path(destination_root) / category
    destination_path = destination_dir / src.name
    destination_path = resolve_duplicate_path(destination_path)

    if dry_run:
        return destination_path

    destination_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(destination_path))
    return destination_path
