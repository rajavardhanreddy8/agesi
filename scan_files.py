import os
from pathlib import Path

root = r'C:\Users\admin\Documents\outing\agent 4.0'
excludes = ['.git', '__pycache__', '.pytest_cache', 'build', 'dist']

categories = {
    'Essential Code (JS/PY/HTML/CSS)': {'size': 0, 'count': 0, 'files': []},
    'Dependencies (node_modules/.venv)': {'size': 0, 'count': 0, 'files': []},
    'Databases (.db/.sqlite3)': {'size': 0, 'count': 0, 'files': []},
    'Logs & Archives (.log/.zip/.json logs)': {'size': 0, 'count': 0, 'files': []},
    'Images & Media (.png/.jpg/.jpeg/.svg)': {'size': 0, 'count': 0, 'files': []},
    'Documents & Outputs (.pdf/.csv)': {'size': 0, 'count': 0, 'files': []},
    'Temp & System Folders (.claude/temp_uploads/signatures)': {'size': 0, 'count': 0, 'files': []},
    'Other': {'size': 0, 'count': 0, 'files': []}
}

def is_excluded(path):
    parts = Path(path).parts
    return any(exc in parts for exc in excludes)

for dirpath, dirnames, filenames in os.walk(root):
    if is_excluded(dirpath): continue
    
    parts = Path(dirpath).parts
    str_parts = '/'.join(parts).lower()
    
    for f in filenames:
        fp = os.path.join(dirpath, f)
        if is_excluded(fp): continue
        if os.path.islink(fp): continue
        
        try:
            size = os.path.getsize(fp)
        except: continue
        
        ext = os.path.splitext(f)[1].lower()
        f_lower = f.lower()
        
        cat = 'Other'
        
        if any(p in parts for p in ['.venv', 'node_modules']):
            cat = 'Dependencies (node_modules/.venv)'
        elif any(p in parts for p in ['.claude', 'temp_uploads', 'signatures', 'images']):
            cat = 'Temp & System Folders (.claude/temp_uploads/signatures)'
        elif ext in ['.db', '.sqlite3']:
            cat = 'Databases (.db/.sqlite3)'
        elif ext in ['.log', '.zip', '.txt'] or 'log' in f_lower or 'debug' in f_lower or ('log' in str_parts and ext == '.xml'):
            cat = 'Logs & Archives (.log/.zip/.json logs)'
        elif ext in ['.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.json'] and not f_lower.endswith('_log.json') and not f_lower.endswith('log.json'):
            cat = 'Essential Code (JS/PY/HTML/CSS)'
        elif ext in ['.png', '.jpg', '.jpeg', '.svg', '.gif', '.ico', '.webp']:
            cat = 'Images & Media (.png/.jpg/.jpeg/.svg)'
        elif ext in ['.pdf', '.csv', '.xlsx', '.doc', '.docx']:
            cat = 'Documents & Outputs (.pdf/.csv)'
            
        categories[cat]['size'] += size
        categories[cat]['count'] += 1
        if size > 1024 * 512: # track files > 500 KB to list them
            categories[cat]['files'].append((size, fp))

with open('deep_analysis.md', 'w') as f:
    f.write('## Summary of Internal Files\n')
    
    sorted_cats = sorted(categories.items(), key=lambda x: x[1]['size'], reverse=True)
    
    for name, data in sorted_cats:
        f.write(f'- **{name}**: {data["size"] / (1024*1024):.2f} MB ({data["count"]} files)\n')
    
    f.write('\n## Detail: Disposable Assets (Can be safely deleted)\n')
    f.write('These categories contain files not required to run the code:\n\n')
    
    for name in ['Logs & Archives (.log/.zip/.json logs)', 'Images & Media (.png/.jpg/.jpeg/.svg)', 'Documents & Outputs (.pdf/.csv)', 'Temp & System Folders (.claude/temp_uploads/signatures)']:
        data = categories[name]
        f.write(f'### {name} - Total: {data["size"] / (1024*1024):.2f} MB ({data["count"]} files)\n')
        if data['files']:
            f.write('Largest files in this category:\n')
            sorted_files = sorted(data['files'], reverse=True)[:10]
            for s, path in sorted_files:
                f.write(f'- `{os.path.relpath(path, root)}` ({s/1024/1024:.2f} MB)\n')
        f.write('\n')

print('Done')
