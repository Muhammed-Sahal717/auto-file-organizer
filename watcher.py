from pathlib import Path

from utils import log, wait_for_stable_file


def organize_file(
    src_path,
    watch_path,
    rule_engine,
    dry_run=False,
    stability_checks=3,
    stability_delay=0.5,
):
    from mover import move_file

    src_path = Path(src_path)
    watch_path = Path(watch_path)
    file_name = src_path.name

    if rule_engine.should_ignore(file_name):
        log(f"Ignored temporary file: {file_name}")
        return None

    if not wait_for_stable_file(
        src_path,
        checks=stability_checks,
        delay_seconds=stability_delay,
    ):
        log(f"Skipped unstable or missing file: {file_name}", level="WARNING")
        return None

    category = rule_engine.category_for(src_path)

    try:
        destination = move_file(
            src_path=src_path,
            destination_root=watch_path,
            category=category,
            dry_run=dry_run,
        )
    except FileNotFoundError:
        log(f"File disappeared before it could be moved: {file_name}", level="WARNING")
        return None
    except OSError as exc:
        log(f"Failed to move {file_name}: {exc}", level="ERROR")
        return None

    action = "Would move" if dry_run else "Moved"
    log(f"{action} {file_name} -> {destination.relative_to(watch_path)}")
    return destination


def organize_existing_files(
    watch_path,
    rule_engine,
    dry_run=False,
    stability_checks=3,
    stability_delay=0.5,
):
    watch_path = Path(watch_path)
    organized_count = 0

    for path in sorted(watch_path.iterdir()):
        if not path.is_file():
            continue

        destination = organize_file(
            src_path=path,
            watch_path=watch_path,
            rule_engine=rule_engine,
            dry_run=dry_run,
            stability_checks=stability_checks,
            stability_delay=stability_delay,
        )
        if destination is not None:
            organized_count += 1

    return organized_count


class OrganizerEventHandler:
    def __init__(
        self,
        watch_path,
        rule_engine,
        dry_run=False,
        stability_checks=3,
        stability_delay=0.5,
    ):
        from watchdog.events import FileSystemEventHandler

        class _Handler(FileSystemEventHandler):
            def __init__(self, outer):
                super().__init__()
                self.outer = outer

            def on_created(self, event):
                self.outer.handle_created(event)

        self._handler = _Handler(self)
        self.watch_path = Path(watch_path)
        self.rule_engine = rule_engine
        self.dry_run = dry_run
        self.stability_checks = stability_checks
        self.stability_delay = stability_delay

    @property
    def handler(self):
        return self._handler

    def handle_created(self, event):
        if event.is_directory:
            return

        src_path = Path(event.src_path)
        file_name = src_path.name

        log(f"Detected file: {file_name}")
        organize_file(
            src_path=src_path,
            watch_path=self.watch_path,
            rule_engine=self.rule_engine,
            dry_run=self.dry_run,
            stability_checks=self.stability_checks,
            stability_delay=self.stability_delay,
        )


def start_watcher(
    watch_path,
    rule_engine,
    dry_run=False,
    stability_checks=3,
    stability_delay=0.5,
):
    from watchdog.observers import Observer

    event_handler = OrganizerEventHandler(
        watch_path=watch_path,
        rule_engine=rule_engine,
        dry_run=dry_run,
        stability_checks=stability_checks,
        stability_delay=stability_delay,
    )

    observer = Observer()
    observer.schedule(event_handler.handler, str(watch_path), recursive=False)
    observer.start()
    return observer
