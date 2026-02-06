import json
import codecs

try:
    with codecs.open("env_backup.json", "r", "utf-16") as f:
        content = f.read()

    data = json.loads(content)
    print("Successfully parsed JSON")
    
    config = {}
    for item in data:
        # Also grab Supabase keys just in case
        if any(k in item['name'] for k in ['DB_', 'SUPABASE']):
             config[item['name']] = item['value']
            
    with open("db_test_config.json", "w") as cf:
        json.dump(config, cf)
    print("Written config to db_test_config.json")
    
except Exception as e:
    print(f"Error: {e}")
