import heapq
from collections import Counter
from decimal import Decimal
from math import ceil
from statistics import mean


def minutes_from_hhmm(value: str) -> int:
    hours, minutes = value.split(":")
    return int(hours) * 60 + int(minutes)


def normalize_job_record(item):
    normalized = dict(item)
    normalized["estimated_runtime_minutes"] = int(
        normalized["estimated_runtime_minutes"]
    )
    normalized["priority"] = int(normalized["priority"])
    if isinstance(normalized["requires_exclusive_lock"], Decimal):
        normalized["requires_exclusive_lock"] = bool(
            int(normalized["requires_exclusive_lock"])
        )
    return normalized


def summarize_jobs(jobs):
    if not jobs:
        return {
            "job_count": 0,
            "window_counts": Counter(),
            "workload_counts": Counter(),
            "avg_runtime_minutes": 0.0,
            "exclusive_jobs": 0,
            "high_priority_jobs": 0,
        }

    normalized = [normalize_job_record(job) for job in jobs]
    return {
        "job_count": len(normalized),
        "window_counts": Counter(job["requested_window"] for job in normalized),
        "workload_counts": Counter(job["workload_class"] for job in normalized),
        "avg_runtime_minutes": mean(
            job["estimated_runtime_minutes"] for job in normalized
        ),
        "exclusive_jobs": sum(
            1 for job in normalized if job["requires_exclusive_lock"]
        ),
        "high_priority_jobs": sum(1 for job in normalized if job["priority"] >= 3),
    }


def percentile(values, pct: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, ceil((pct / 100.0) * len(ordered)) - 1)
    return float(ordered[index])


def _dispatch_jobs(current_minute, waiting, active, workers, sequence):
    scheduled = []

    while waiting:
        waiting.sort(
            key=lambda job: (-job["priority"], job["arrival_minute"], job["job_id"])
        )
        used_workers = sum(item[2] for item in active)
        available_workers = workers - used_workers
        if available_workers <= 0:
            break

        active_has_exclusive = any(item[3]["requires_exclusive_lock"] for item in active)
        exclusive_waiting = any(job["requires_exclusive_lock"] for job in waiting)
        if active_has_exclusive:
            break

        if exclusive_waiting:
            if active:
                break
            next_index = next(
                index for index, job in enumerate(waiting) if job["requires_exclusive_lock"]
            )
            job = waiting.pop(next_index)
            workers_used = workers
        else:
            job = waiting.pop(0)
            workers_used = 1

        scheduled_job = {
            "job_id": job["job_id"],
            "requested_window": job["requested_window"],
            "workload_class": job["workload_class"],
            "requires_exclusive_lock": job["requires_exclusive_lock"],
            "priority": job["priority"],
            "arrival_minute": job["arrival_minute"],
            "runtime_minutes": job["estimated_runtime_minutes"],
            "start_minute": current_minute,
            "finish_minute": current_minute + job["estimated_runtime_minutes"],
            "wait_minutes": current_minute - job["arrival_minute"],
            "workers_used": workers_used,
        }
        heapq.heappush(
            active,
            (
                scheduled_job["finish_minute"],
                sequence,
                workers_used,
                scheduled_job,
            ),
        )
        scheduled.append(scheduled_job)
        sequence += 1

    return sequence, scheduled


def simulate_batch(jobs, workers: int, batch_start: str, batch_end: str):
    normalized = [normalize_job_record(job) for job in jobs]
    start_minute = minutes_from_hhmm(batch_start)
    end_minute = minutes_from_hhmm(batch_end)
    horizon_minutes = max(1, end_minute - start_minute)

    arrivals = []
    for job in normalized:
        arrivals.append(
            {
                **job,
                "arrival_minute": max(
                    0, minutes_from_hhmm(job["requested_window"]) - start_minute
                ),
            }
        )
    arrivals.sort(key=lambda job: (job["arrival_minute"], -job["priority"], job["job_id"]))

    waiting = []
    active = []
    completed = []
    arrival_index = 0
    current_minute = 0
    sequence = 0
    queue_area = 0.0
    max_queue_length = 0
    last_observed_minute = 0

    while arrival_index < len(arrivals) or waiting or active:
        next_arrival = (
            arrivals[arrival_index]["arrival_minute"]
            if arrival_index < len(arrivals)
            else None
        )
        next_completion = active[0][0] if active else None

        candidates = [value for value in (next_arrival, next_completion) if value is not None]
        if not candidates:
            break

        next_minute = min(candidates)
        queue_area += len(waiting) * max(
            0, min(next_minute, horizon_minutes) - min(last_observed_minute, horizon_minutes)
        )
        current_minute = next_minute
        last_observed_minute = next_minute

        while active and active[0][0] <= current_minute:
            finished = heapq.heappop(active)
            completed.append(finished[3])

        while arrival_index < len(arrivals) and arrivals[arrival_index]["arrival_minute"] <= current_minute:
            waiting.append(arrivals[arrival_index])
            arrival_index += 1

        sequence, _ = _dispatch_jobs(current_minute, waiting, active, workers, sequence)
        max_queue_length = max(max_queue_length, len(waiting))

    if waiting and last_observed_minute < horizon_minutes:
        queue_area += len(waiting) * (horizon_minutes - last_observed_minute)

    wait_times = [job["wait_minutes"] for job in completed]
    total_busy_worker_minutes = 0
    for job in completed:
        start = min(job["start_minute"], horizon_minutes)
        finish = min(job["finish_minute"], horizon_minutes)
        total_busy_worker_minutes += max(0, finish - start) * job["workers_used"]
    overflow_jobs = sum(1 for job in completed if job["finish_minute"] > horizon_minutes)

    return {
        "scheduled_jobs": completed,
        "average_wait_minutes": mean(wait_times) if wait_times else 0.0,
        "p95_wait_minutes": percentile(wait_times, 95),
        "average_queue_length": queue_area / horizon_minutes,
        "max_queue_length": max_queue_length,
        "overflow_jobs": overflow_jobs,
        "overflow_risk": overflow_jobs / len(completed) if completed else 0.0,
        "worker_utilization": (
            total_busy_worker_minutes / (workers * horizon_minutes)
            if completed
            else 0.0
        ),
        "queue_drained_minute": max(
            (job["finish_minute"] for job in completed), default=0
        ),
    }
