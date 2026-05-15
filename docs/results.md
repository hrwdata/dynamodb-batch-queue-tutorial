# Results

Reference local run:

```text
Scenario: Stable baseline
batch_date=2026-05-13

Loading local sample job requests for 2026-05-13.
AWS service cost in this run: $0.00000000

jobs_loaded=10
average_runtime_minutes=27.00
exclusive_lock_jobs=2
high_priority_jobs=2

Demand by requested window
01:00: 4
02:00: 3
03:00: 3

Workload mix
backfill: 1
etl: 5
index_maintenance: 1
refresh: 3

Queueing parameters
lambda=2.50 jobs/hour
mu=2.22 jobs/hour/worker
workers=3
rho=0.38

Simulation results
average_wait_minutes=29.00
p95_wait_minutes=50.00
average_queue_length=1.21
max_queue_length=3
worker_utilization=61.11%
overflow_jobs=0
overflow_risk=0.00%
queue_drained_minute=160
------------------------------------------------------------
Scenario: Overloaded stress test
batch_date=2026-05-14

Loading local sample job requests for 2026-05-14.
AWS service cost in this run: $0.00000000

jobs_loaded=12
average_runtime_minutes=51.67
exclusive_lock_jobs=5
high_priority_jobs=5

Demand by requested window
01:00: 5
02:00: 4
03:00: 3

Workload mix
backfill: 3
etl: 4
index_maintenance: 2
refresh: 3

Queueing parameters
lambda=3.00 jobs/hour
mu=1.16 jobs/hour/worker
workers=2
rho=1.29

Simulation results
average_wait_minutes=246.67
p95_wait_minutes=390.00
average_queue_length=7.40
max_queue_length=10
worker_utilization=100.00%
overflow_jobs=9
overflow_risk=75.00%
queue_drained_minute=490
```

## Observations

- The stable case stays below full utilization and drains before the cutoff.
- The overloaded case crosses `rho >= 1`, accumulates a visible queue, and overruns the batch window.
- Exclusive-lock jobs make congestion worse because they block the full worker pool in this teaching model.

## Optional Extension

The PyTorch extension is intentionally separate from the main tutorial. On the tiny toy history in this repo, its holdout forecast remains poor, which is the correct teaching outcome: without real historical signal, ML does not replace first-principles queueing analysis.
