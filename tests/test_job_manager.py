import sys
import os

sys.path.append(os.getcwd())
import time
import json
from src.job_manager import JobManager, JobStatus


def test_job_manager():
    print("🚀 Testing JobManager...")

    # 1. Initialize
    mgr = JobManager()
    print("✅ Initialized JobManager")

    # 2. Create Job
    job_id = "test-job-123"
    config = {"url": "http://test.com", "style": "Hormozi"}
    mgr.create_job(job_id, config)
    print(f"✅ Created Job {job_id}")

    # 3. Verify Pending
    job = mgr.get_job(job_id)
    assert job["status"] == JobStatus.PENDING
    print("✅ Job status is PENDING")

    # 4. Start Mock Job
    def mock_worker():
        print("   [Worker] Starting...")
        time.sleep(1)
        print("   [Worker] Done")
        return "result_ok"

    mgr.start_job(job_id, mock_worker)
    print("✅ Started Job")

    # 5. Check Active
    active = mgr.get_active_job()
    assert active is not None
    assert active["id"] == job_id
    print("✅ Active Job found")

    # 6. Wait for complete
    time.sleep(2)
    job = mgr.get_job(job_id)
    assert job["status"] == JobStatus.COMPLETED
    print(f"✅ Job Completed: {job['result']}")

    # 7. Persistence Check (New Instance)
    mgr2 = JobManager()
    job2 = mgr2.get_job(job_id)
    assert job2["status"] == JobStatus.COMPLETED
    print("✅ Persistence Confirmed")


if __name__ == "__main__":
    try:
        test_job_manager()
        print("\n🎉 ALL TESTS PASSED")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
