from copy import deepcopy
from typing import Optional


BATCH_START = "01:00"
BATCH_END = "05:00"
DEFAULT_BATCH_DATE = "2026-05-13"


def build_job(
    batch_date: str,
    sequence: int,
    requested_window: str,
    workload_class: str,
    estimated_runtime_minutes: int,
    priority: int,
    requires_exclusive_lock: bool,
    status: str = "queued",
):
    job_id = f"JOB-{batch_date.replace('-', '')}-{sequence:03d}"
    submitted_hour = max(0, int(requested_window[:2]) - 1)
    submitted_minute = (sequence * 7) % 60
    return {
        "batch_date": batch_date,
        "window_job_id": f"{requested_window}#{job_id}",
        "job_id": job_id,
        "requested_window": requested_window,
        "submitted_at": f"{batch_date}T{submitted_hour:02d}:{submitted_minute:02d}:00Z",
        "workload_class": workload_class,
        "estimated_runtime_minutes": estimated_runtime_minutes,
        "priority": priority,
        "requires_exclusive_lock": requires_exclusive_lock,
        "status": status,
    }


BATCH_SPECS = {
    "2026-05-11": [
        ("01:00", "etl", 25, 2, False),
        ("01:00", "refresh", 20, 2, False),
        ("01:00", "backfill", 40, 3, True),
        ("02:00", "etl", 25, 2, False),
        ("02:00", "index_maintenance", 35, 3, True),
        ("02:00", "refresh", 20, 2, False),
        ("03:00", "etl", 25, 2, False),
        ("03:00", "refresh", 20, 2, False),
    ],
    "2026-05-12": [
        ("01:00", "etl", 30, 2, False),
        ("01:00", "refresh", 22, 2, False),
        ("01:00", "backfill", 45, 3, True),
        ("02:00", "etl", 30, 2, False),
        ("02:00", "etl", 25, 2, False),
        ("02:00", "refresh", 25, 2, False),
        ("02:00", "index_maintenance", 40, 3, True),
        ("03:00", "etl", 25, 2, False),
        ("03:00", "refresh", 20, 2, False),
    ],
    "2026-05-13": [
        ("01:00", "etl", 25, 2, False),
        ("01:00", "refresh", 20, 2, False),
        ("01:00", "backfill", 50, 3, True),
        ("01:00", "etl", 25, 2, False),
        ("02:00", "etl", 25, 2, False),
        ("02:00", "refresh", 20, 2, False),
        ("02:00", "index_maintenance", 35, 3, True),
        ("03:00", "etl", 25, 2, False),
        ("03:00", "refresh", 20, 2, False),
        ("03:00", "etl", 25, 2, False),
    ],
    "2026-05-14": [
        ("01:00", "backfill", 80, 4, True),
        ("01:00", "index_maintenance", 70, 4, True),
        ("01:00", "etl", 40, 2, False),
        ("01:00", "refresh", 35, 2, False),
        ("01:00", "etl", 35, 2, False),
        ("02:00", "backfill", 75, 4, True),
        ("02:00", "etl", 45, 2, False),
        ("02:00", "refresh", 35, 2, False),
        ("02:00", "index_maintenance", 60, 4, True),
        ("03:00", "backfill", 70, 4, True),
        ("03:00", "etl", 45, 2, False),
        ("03:00", "refresh", 30, 2, False),
    ],
}


SAMPLE_JOB_REQUESTS = []
for batch_date, specs in BATCH_SPECS.items():
    for sequence, spec in enumerate(specs, start=1):
        SAMPLE_JOB_REQUESTS.append(build_job(batch_date, sequence, *spec))


def available_batch_dates():
    return sorted(BATCH_SPECS)


def get_sample_job_requests(
    batch_date: Optional[str] = None, window_prefix: Optional[str] = None
):
    jobs = SAMPLE_JOB_REQUESTS
    if batch_date:
        jobs = [job for job in jobs if job["batch_date"] == batch_date]
    if window_prefix:
        jobs = [job for job in jobs if job["requested_window"] == window_prefix]
    return [deepcopy(job) for job in jobs]
