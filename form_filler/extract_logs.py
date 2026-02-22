import json
import io

try:
    with io.open('v6_diag_log.json', 'r', encoding='utf-16le') as f:
        data = f.read()
except:
    with io.open('v6_diag_log.json', 'r', encoding='utf-8') as f:
        data = f.read()
        
data = data.lstrip('\ufeff')
j = json.loads(data)
logs = j.get('debug', {}).get('logs', [])
with open('extracted_logs.txt', 'w', encoding='utf-8') as f:
    f.write('\\n'.join(logs))
print("Extracted to extracted_logs.txt")
