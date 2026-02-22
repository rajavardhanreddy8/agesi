
import subprocess
import json

def fix_config():
    print("Fetching connection string...")
    res = subprocess.run(
        ["az", "storage account show-connection-string", "--name", "agesi", "--resource-group", "rg-outing-agent", "--query", "connectionString", "--output", "tsv"],
        capture_output=True, text=True, shell=True
    )
    conn_str = res.stdout.strip()
    
    if not conn_str:
        print("Error: Could not fetch connection string")
        return

    print(f"Found connection string (length: {len(conn_str)})")
    
    print("Setting Azure App Setting...")
    # Passing the value directly in the command list to avoid shell parsing issues
    subprocess.run(
        ["az", "webapp", "config", "appsettings", "set", "--name", "outing-backend-api", "--resource-group", "rg-outing-agent", "--settings", f"AZURE_STORAGE_CONNECTION_STRING={conn_str}"],
        shell=True
    )
    print("✅ Configuration updated!")

if __name__ == "__main__":
    fix_config()
