import subprocess, json
result = subprocess.run(
    'az staticwebapp secrets list --name AOP-frontend -o json',
    capture_output=True, text=True, shell=True
)
data = json.loads(result.stdout)
token = data['properties']['apiKey']
# Write token to file so we can use it without truncation
with open('deploy_token.txt', 'w') as f:
    f.write(token)
print(f"Token saved to deploy_token.txt (length: {len(token)})")
