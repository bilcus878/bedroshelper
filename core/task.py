from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
import uuid
import time


class TaskPriority(int, Enum):
    CRITICAL = 1    # incoming attack
    HIGH = 3        # war action
    NORMAL = 5      # colonization
    LOW = 8         # resource check
    BACKGROUND = 10


class TaskStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass
class TaskResult:
    success: bool
    message: str = ""
    data: dict = field(default_factory=dict)


class BaseTask(ABC):
    def __init__(self, priority: TaskPriority, max_retries: int = 3):
        self.priority = priority
        self.status = TaskStatus.PENDING
        self.retry_count = 0
        self.max_retries = max_retries
        self.task_id = str(uuid.uuid4())[:8]
        self.created_at = time.time()

    @abstractmethod
    async def execute(self, browser, game_state, navigator, human) -> TaskResult: ...

    async def on_failure(self, result: TaskResult) -> None:
        pass

    def can_retry(self) -> bool:
        return self.retry_count < self.max_retries

    def __lt__(self, other: "BaseTask") -> bool:
        return self.priority < other.priority
