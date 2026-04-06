"""Heartbeat scheduler."""

import asyncio
import time
from typing import Optional, Callable
from .heartbeat import HeartbeatManager


class HeartbeatScheduler:
    """Periodically triggers heartbeat checks."""

    def __init__(self, manager: HeartbeatManager, interval_minutes: int = 60):
        self.manager = manager
        self.interval = interval_minutes * 60  # Convert to seconds
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._callback: Optional[Callable] = None

    def set_callback(self, callback: Callable):
        """Set callback for when tasks are due."""
        self._callback = callback

    async def start(self):
        """Start the scheduler."""
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _loop(self):
        """Main loop."""
        while self._running:
            await asyncio.sleep(self.interval)
            await self._check()

    async def _check(self):
        """Check for due tasks."""
        due = self.manager.get_due_tasks()
        if due and self._callback:
            await self._callback(due)

    async def trigger_now(self):
        """Trigger check immediately."""
        due = self.manager.get_due_tasks()
        if due and self._callback:
            await self._callback(due)