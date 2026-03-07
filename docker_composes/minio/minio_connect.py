import boto3
from botocore.client import Config
import io
import pandas as pd

s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:9000",
    aws_access_key_id="admin",
    aws_secret_access_key="password123",
    config=Config(signature_version="s3v4"),
    region_name="us-east-1",
)

bucket = "busket1"

resp = s3.list_objects_v2(Bucket=bucket)
for obj in resp.get("Contents", []):
    print(repr(obj["Key"]))
    if "invite rounds.xlsx" in obj["Key"]:
        key = obj["Key"]          # no quotes here
        break

# 2) Read the object into pandas
obj = s3.get_object(Bucket=bucket, Key=key)
data = obj["Body"].read()

df = pd.read_excel(io.BytesIO(data))
print(df)
