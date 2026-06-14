# Industry Standards

## Operational AWS Queueing

For real asynchronous producer-consumer work queues on AWS, the standard first answer is usually **Amazon SQS**.

Common operational expectations:

- choose `Standard` versus `FIFO` based on ordering and deduplication needs
- design consumers to be idempotent
- configure retries and dead-letter queues
- use long polling when polling directly
- monitor backlog, age of oldest message, failure counts, and redrive behavior

Sources:

- [Amazon SQS best practices](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-best-practices.html)
- [Amazon SQS queue types](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-queue-types.html)
- [AWS Prescriptive Guidance: Amazon SQS](https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-integrating-microservices/sqs.html)

## DynamoDB Standards Used Here

This repo intentionally teaches a different problem: queueing analysis for nightly database batches.

For that narrower use case, the relevant DynamoDB standards are:

- model the table from access patterns first
- prefer `Query` over table-wide `Scan`
- use a key design that naturally supports the time-oriented workload
- keep the first version simple and explicit

This tutorial follows those rules with:

- `batch_date` as the partition key
- `window_job_id` as the sort key
- optional prefix filtering by requested window

Sources:

- [DynamoDB best practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [Best practices for Query and Scan](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-query-scan.html)
- [Best practices for sort keys](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-sort-keys.html)
- [Best practices for time-series data](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-time-series.html)

## Queueing Analysis Scope

This repository focuses on a finite nightly planning window, not on closed-form results for a textbook steady-state queue.

The core method is a discrete-event simulation that makes the scheduling rules explicit:

- arrivals are tied to requested windows
- service times are taken from the sample workload catalog
- worker count is fixed for each run
- exclusive-lock jobs temporarily consume the full worker pool

That scope keeps the tutorial aligned with the code in the repository and makes the reference results reproducible from the sample data.
