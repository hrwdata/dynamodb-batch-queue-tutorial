# AWS Cost Guide

## Pricing Scope

The prices in this document are the published **us-east-1** list prices reviewed on **May 13, 2026**.

Published rates used in the cost formulas:

- DynamoDB on-demand write request unit: **$0.0000006250** per write request unit
- DynamoDB on-demand read request unit: **$0.0000001250** per read request unit
- DynamoDB standard table storage beyond the first 25 GB-months: **$0.25** per GB-month
- EC2 `t3.small` on-demand Linux instance: **$0.0208** per hour
- EBS `gp3` storage: **$0.08** per GB-month
- Cost Explorer console: **$0.00**
- Cost Explorer API: **$0.01** per paginated API request
- AWS Budgets monitoring: **$0.00**
- AWS Budgets action-enabled budgets: first two free, then **$0.10** per day for each additional action-enabled budget
- AWS Budgets report delivery: **$0.01** per delivered report
- AWS CloudFormation for `AWS::*` resources: **$0.00** additional service charge

## Service-by-Service Billing

### 1. CloudFormation

If the table is created from [`infra/dynamodb_table.yaml`](../infra/dynamodb_table.yaml), CloudFormation adds no separate charge for native AWS resources.

Billing begins only when the underlying AWS resources exist.

### 2. DynamoDB

The demo uses a single on-demand table: `db_batch_window_requests`.

Charges can occur in three places:

- write request units during [`seed_job_requests.py`](../seed_job_requests.py)
- read request units during [`tutorial.py`](../tutorial.py) when querying one nightly batch date
- table storage while the table exists

The scripts print request-unit consumption directly:

- `seed_job_requests.py` prints total DynamoDB write request units and the raw request charge
- `tutorial.py --source aws` prints total DynamoDB read request units and the raw request charge

The main tutorial path uses `Query`, not `Scan`, so the cost story aligns with the intended access pattern.

### 3. Core Tutorial Compute

The main queueing tutorial runs locally.

- AWS compute charge for the core simulation: **$0.00**

## Demo Cost by Action

### Action: create the table

Command paths:

- CloudFormation deployment of [`infra/dynamodb_table.yaml`](../infra/dynamodb_table.yaml)
- direct creation inside [`seed_job_requests.py`](../seed_job_requests.py)

AWS services involved:

- CloudFormation: **$0.00** additional service charge if used
- DynamoDB table resource: storage charges begin once the table exists

### Action: seed sample job requests

Command:

```bash
python seed_job_requests.py
```

AWS services involved:

- DynamoDB write request units

Raw cost formula:

`write_request_units * 0.0000006250 USD`

### Action: run the queue analysis against AWS data

Command:

```bash
python tutorial.py --source aws --batch-date 2026-05-13 --workers 3
```

AWS services involved:

- DynamoDB read request units

Raw cost formula:

`read_request_units * 0.0000001250 USD`

### Action: run the queue analysis locally

Command:

```bash
python tutorial.py --source local
```

AWS services involved:

- none

AWS cost:

- **$0.00**

## Cost Control Practices

Recommended control practices for this tutorial:

- keep the demo in one region
- use one DynamoDB table only
- keep DynamoDB in on-demand mode
- keep the main workflow query-based
- avoid backups, exports, Streams, and extra indexes unless they are part of the lesson
- delete demo resources after the exercise

## Cleanup

Delete the table directly:

```bash
python cleanup_demo.py
```

Delete the CloudFormation stack instead:

```bash
python cleanup_demo.py --stack-name db-batch-window-demo
```

## Sources

- [Amazon DynamoDB pricing](https://aws.amazon.com/dynamodb/pricing/)
- [Amazon DynamoDB developer guide](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html)
- [AWS public price list API](https://docs.aws.amazon.com/en_us/awsaccountbilling/latest/aboutv2/price-changes.html)
- [Amazon EC2 on-demand pricing](https://aws.amazon.com/ec2/pricing/on-demand/)
- [AWS CloudFormation pricing](https://aws.amazon.com/cloudformation/pricing/)
