from abc import ABC, abstractmethod
from core.event_bus import EventBus, Event
from core.game_state import GameState
from core.scheduler import Scheduler
from core.human import HumanBehavior


class BaseModule(ABC):
    def __init__(
        self,
        event_bus: EventBus,
        game_state: GameState,
        scheduler: Scheduler,
        human: HumanBehavior,
    ):
        self.event_bus = event_bus
        self.game_state = game_state
        self.scheduler = scheduler
        self.human = human
        self.name = self.__class__.__name__

    @abstractmethod
    async def setup(self) -> None: ...

    @abstractmethod
    async def teardown(self) -> None: ...
