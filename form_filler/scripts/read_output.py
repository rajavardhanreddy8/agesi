
import sys

def search_in_file(filename, term):
    encodings = ['utf-16le', 'utf-8', 'cp1252', 'utf-16']
    content = ""
    success = False
    
    for enc in encodings:
        try:
            with open(filename, 'r', encoding=enc) as f:
                content = f.read()
                success = True
                print(f"Successfully read with {enc}")
                break
        except Exception:
            continue
            
    if not success:
        print("Failed to read file with common encodings")
        return

    found = False
    for line in content.splitlines():
        if term in line:
            print(f"FOUND: {line.strip()}")
            found = True
            
    if not found:
        print(f"NOT FOUND: '{term}'")

if __name__ == "__main__":
    search_in_file("test_output.txt", "School Name")
