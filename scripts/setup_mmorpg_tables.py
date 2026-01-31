"""Setup MMORPG analytics tables in Glue based on mockdb schema."""
import boto3
import json
from datetime import datetime, timedelta
import random

REGION = "us-east-1"
DATABASE = "game_logs"
S3_BUCKET = "devops-agent-kb-965037532757"
S3_PREFIX = "mmorpg-data"

glue = boto3.client("glue", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)

# MMORPG 테이블 정의 (mockdb 기반)
TABLES = {
    "accounts": {
        "columns": [
            {"Name": "account_uid", "Type": "bigint"},
            {"Name": "channel_type", "Type": "int"},
            {"Name": "channel_id", "Type": "bigint"},
            {"Name": "create_date", "Type": "timestamp"},
            {"Name": "login_date", "Type": "timestamp"},
            {"Name": "logout_date", "Type": "timestamp"},
        ],
        "partition_keys": [{"Name": "dt", "Type": "string"}],
    },
    "characters": {
        "columns": [
            {"Name": "char_uid", "Type": "bigint"},
            {"Name": "account_uid", "Type": "bigint"},
            {"Name": "char_name", "Type": "string"},
            {"Name": "char_type", "Type": "int"},
            {"Name": "level", "Type": "int"},
            {"Name": "exp", "Type": "bigint"},
            {"Name": "gold", "Type": "bigint"},
            {"Name": "login_date", "Type": "timestamp"},
            {"Name": "logout_date", "Type": "timestamp"},
        ],
        "partition_keys": [{"Name": "dt", "Type": "string"}],
    },
    "hero_gacha": {
        "columns": [
            {"Name": "gacha_id", "Type": "bigint"},
            {"Name": "char_uid", "Type": "bigint"},
            {"Name": "hero_tid", "Type": "bigint"},
            {"Name": "grade", "Type": "int"},
            {"Name": "gacha_type", "Type": "string"},
            {"Name": "cost_currency", "Type": "string"},
            {"Name": "cost_amount", "Type": "bigint"},
            {"Name": "gacha_time", "Type": "timestamp"},
        ],
        "partition_keys": [{"Name": "dt", "Type": "string"}],
    },
    "currency_logs": {
        "columns": [
            {"Name": "log_id", "Type": "bigint"},
            {"Name": "char_uid", "Type": "bigint"},
            {"Name": "currency_tid", "Type": "bigint"},
            {"Name": "change_type", "Type": "string"},
            {"Name": "change_reason", "Type": "string"},
            {"Name": "before_value", "Type": "bigint"},
            {"Name": "delta_value", "Type": "bigint"},
            {"Name": "after_value", "Type": "bigint"},
            {"Name": "log_time", "Type": "timestamp"},
        ],
        "partition_keys": [{"Name": "dt", "Type": "string"}],
    },
    "quest_logs": {
        "columns": [
            {"Name": "log_id", "Type": "bigint"},
            {"Name": "char_uid", "Type": "bigint"},
            {"Name": "quest_tid", "Type": "bigint"},
            {"Name": "category1", "Type": "int"},
            {"Name": "category2", "Type": "int"},
            {"Name": "action", "Type": "string"},
            {"Name": "log_time", "Type": "timestamp"},
        ],
        "partition_keys": [{"Name": "dt", "Type": "string"}],
    },
    "attendance_logs": {
        "columns": [
            {"Name": "char_uid", "Type": "bigint"},
            {"Name": "attend_date", "Type": "string"},
            {"Name": "reward_gold", "Type": "int"},
            {"Name": "consecutive_days", "Type": "int"},
        ],
        "partition_keys": [{"Name": "dt", "Type": "string"}],
    },
}


def create_table(table_name: str, config: dict):
    """Create Glue table."""
    try:
        glue.delete_table(DatabaseName=DATABASE, Name=table_name)
        print(f"Deleted existing table: {table_name}")
    except glue.exceptions.EntityNotFoundException:
        pass

    glue.create_table(
        DatabaseName=DATABASE,
        TableInput={
            "Name": table_name,
            "StorageDescriptor": {
                "Columns": config["columns"],
                "Location": f"s3://{S3_BUCKET}/{S3_PREFIX}/{table_name}/",
                "InputFormat": "org.apache.hadoop.mapred.TextInputFormat",
                "OutputFormat": "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
                "SerdeInfo": {
                    "SerializationLibrary": "org.openx.data.jsonserde.JsonSerDe"
                },
            },
            "PartitionKeys": config.get("partition_keys", []),
            "TableType": "EXTERNAL_TABLE",
        },
    )
    print(f"Created table: {table_name}")


