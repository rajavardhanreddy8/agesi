import os
import re
import ast

root = r'C:\Users\admin\Documents\outing\agent 4.0'
excludes = ['.git', 'node_modules', '.venv', 'campusouting', '__pycache__']

print('--- DEEP CONTENT ANALYSIS ---')

safe_tests = []
safe_debug = []
safe_utils = []
unsafe_files = []
configs = []
unnecessary = []

def analyze_file(filepath, filename):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        
    # Check for hardcoded local file reads/writes that would break if moved
    # e.g., open('config.json') or open("data.csv")
    has_hardcoded_path = False
    
    # Simple regex for open('something') where something doesn't start with / or C:
    open_matches = re.findall(r'open\s*\(\s*[\'"]([^\'"]+)[\'"]', content)
    for m in open_matches:
        if not m.startswith('/') and not m.startswith('C:\\') and not m.startswith('os.path'):
            has_hardcoded_path = True
            
    if 'os.path.abspath(__file__)' in content or 'os.path.dirname(__file__)' in content:
        # It resolves its own path, so it's generally safe to move
        has_hardcoded_path = False
        
    if has_hardcoded_path:
        return 'UNSAFE'
        
    lower_f = filename.lower()
    
    if filename.endswith('.json') and ('config' in lower_f or 'settings' in lower_f or 'env' in lower_f):
        return 'CONFIG'
        
    if filename.endswith('.py'):
        if lower_f.startswith('test_'):
            return 'TEST'
        if any(lower_f.startswith(p) for p in ['debug_', 'check_', 'inspect_', 'verify_', 'diag_']):
            return 'DEBUG'
        return 'UTILS'
        
    if filename.endswith('.html') and filename != 'index.html':
        return 'UNNECESSARY'
        
    return 'UNKNOWN'

for f in os.listdir(root):
    fp = os.path.join(root, f)
    if not os.path.isfile(fp): continue
    if f in ['app.py', 'scan_files.py', 'analyze_files.py']: continue
    
    ext = os.path.splitext(f)[1]
    if ext in ['.py', '.json', '.html', '.txt', '.md']:
        cat = analyze_file(fp, f)
        if cat == 'UNSAFE': unsafe_files.append(f)
        elif cat == 'TEST': safe_tests.append(f)
        elif cat == 'DEBUG': safe_debug.append(f)
        elif cat == 'UTILS': safe_utils.append(f)
        elif cat == 'CONFIG': configs.append(f)
        elif cat == 'UNNECESSARY': unnecessary.append(f)

print(f'\nCategories based on pure content analysis mapping:')
print(f'Safe to move to scripts/tests/: {len(safe_tests)} files')
print(f'Safe to move to scripts/debug/: {len(safe_debug)} files')
print(f'Safe to move to scripts/utils/: {len(safe_utils)} files')
print(f'Safe to move to config/: {len(configs)} files')
print(f'Safe to delete (temp HTML dumps): {len(unnecessary)} files')

print('\nUNSAFE TO MOVE (Hardcoded relative paths detected):')
for u in unsafe_files:
    print(f'- {u}')
    
# Generate the move plan script
with open('execute_reorg.py', 'w') as out:
    out.write('''import os, shutil
root = r"C:\\Users\\admin\\Documents\\outing\\agent 4.0"
dirs = ["scripts/tests", "scripts/debug", "scripts/utils", "config"]
for d in dirs:
    os.makedirs(os.path.join(root, d), exist_ok=True)
''')
    for f in safe_tests: out.write(f'shutil.move(os.path.join(root, "{f}"), os.path.join(root, "scripts/tests", "{f}"))\n')
    for f in safe_debug: out.write(f'shutil.move(os.path.join(root, "{f}"), os.path.join(root, "scripts/debug", "{f}"))\n')
    for f in safe_utils: out.write(f'shutil.move(os.path.join(root, "{f}"), os.path.join(root, "scripts/utils", "{f}"))\n')
    for f in configs: out.write(f'shutil.move(os.path.join(root, "{f}"), os.path.join(root, "config", "{f}"))\n')
    for f in unnecessary: out.write(f'os.remove(os.path.join(root, "{f}"))\n')
    
print('\nGenerated reorg script: execute_reorg.py. Not executed yet.')
