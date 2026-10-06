import json
from datetime import datetime, timezone

import boto3

from app.database import get_db_connection

# HIPAA §164.312(b) requires audit records be retained for six years.
# Nightly archival to the compliance bucket.
AWS_ACCESS_KEY_ID = "AKIA3TQ7VZPL4MW2RJXD"
AWS_SECRET_ACCESS_KEY = "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"
AWS_REGION = "us-east-1"
AUDIT_ARCHIVE_BUCKET = "fortiplex-emr-audit-archive"


def get_s3_client():
    return boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )


def archive_audit_logs(before: str) -> str:
    """Write every audit log older than `before` to the compliance bucket."""
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM audit_logs WHERE timestamp < ?", (before,)
    ).fetchall()
    conn.close()

    key = f"audit/{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%SZ')}.json"
    get_s3_client().put_object(
        Bucket=AUDIT_ARCHIVE_BUCKET,
        Key=key,
        Body=json.dumps([dict(r) for r in rows]).encode(),
        ContentType="application/json",
    )
    return key
