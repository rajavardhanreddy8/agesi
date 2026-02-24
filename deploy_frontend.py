import subprocess, os

# Read the token
with open('deploy_token.txt', 'r') as f:
    token = f.read().strip()

print(f"Token length: {len(token)}")
print("Deploying frontend...")

result = subprocess.run(
    f'npx @azure/static-web-apps-cli deploy ./dist --deployment-token {token}',
    capture_output=True, text=True, shell=True, cwd='campusouting'
)
print("STDOUT:", result.stdout[-1000:] if result.stdout else "none")
print("STDERR:", result.stderr[-1000:] if result.stderr else "none")
print("Return code:", result.returncode)
