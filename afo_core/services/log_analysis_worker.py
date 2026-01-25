import asyncio
import logging
import time
from typing import Any

from AFO.services.log_analysis import LogAnalysisService

logger = logging.getLogger("AFO.LogWorker")


class LogAnalysisWorker:
    """
    Background worker for offloading heavy log analysis.
    Prevents blocking the main API thread.
    """

    def __init__(self, output_dir: str = "logs/analysis"):
        self.service = LogAnalysisService(output_dir)
        self.queue = asyncio.Queue()
        self.is_running = False
        self.results = {}

    async def start(self):
        """Starts the worker loop."""
        if self.is_running:
            return
        self.is_running = True
        logger.info("🚀 Log Analysis Worker Started")
        asyncio.create_task(self._worker_loop())

    async def _worker_loop(self):
        while self.is_running:
            task_id, log_file = await self.queue.get()
            try:
                logger.info(f"🔄 Processing Task {task_id}: {log_file}")
                # Use a thread pool for the sync parts of the pipeline if needed
                # For now, running as is within the async context
                result = await asyncio.to_thread(self.service.run_pipeline, log_file)
                self.results[task_id] = {
                    "status": "completed",
                    "timestamp": time.time(),
                    "result": result,
                }
                logger.info(f"✅ Task {task_id} Completed")
            except Exception as e:
                logger.error(f"❌ Task {task_id} Failed: {e}")
                self.results[task_id] = {"status": "failed", "error": str(e)}
            finally:
                self.queue.task_done()

    async def enqueue(self, log_file: str) -> str:
        """Enqueues a log file for analysis."""
        task_id = f"task_{int(time.time())}"
        self.results[task_id] = {"status": "pending"}
        await self.queue.put((task_id, log_file))
        return task_id

    def get_status(self, task_id: str) -> dict[str, Any]:
        """Returns the status of a specific task."""
        return self.results.get(task_id, {"status": "not_found"})


log_worker = LogAnalysisWorker()
