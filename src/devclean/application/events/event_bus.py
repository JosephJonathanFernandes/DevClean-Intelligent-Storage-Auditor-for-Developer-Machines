import logging
import json
from typing import Callable, Protocol, TypeVar
from collections import defaultdict

from devclean.domain.events import Event

# A generic type for our events
E = TypeVar('E', bound=Event)

class EventSubscriber(Protocol):
    def handle(self, event: Event) -> None:
        ...

class EventBus:
    """A lightweight in-memory event bus for application events."""
    
    def __init__(self) -> None:
        self._subscribers: dict[type[Event], list[Callable[[Event], None]]] = defaultdict(list)
        self._global_subscribers: list[Callable[[Event], None]] = []

    def subscribe(self, event_type: type[E], handler: Callable[[E], None]) -> None:
        """Subscribe to a specific event type."""
        self._subscribers[event_type].append(handler)

    def subscribe_all(self, handler: Callable[[Event], None]) -> None:
        """Subscribe to all events (e.g., for global logging or telemetry)."""
        self._global_subscribers.append(handler)

    def publish(self, event: Event) -> None:
        """Publish an event to all interested subscribers."""
        event_type = type(event)
        
        for handler in self._subscribers[event_type]:
            handler(event)
            
        for handler in self._global_subscribers:
            handler(event)


class LoggingSubscriber:
    """A subscriber that converts domain events into structured JSON logs."""
    
    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def handle(self, event: Event) -> None:
        """Converts the dataclass event to a dictionary and logs it as JSON."""
        # Note: In a real app we might use a robust serializer (like Pydantic or cattrs).
        # Here we do a simple vars() which works for shallow dataclasses.
        import dataclasses
        if dataclasses.is_dataclass(event):
            data = dataclasses.asdict(event)
            # Convert UUIDs to strings for JSON serialization
            data['scan_id'] = str(data['scan_id'])
            data['event_type'] = event.__class__.__name__
            
            # Remove complex objects like AuditItem from raw logs to avoid huge outputs,
            # or summarize them.
            if 'item' in data:
                data['item'] = str(data['item'].path)
                
            self._logger.debug(json.dumps(data))
