from modules.base_module import BaseModule


class WarModule(BaseModule):
    """
    STUB — not implemented yet.
    Will handle: incoming attacks, unit dispatching, defense.
    Priority: CRITICAL (1) — preempts colonization tasks.
    """

    async def setup(self) -> None:
        pass   # will subscribe to ATTACK_INCOMING when implemented

    async def teardown(self) -> None:
        pass
