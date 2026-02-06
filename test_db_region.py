import json
import psycopg2
import sys

# Load config
try:
    with open("db_test_config.json", "r") as f:
        config = json.load(f)
except Exception as e:
    print(f"Failed to load config: {e}")
    sys.exit(1)

project_ref = "uehkqlamchtdzcusqmhi" # Hardcoded from knowledge
db_user = config.get("DB_USER", "postgres")
db_pass = config.get("DB_PASSWORD")
db_name = config.get("DB_NAME", "postgres")

# Construct pooler user: user.project_ref
pooler_user = f"{db_user}.{project_ref}"

regions = {
    "Tokyo": "aws-1-ap-northeast-1.pooler.supabase.com",
}

print(f"Testing connectivity for Project: {project_ref}")
print(f"User: {pooler_user}")

for region, host in regions.items():
    print(f"\nTesting {region} ({host})...")
    try:
        conn = psycopg2.connect(
            host=host,
            user=pooler_user,
            password=db_pass,
            database=db_name,
            port=6543,
            connect_timeout=5,
            sslmode='require'
        )
        print(f"SUCCESS! Connected to {region}")
        with open("found_region.txt", "w") as rf:
            rf.write(region)
            rf.write("\n")
            rf.write(host)
        conn.close()
        break
    except psycopg2.OperationalError as e:
        msg = str(e)
        if "password authentication failed" in msg:
             print(f"FOUND REGION via Auth Error: {region}")
             with open("found_region.txt", "w") as rf:
                rf.write(region)
                rf.write("\n")
                rf.write(host)
             break
        print(f"Failed ({region}): {e}")
    except Exception as e:
        print(f"Error ({region}): {e}")
