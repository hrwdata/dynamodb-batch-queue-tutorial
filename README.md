# Queueing Tutorial: Batch Scheduling with Discrete-Event Simulation

This repository is a simple tutorial for a canonical database-engineering problem: a nightly maintenance queue where ETL jobs, refreshes, backfills, and index work compete for a limited execution window.

The repository is intentionally **DynamoDB-centric**. It uses DynamoDB as a workload catalog and status store, then queries a single batch night and runs a queueing simulation in Python to estimate delay, congestion, and overflow risk. It is a teaching example for capacity planning, not a production scheduler.

## Local-First Usage

You can run the core tutorial locally without AWS credentials or cloud resources:

```bash
pip install -r requirements.txt
python -m unittest discover -s tests -v
python tutorial.py --source local
```

## What This Tutorial Teaches

- model a nightly queue of database jobs in DynamoDB
- design the table for `Query` access by nightly batch date and requested window
- derive queueing parameters such as `lambda`, `mu`, `c`, and `rho`
- simulate wait time, queue length, and overflow risk
- compare a stable workload against an overloaded workload
- reproduce the reference scenarios with local sample data and tests

## Industry Standards

Two standards matter here:

1. For a real asynchronous work queue on AWS, the usual default is **Amazon SQS**, not DynamoDB. Standard AWS guidance emphasizes queue choice, retries, dead-letter queues, long polling, deduplication or ordering requirements, and idempotent consumers.
2. For DynamoDB workloads, the standard practice is to design for access patterns first and favor `Query` over table-wide `Scan`.

This tutorial intentionally keeps DynamoDB in the foreground because the problem is **batch scheduling analysis for database engineers**, not operational message brokering.

References:

- [Amazon SQS best practices](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-best-practices.html)
- [AWS Prescriptive Guidance: Amazon SQS](https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-integrating-microservices/sqs.html)
- [DynamoDB best practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [Query versus Scan guidance](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-query-scan.html)

## Repository Layout

```text
README.md
.gitignore
requirements.txt
aws_costs.py
sample_jobs.py
queue_analysis.py
seed_job_requests.py
tutorial.py
cleanup_demo.py
docs/
  architecture.md
  costs.md
  industry_standards.md
  results.md
infra/
  dynamodb_table.yaml
```

## Data Model

Each DynamoDB item represents one queued batch job.

- `batch_date`
- `window_job_id`
- `job_id`
- `requested_window`
- `submitted_at`
- `workload_class`
- `estimated_runtime_minutes`
- `priority`
- `requires_exclusive_lock`
- `status`

The primary key is:

- partition key: `batch_date`
- sort key: `window_job_id`, formatted as `<requested_window>#<job_id>`

Example item:

```json
{
  "batch_date": "2026-05-13",
  "window_job_id": "01:00#JOB-20260513-001",
  "job_id": "JOB-20260513-001",
  "requested_window": "01:00",
  "submitted_at": "2026-05-13T00:07:00Z",
  "workload_class": "etl",
  "estimated_runtime_minutes": 25,
  "priority": 2,
  "requires_exclusive_lock": false,
  "status": "queued"
}
```

## Core Workflow

The main tutorial path is:

`DynamoDB -> Query batch_date -> summarize arrivals and runtimes -> queue simulation -> queueing metrics`

The simulator reports:

- arrival rate `lambda`
- service rate `mu`
- worker count `c`
- utilization `rho`
- average wait
- p95 wait
- average queue length
- worker utilization
- overflow risk after the batch cutoff

Exclusive-lock jobs are treated as special blocking jobs that consume the full worker pool while they run. This keeps the example simple while making lock contention visible.

## Setup

Install the core dependencies:

```bash
pip install -r requirements.txt
```

The local tutorial path requires only Python and the packages in `requirements.txt`.

Run the local test suite:

```bash
python -m unittest discover -s tests -v
```

## Optional AWS-Backed Usage

The AWS-backed path is optional. Use it only if you want to load job requests from DynamoDB instead of the local sample dataset.

Before running AWS commands, verify that `boto3` is available:

```bash
python -c "import boto3; import seed_job_requests, cleanup_demo; print('aws-import-ok')"
```

Configure AWS credentials and region:

```bash
aws configure
```

or:

```bash
set AWS_REGION=us-east-1
```

AWS-backed examples require configured credentials, an allowed AWS account and region, DynamoDB permissions, and acceptance of possible AWS charges.

## Execution

Seed the DynamoDB table:

```bash
python seed_job_requests.py
```

Run the local tutorial. By default this prints one stable case and one overloaded case:

```bash
python tutorial.py --source local
```

Run one selected batch night from DynamoDB:

```bash
python tutorial.py --source aws --batch-date 2026-05-13 --workers 3
```

Optionally filter one requested window:

```bash
python tutorial.py --source aws --batch-date 2026-05-13 --window 02:00 --workers 3
```

## Limitations

- The sample dataset is small and instructional.
- The simulator uses a simplified dispatch policy.
- Exclusive-lock jobs are modeled as full-pool blockers for clarity.
- The tutorial is not a production scheduler.
- The tutorial is not the canonical AWS operational queue pattern; SQS is.

## Verification

The local tutorial path is intended to work without provisioning AWS resources:

```bash
python tutorial.py --source local
```

The AWS-backed path is kept separate so the core teaching flow stays lightweight and easy to review.

## References

- [DynamoDB best practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [Best practices for Query and Scan](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-query-scan.html)
- [Best practices for sort keys](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-sort-keys.html)
- [Best practices for time-series data in DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-time-series.html)
- [What is Amazon DynamoDB?](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html)
