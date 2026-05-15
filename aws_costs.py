from decimal import Decimal, ROUND_HALF_UP


PRICING_REGION = "us-east-1"
PRICING_EFFECTIVE_DATE = "2026-05-13"

# DynamoDB on-demand prices in us-east-1 from the AWS public price list.
DDB_WRITE_REQUEST_UNIT_USD = Decimal("0.0000006250")
DDB_READ_REQUEST_UNIT_USD = Decimal("0.0000001250")
DDB_STORAGE_GB_MONTH_USD = Decimal("0.2500000000")

# EC2 and EBS prices in us-east-1 from the AWS public price list.
EC2_T3_SMALL_HOURLY_USD = Decimal("0.0208000000")
EC2_GP3_GB_MONTH_USD = Decimal("0.0800000000")

# SageMaker Notebook / Studio-Notebook ml.t3.medium price in us-east-1.
SAGEMAKER_ML_T3_MEDIUM_HOURLY_USD = Decimal("0.0500000000")

# Cost management reference prices.
COST_EXPLORER_API_REQUEST_USD = Decimal("0.0100000000")
BUDGET_ACTION_ENABLED_EXTRA_DAILY_USD = Decimal("0.10")
BUDGET_REPORT_DELIVERY_USD = Decimal("0.01")

HOURS_PER_MONTH = Decimal("730")


def money(value: Decimal) -> str:
    rounded = value.quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)
    return f"${rounded}"


def ddb_write_cost(write_request_units) -> Decimal:
    return Decimal(str(write_request_units)) * DDB_WRITE_REQUEST_UNIT_USD


def ddb_read_cost(read_request_units) -> Decimal:
    return Decimal(str(read_request_units)) * DDB_READ_REQUEST_UNIT_USD


def gp3_storage_cost(gb: Decimal, hours: Decimal) -> Decimal:
    return gb * EC2_GP3_GB_MONTH_USD * (hours / HOURS_PER_MONTH)


def ec2_t3_small_cost(hours: Decimal) -> Decimal:
    return hours * EC2_T3_SMALL_HOURLY_USD


def sagemaker_ml_t3_medium_cost(hours: Decimal) -> Decimal:
    return hours * SAGEMAKER_ML_T3_MEDIUM_HOURLY_USD
