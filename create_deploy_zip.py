import zipfile
import os

def create_connprehensive_zip(output_filename):
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk('.'):
            # Exclude directories
            dirs[:] = [d for d in dirs if d not in (
                '.git', '.github', '.venv', 'venv', 'node_modules', 
                'logs', 'logs_debug', 'logs_debug_v10', 'logs_debug_v11', 'logs_debug_v12',
                '__pycache__', '.vscode', 'doc_handle', 'mail_agent' 
            )]
            
            for file in files:
                if (file.endswith('.zip') or 
                    file.endswith('.log') or 
                    file.endswith('.pyc') or 
                    file == output_filename or
                    file == 'create_deploy_zip.py' or
                    file == 'read_env.py' or
                    file == 'parse_creds.py'):
                    continue
                
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, ".")
                print(f"Adding {arcname}")
                zipf.write(file_path, arcname=arcname)

create_connprehensive_zip('deploy_fixed.zip')
print("deploy_fixed.zip created successfully.")
