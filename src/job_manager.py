import threading
import sqlite3
import json
import time
import os
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

# Use a relative path for the DB to avoid permissions issues
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "jobs.db"
)


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(JobManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.current_job_id = None
        self.cancel_event = threading.Event()
        self.processing_thread = None

        # Initialize DB
        self._init_db()

        # Reset any "processing" jobs to "failed" on startup (crash recovery)
        self._recover_jobs()

    def _init_db(self):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    status TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    config TEXT,
                    result TEXT,
                    error TEXT,
                    percent REAL DEFAULT 0.0,
                    log_path TEXT
                )
            """)
            conn.commit()

    def _recover_jobs(self):
        """Mark any jobs left in 'processing' state as 'failed' (crashed)."""
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "UPDATE jobs SET status = ?, error = ?, updated_at = ? WHERE status = ?",
                (
                    JobStatus.FAILED,
                    "Backend restarted unexpectedly",
                    datetime.now(),
                    JobStatus.PROCESSING,
                ),
            )
            conn.commit()

    def create_job(self, job_id: str, config: Dict[str, Any]) -> str:
        """Creates a new job record."""
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO jobs (id, status, created_at, updated_at, config) VALUES (?, ?, ?, ?, ?)",
                (
                    job_id,
                    JobStatus.PENDING,
                    datetime.now(),
                    datetime.now(),
                    json.dumps(config),
                ),
            )
            conn.commit()
        return job_id

    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        error: Optional[str] = None,
        result: Optional[Any] = None,
        percent: float = None,
    ):
        """Updates job status, error, result, or progress."""
        with sqlite3.connect(DB_PATH) as conn:
            updates = ["status = ?", "updated_at = ?"]
            params = [status, datetime.now()]

            if error is not None:
                updates.append("error = ?")
                params.append(error)

            if result is not None:
                updates.append("result = ?")
                params.append(json.dumps(result))

            if percent is not None:
                updates.append("percent = ?")
                params.append(percent)

            params.append(job_id)

            query = f"UPDATE jobs SET {', '.join(updates)} WHERE id = ?"
            conn.execute(query, params)
            conn.commit()

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    def get_active_job(self) -> Optional[Dict[str, Any]]:
        """Returns the currently processing job, if any."""
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC LIMIT 1",
                (JobStatus.PROCESSING,),
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    def start_job(self, job_id: str, task_func, *args, **kwargs):
        """
        Starts a job in a background thread.
        status_callback: function(percent, message) called by the task
        """
        if self.processing_thread and self.processing_thread.is_alive():
            raise RuntimeError("A job is already running")

        self.current_job_id = job_id
        self.cancel_event.clear()

        # Mark as processing
        self.update_job_status(job_id, JobStatus.PROCESSING)

        def worker():
            try:
                # Execute the actual task
                result = task_func(*args, **kwargs)

                if self.cancel_event.is_set():
                    self.update_job_status(job_id, JobStatus.CANCELLED)
                else:
                    self.update_job_status(
                        job_id, JobStatus.COMPLETED, result=result, percent=1.0
                    )

            except Exception as e:
                traceback.print_exc()
                self.update_job_status(job_id, JobStatus.FAILED, error=str(e))
            finally:
                self.current_job_id = None

        self.processing_thread = threading.Thread(target=worker, daemon=True)
        self.processing_thread.start()

    def cancel_current_job(self):
        if self.processing_thread and self.processing_thread.is_alive():
            self.cancel_event.set()
            return True
        return False
