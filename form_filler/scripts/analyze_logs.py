
import os
import glob

log_dir = 'extracted_logs_v5/LogFiles'
files = glob.glob(os.path.join(log_dir, '*docker*.log'))
files.sort(key=os.path.getmtime, reverse=True)

print(f"Found {len(files)} docker logs.")


with open('analysis_report.txt', 'w', encoding='utf-8') as report:
    for f in files[:5]:
        report.write(f"\n--- FILE: {f} ({os.path.getsize(f)} bytes) ---\n")
        try:
            with open(f, 'r', encoding='utf-8', errors='ignore') as log:
                content = log.read()
                lines = content.splitlines()
                report.write("START:\n")
                for l in lines[:5]: report.write(l + '\n')
                report.write("...\n")
                report.write("END:\n")
                for l in lines[-5:]: report.write(l + '\n')
                
                report.write("ERRORS:\n")
                for l in lines:
                    if 'error' in l.lower() or 'fail' in l.lower() or 'exception' in l.lower():
                        report.write(l[:200] + '\n')
        except Exception as e:
            report.write(f"Error reading file: {e}\n")    
print("Analysis complete. Check analysis_report.txt")
