from contextlib import contextmanager
from typing import Generator

from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn
)

from devclean.domain.events import Event, AnalyzerStarted, AnalyzerCompleted, ItemDiscovered
from devclean.application.events.event_bus import EventSubscriber


class ProgressSubscriber(EventSubscriber):
    """
    Subscribes to domain events and updates a Rich Progress bar.
    Designed to be used as a context manager so the UI updates cleanly.
    """

    def __init__(self) -> None:
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            transient=True,
        )
        self.task_id = None
        self.items_found = 0
        self.bytes_found = 0

    def _format_bytes(self, size_bytes: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    def handle(self, event: Event) -> None:
        if self.task_id is None:
            return

        if isinstance(event, AnalyzerStarted):
            self.progress.update(
                self.task_id, 
                description=f"[cyan]Scanning {event.analyzer_name}...[/cyan] | Items: {self.items_found} | Reclaim: {self._format_bytes(self.bytes_found)}"
            )

        elif isinstance(event, ItemDiscovered):
            self.items_found += 1
            self.bytes_found += event.item.size_bytes
            self.progress.update(
                self.task_id, 
                description=f"[cyan]Scanning {event.analyzer_name}...[/cyan] | Items: {self.items_found} | Reclaim: {self._format_bytes(self.bytes_found)}"
            )
            
        elif isinstance(event, AnalyzerCompleted):
            self.progress.update(
                self.task_id,
                description=f"[green]{event.analyzer_name} ✓[/green] | Items: {self.items_found} | Reclaim: {self._format_bytes(self.bytes_found)}"
            )

    @contextmanager
    def run(self) -> Generator[None, None, None]:
        with self.progress:
            self.task_id = self.progress.add_task("[cyan]Starting scan...[/cyan]", total=None)
            yield
            self.progress.update(self.task_id, completed=100)
            self.task_id = None
