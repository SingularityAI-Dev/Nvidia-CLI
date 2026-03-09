"""Subagent orchestration for parallel task execution."""

import asyncio
import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Callable
from datetime import datetime
from enum import Enum
import uuid


class SubagentOutcome(Enum):
    """Outcome of a subagent run."""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class SubagentRunRecord:
    """Record of a subagent run."""
    run_id: str
    child_session_key: str
    requester_session_key: str
    task: str
    agent_id: str
    model: str
    timeout_seconds: int
    created_at: float
    started_at: Optional[float] = None
    ended_at: Optional[float] = None
    outcome: Optional[SubagentOutcome] = None
    result: Optional[str] = None
    cleanup: str = "delete"  # delete, keep
    archive_at_ms: Optional[int] = None


class SubagentRegistry:
    """Registry for managing subagent runs."""

    ARCHIVE_AGE_MS = 24 * 60 * 60 * 1000  # 24 hours
    SWEEP_INTERVAL = 60  # seconds

    def __init__(self, storage_path: Optional[Path] = None):
        if storage_path is None:
            storage_path = Path.home() / ".nv-cli-config" / "subagents.json"
        self.storage_path = storage_path
        self.runs: Dict[str, SubagentRunRecord] = {}
        self.lock = asyncio.Lock()
        self._sweep_task: Optional[asyncio.Task] = None
        self._load_runs()

    def _load_runs(self):
        """Load existing runs from storage."""
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text())
                for run_id, run_data in data.items():
                    self.runs[run_id] = SubagentRunRecord(**run_data)
            except Exception:
                pass

    def _save_runs(self):
        """Save runs to storage."""
        data = {
            run_id: asdict(run) for run_id, run in self.runs.items()
        }
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.write_text(json.dumps(data, indent=2, default=str))

    async def spawn(
        self,
        parent_session: str,
        task: str,
        agent_id: str = "default",
        model: Optional[str] = None,
        timeout: int = 300,
        cleanup: str = "delete",
    ) -> str:
        """Spawn a new subagent."""
        async with self.lock:
            run_id = str(uuid.uuid4())[:8]
            child_key = f"subagent-{run_id}"

            record = SubagentRunRecord(
                run_id=run_id,
                child_session_key=child_key,
                requester_session_key=parent_session,
                task=task,
                agent_id=agent_id,
                model=model or "default",
                timeout_seconds=timeout,
                created_at=time.time(),
                cleanup=cleanup,
            )
            self.runs[run_id] = record
            self._save_runs()

            # Start execution
            asyncio.create_task(self._execute_subagent(run_id))

            return run_id

    async def _execute_subagent(self, run_id: str):
        """Execute a subagent."""
        record = self.runs.get(run_id)
        if not record:
            return

        record.started_at = time.time()

        try:
            # Simulate subagent execution
            # In real implementation, this would spawn a new agent instance
            result = await asyncio.wait_for(
                self._run_subagent_task(record),
                timeout=record.timeout_seconds
            )
            record.outcome = SubagentOutcome.SUCCESS
            record.result = result

        except asyncio.TimeoutError:
            record.outcome = SubagentOutcome.TIMEOUT
            record.result = "Timeout"
        except Exception as e:
            record.outcome = SubagentOutcome.ERROR
            record.result = str(e)
        finally:
            record.ended_at = time.time()
            self._save_runs()

            # Announce completion
            await self._announce_completion(record)

            # Schedule cleanup
            if record.cleanup == "delete":
                record.archive_at_ms = (
                    int(time.time() * 1000) + self.ARCHIVE_AGE_MS
                )

    async def _run_subagent_task(self, record: SubagentRunRecord) -> str:
        """Run the actual subagent task."""
        # Placeholder - real implementation would:
        # 1. Load the specified agent config
        # 2. Create a ReActAgent with isolated context
        # 3. Execute the task
        # 4. Return results
        await asyncio.sleep(0.1)  # Simulate work
        return f"Completed: {record.task}"

    async def _announce_completion(self, record: SubagentRunRecord):
        """Announce subagent completion to parent."""
        # In real implementation, this would send a message
        # to the parent session or trigger a callback
        pass

    def get_run(self, run_id: str) -> Optional[SubagentRunRecord]:
        """Get a run by ID."""
        return self.runs.get(run_id)

    def get_active_runs(self, parent_session: Optional[str] = None) -> List[SubagentRunRecord]:
        """Get active runs, optionally filtered by parent."""
        active = [
            run for run in self.runs.values()
            if run.outcome is None  # Still running
        ]
        if parent_session:
            active = [
                run for run in active
                if run.requester_session_key == parent_session
            ]
        return active

    def list_runs(self, parent_session: Optional[str] = None) -> List[Dict]:
        """List all runs."""
        runs = list(self.runs.values())
        if parent_session:
            runs = [
                run for run in runs
                if run.requester_session_key == parent_session
            ]
        return [asdict(r) for r in runs]

    async def start_sweeper(self):
        """Start the background sweeper."""
        self._sweep_task = asyncio.create_task(self._sweep_loop())

    async def stop_sweeper(self):
        """Stop the background sweeper."""
        if self._sweep_task:
            self._sweep_task.cancel()
            try:
                await self._sweep_task
            except asyncio.CancelledError:
                pass

    async def _sweep_loop(self):
        """Background loop to cleanup old runs."""
        while True:
            try:
                await asyncio.sleep(self.SWEEP_INTERVAL)
                await self._sweep()
            except asyncio.CancelledError:
                break
            except Exception:
                pass

    async def _sweep(self):
        """Cleanup old runs."""
        now_ms = int(time.time() * 1000)
        to_delete = [
            run_id for run_id, run in self.runs.items()
            if run.archive_at_ms and run.archive_at_ms < now_ms
        ]
        if to_delete:
            async with self.lock:
                for run_id in to_delete:
                    del self.runs[run_id]
                self._save_runs()