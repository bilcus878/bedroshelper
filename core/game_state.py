from dataclasses import dataclass, field
import asyncio
import time
from typing import Optional


@dataclass
class GameState:
    current_view: str = "sector_map"
    current_sector: Optional[int] = None
    under_attack: bool = False
    consecutive_errors: int = 0
    last_successful_action: float = field(default_factory=time.time)
    credits: int = 0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

    async def update(self, **kwargs) -> None:
        async with self._lock:
            for k, v in kwargs.items():
                if hasattr(self, k):
                    setattr(self, k, v)