def generate_sample_data():
    """Generate sample MMORPG data."""
    today = datetime.now()
    dt = today.strftime("%Y-%m-%d")
    
    # Sample accounts & characters
    accounts = []
    characters = []
    for i in range(1, 101):
        create_dt = today - timedelta(days=random.randint(1, 30))
        accounts.append({
            "account_uid": 1000000 + i,
            "channel_type": random.choice([1, 2, 3]),
            "channel_id": 2000000 + i,
            "create_date": create_dt.isoformat(),
            "login_date": (today - timedelta(hours=random.randint(0, 48))).isoformat(),
            "logout_date": None if random.random() > 0.3 else today.isoformat(),
        })
        characters.append({
            "char_uid": 3000000 + i,
            "account_uid": 1000000 + i,
            "char_name": f"Player{i:03d}",
            "char_type": random.randint(1, 5),
            "level": random.randint(1, 100),
            "exp": random.randint(0, 1000000),
            "gold": random.randint(0, 100000),
            "login_date": (today - timedelta(hours=random.randint(0, 48))).isoformat(),
            "logout_date": None,
        })
    
    # Sample gacha logs
    gacha_logs = []
    grades = [1, 1, 1, 1, 2, 2, 2, 3, 3, 4]  # 등급 확률
    for i in range(1, 501):
        gacha_logs.append({
            "gacha_id": i,
            "char_uid": 3000000 + random.randint(1, 100),
            "hero_tid": random.randint(1001, 1050),
            "grade": random.choice(grades),
            "gacha_type": random.choice(["single", "ten_pull"]),
            "cost_currency": random.choice(["diamond", "gacha_ticket"]),
            "cost_amount": random.choice([300, 2700]),
            "gacha_time": (today - timedelta(hours=random.randint(0, 168))).isoformat(),
        })
    
    # Sample currency logs
    currency_logs = []
    for i in range(1, 1001):
        before = random.randint(0, 100000)
        delta = random.randint(-5000, 10000)
        currency_logs.append({
            "log_id": i,
            "char_uid": 3000000 + random.randint(1, 100),
            "currency_tid": random.choice([1, 2, 3, 4]),  # gold, diamond, stamina, etc
            "change_type": "earn" if delta > 0 else "spend",
            "change_reason": random.choice(["quest", "gacha", "shop", "battle", "attendance"]),
            "before_value": before,
            "delta_value": delta,
            "after_value": max(0, before + delta),
            "log_time": (today - timedelta(hours=random.randint(0, 168))).isoformat(),
        })
    
    # Sample quest logs
    quest_logs = []
    for i in range(1, 301):
        quest_logs.append({
            "log_id": i,
            "char_uid": 3000000 + random.randint(1, 100),
            "quest_tid": random.randint(1, 100),
            "category1": random.randint(1, 5),
            "category2": random.randint(1, 10),
            "action": random.choice(["start", "progress", "complete"]),
            "log_time": (today - timedelta(hours=random.randint(0, 168))).isoformat(),
        })
    
    # Sample attendance
    attendance_logs = []
    for i in range(1, 101):
        attendance_logs.append({
            "char_uid": 3000000 + i,
            "attend_date": dt,
            "reward_gold": 100,
            "consecutive_days": random.randint(1, 30),
        })
    
    # Upload to S3
    data_map = {
        "accounts": accounts,
        "characters": characters,
        "hero_gacha": gacha_logs,
        "currency_logs": currency_logs,
        "quest_logs": quest_logs,
        "attendance_logs": attendance_logs,
    }
    
    for table_name, data in data_map.items():
        key = f"{S3_PREFIX}/{table_name}/dt={dt}/data.json"
        body = "\n".join(json.dumps(row) for row in data)
        s3.put_object(Bucket=S3_BUCKET, Key=key, Body=body)
        print(f"Uploaded {len(data)} rows to s3://{S3_BUCKET}/{key}")
        
        # Add partition
        try:
            glue.create_partition(
                DatabaseName=DATABASE,
                TableName=table_name,
                PartitionInput={
                    "Values": [dt],
                    "StorageDescriptor": {
                        "Columns": TABLES[table_name]["columns"],
                        "Location": f"s3://{S3_BUCKET}/{S3_PREFIX}/{table_name}/dt={dt}/",
                        "InputFormat": "org.apache.hadoop.mapred.TextInputFormat",
                        "OutputFormat": "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
                        "SerdeInfo": {"SerializationLibrary": "org.openx.data.jsonserde.JsonSerDe"},
                    },
                },
            )
            print(f"Added partition dt={dt} to {table_name}")
        except glue.exceptions.AlreadyExistsException:
            print(f"Partition dt={dt} already exists for {table_name}")


def main():
    print("=== Setting up MMORPG Analytics Tables ===\n")
    
    # Create tables
    for table_name, config in TABLES.items():
        create_table(table_name, config)
    
    print("\n=== Generating Sample Data ===\n")
    generate_sample_data()
    
    print("\n=== Setup Complete ===")
    print(f"Database: {DATABASE}")
    print(f"Tables: {', '.join(TABLES.keys())}")


if __name__ == "__main__":
    main()
