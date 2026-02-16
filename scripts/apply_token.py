import os

def apply():
    token_file = 'token.txt'
    if not os.path.exists(token_file):
        print(f"Error: {token_file} not found.")
        return

    # Handle potential UTF-16LE from PowerShell redirection
    try:
        with open(token_file, 'rb') as f:
            raw = f.read()
            if raw.startswith(b'\xff\xfe'): # UTF-16 LE BOM
                token_data = raw.decode('utf-16')
            else:
                token_data = raw.decode('utf-8')
    except Exception as e:
        print(f"Error reading token: {e}")
        return

    tokens = [l.strip() for l in token_data.splitlines() if l.strip().startswith('eyJ')]
    if not tokens:
        print("Error: No JWT found in token.txt")
        return
    token = tokens[0]

    sf = 'scripts/trigger_real_task.py'
    with open(sf, 'r') as f:
        content = f.read()

    new_headers = f"headers = {{'Content-Type': 'application/json', 'Authorization': 'Bearer {token}'}}"
    old_target = "headers = {'Content-Type': 'application/json'}"
    
    if old_target in content:
        new_content = content.replace(old_target, new_headers)
        with open(sf, 'w') as f:
            f.write(new_content)
        print(f"Successfully applied token to {sf}")
    else:
        print(f"Warning: Could not find target header line in {sf}")

if __name__ == "__main__":
    apply()
