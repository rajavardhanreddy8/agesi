import subprocess
import json
import sys

# Command to update the linux-fx-version
cmd = [
    "az.cmd", "webapp", "config", "set",
    "--name", "outing-backend-api",
    "--resource-group", "rg-outing-agent",
    "--linux-fx-version", "DOCKER|acroutingagent.azurecr.io/agesi:latest"
]

print(f"Executing command: {' '.join(cmd)}")

try:
    # On Windows, we need to use az.cmd and shell=False (default) generally works for list args
    # But for 'az' specifically, since it's a batch file, we might need shell=True BUT with proper quoting if using shell.
    # However, subprocess.run with list args on Windows DOES quoting automatically for arguments.
    # But 'az' is a .cmd file, so we must run it via cmd /c or call az.cmd directly.
    # If we use shell=True, we are back to square one.
    # If we use shell=False, we must execute the actual executable/script.
    
    # Trying with shell=True but let's trust Python's argument quoting or just use the list.
    # Actually, if we use list args with shell=True, it uses /c "..." and quotes might get messy.
    # If we use shell=False, we need full path to az.cmd or rely on PATH finding az.cmd.
    
    # Let's try finding az first.
    # Assuming 'az' is in path.
    
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True) 
    # With shell=True, the list is converted to string. 
    # Python escapes args? No, on Windows with shell=True, it uses subprocess.list2cmdline
    
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    
    if result.returncode != 0:
        sys.exit(result.returncode)
        
except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)
