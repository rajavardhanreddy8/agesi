import os
output_path = os.path.join(os.path.dirname(__file__), 'test_admin_output.txt')
try:
    with open(output_path, 'r', encoding='utf-16le') as f:
        print(f.read())
except Exception as e:
    with open(output_path, 'r', encoding='utf-8') as f:
        print(f.read())
