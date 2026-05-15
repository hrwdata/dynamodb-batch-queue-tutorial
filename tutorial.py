import argparse
import math
import os
from decimal import Decimal
from typing import Optional

from aws_costs import ddb_read_cost, money
from queue_analysis import minutes_from_hhmm, simulate_batch, summarize_jobs
from sample_jobs import (
    BATCH_END,
    BATCH_START,
    DEFAULT_BATCH_DATE,
    available_batch_dates,
    get_sample_job_requests,
)


TABLE_NAME = "db_batch_window_requests"
REGION = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"
DEFAULT_LOCAL_SCENARIOS = [
    ("Stable baseline", "2026-05-13", 3),
    ("Overloaded stress test", "2026-05-14", 2),
]


def load_job_requests_from_aws(batch_date: str, window_prefix: Optional[str]):
    try:
        import boto3
        from boto3.dynamodb.conditions import Key
    except ImportError as exc:
        raise RuntimeError(
            "boto3 is required for --source aws. Install dependencies with "
            "'pip install -r requirements.txt'."
        ) from exc

    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(TABLE_NAME)
    items = []
    read_request_units = Decimal("0")
    key_expression = Key("batch_date").eq(batch_date)
    if window_prefix:
        key_expression &= Key("window_job_id").begins_with(f"{window_prefix}#")

    query_kwargs = {
        "KeyConditionExpression": key_expression,
        "ReturnConsumedCapacity": "TOTAL",
    }

    while True:
        response = table.query(**query_kwargs)
        items.extend(response.get("Items", []))
        read_request_units += Decimal(
            str(response.get("ConsumedCapacity", {}).get("CapacityUnits", 0))
        )
        last_evaluated_key = response.get("LastEvaluatedKey")
        if not last_evaluated_key:
            break
        query_kwargs["ExclusiveStartKey"] = last_evaluated_key

    return items, read_request_units


def load_job_requests(source: str, batch_date: str, window_prefix: Optional[str]):
    if source == "local":
        jobs = get_sample_job_requests(batch_date=batch_date, window_prefix=window_prefix)
        print(f"Loading local sample job requests for {batch_date}.")
        return jobs, Decimal("0")

    print(
        f"Loading job requests from DynamoDB table {TABLE_NAME} in {REGION} "
        f"for batch_date={batch_date}."
    )
    return load_job_requests_from_aws(batch_date, window_prefix)


def print_job_summary(summary):
    print("Demand by requested window")
    for window, count in sorted(summary["window_counts"].items()):
        print(f"{window}: {count}")
    print()

    print("Workload mix")
    for workload, count in sorted(summary["workload_counts"].items()):
        print(f"{workload}: {count}")
    print()


def print_metrics(summary, simulation, workers: int, batch_start: str, batch_end: str):
    horizon_hours = (
        minutes_from_hhmm(batch_end) - minutes_from_hhmm(batch_start)
    ) / 60.0
    horizon_hours = max(horizon_hours, 1.0)
    avg_runtime = summary["avg_runtime_minutes"]
    service_rate = 60.0 / avg_runtime if avg_runtime else 0.0
    arrival_rate = summary["job_count"] / horizon_hours
    rho = (
        arrival_rate / (workers * service_rate)
        if workers > 0 and service_rate > 0
        else math.inf
    )

    print("Queueing parameters")
    print(f"lambda={arrival_rate:.2f} jobs/hour")
    print(f"mu={service_rate:.2f} jobs/hour/worker")
    print(f"workers={workers}")
    print(f"rho={rho:.2f}")
    print()

    print("Simulation results")
    print(f"average_wait_minutes={simulation['average_wait_minutes']:.2f}")
    print(f"p95_wait_minutes={simulation['p95_wait_minutes']:.2f}")
    print(f"average_queue_length={simulation['average_queue_length']:.2f}")
    print(f"max_queue_length={simulation['max_queue_length']}")
    print(f"worker_utilization={simulation['worker_utilization']:.2%}")
    print(f"overflow_jobs={simulation['overflow_jobs']}")
    print(f"overflow_risk={simulation['overflow_risk']:.2%}")
    print(f"queue_drained_minute={simulation['queue_drained_minute']}")
    print()


def analyze_case(
    label: str,
    source: str,
    batch_date: str,
    workers: int,
    window_prefix: Optional[str],
    batch_start: str,
    batch_end: str,
):
    print(f"Scenario: {label}")
    print(f"batch_date={batch_date}")
    if window_prefix:
        print(f"window_filter={window_prefix}")
    print()

    jobs, read_request_units = load_job_requests(source, batch_date, window_prefix)
    summary = summarize_jobs(jobs)

    if source == "aws":
        read_cost = ddb_read_cost(read_request_units)
        print(
            "DynamoDB read request units: "
            f"{read_request_units} | raw request cost: {money(read_cost)}"
        )
        print()
    else:
        print("AWS service cost in this run: $0.00000000")
        print()

    if summary["job_count"] == 0:
        print("No queued jobs matched the selected batch date and window.")
        print()
        return

    print(f"jobs_loaded={summary['job_count']}")
    print(f"average_runtime_minutes={summary['avg_runtime_minutes']:.2f}")
    print(f"exclusive_lock_jobs={summary['exclusive_jobs']}")
    print(f"high_priority_jobs={summary['high_priority_jobs']}")
    print()

    print_job_summary(summary)
    simulation = simulate_batch(jobs, workers=workers, batch_start=batch_start, batch_end=batch_end)
    print_metrics(summary, simulation, workers, batch_start, batch_end)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["aws", "local"], default="local")
    parser.add_argument("--batch-date")
    parser.add_argument("--window")
    parser.add_argument("--workers", type=int)
    parser.add_argument("--batch-start", default=BATCH_START)
    parser.add_argument("--batch-end", default=BATCH_END)
    return parser.parse_args()


def main():
    args = parse_args()

    if args.source == "local" and not args.batch_date and args.workers is None:
        for index, (label, batch_date, workers) in enumerate(DEFAULT_LOCAL_SCENARIOS):
            if index:
                print("-" * 60)
            analyze_case(
                label=label,
                source="local",
                batch_date=batch_date,
                workers=workers,
                window_prefix=args.window,
                batch_start=args.batch_start,
                batch_end=args.batch_end,
            )
        return

    batch_date = args.batch_date or DEFAULT_BATCH_DATE
    workers = args.workers or 3
    analyze_case(
        label="Selected run",
        source=args.source,
        batch_date=batch_date,
        workers=workers,
        window_prefix=args.window,
        batch_start=args.batch_start,
        batch_end=args.batch_end,
    )
    if args.source == "local":
        print("Available sample batch dates:")
        for value in available_batch_dates():
            print(f"- {value}")


if __name__ == "__main__":
    main()
