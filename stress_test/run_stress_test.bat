@echo off
setlocal
cd /d "%~dp0\.."

echo Checking dependencies...
pip install -r requirements.txt -q

cd stress_test
echo ==============================================
echo Running MS Forms Stress Test with %1 Workers
echo ==============================================
python stress_test.py --workers %1 --data test_users.json

if %ERRORLEVEL% NEQ 0 (
    echo [!] Stress test failed. Check stress_test_results.csv!
    exit /b %ERRORLEVEL%
) else (
    echo [OK] All form submissions succeeded under run!
)
