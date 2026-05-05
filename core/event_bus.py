from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Callable, Awaitable
import asyncio


class EventType(Enum):
    DOT_FOUND = auto()
    NO_DOTS_FOUND = auto()
    SECTOR_OPENED = auto()
    DETAIL_LOADED = auto()
    TASK_STARTED = auto()
    TASK_COMPLETED = auto()
    TASK_FAILED = auto()
    COLONIZATION_SUCCESS = auto()
    COLONIZATION_FAILED = auto()
    ATTACK_INCOMING = auto()    # future
    RESOURCE_LOW = auto()       # future


@dataclass
class Event:
    type: EventType
    payload: dict = field(default_factory=dict)
    source: str = ""


class EventBus:
    def __init__(self):
        self._subscribers: dict[EventType, list[Callable]] = {}

    def subscribe(self, event_type: EventType, handler: Callable[[Event], Awaitable[None]]) -> None:
        self._subscribers.setdefault(event_type, []).append(handler)

    async def publish(self, event: Event) -> None:
        handlers = self._subscribers.get(event.type, [])
        if handlers:
            await asyncio.gather(*[h(event) for h in handlers], return_exceptions=True)
