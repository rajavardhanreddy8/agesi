
import sys
import os

try:
    import gotrue
    print(f"gotrue file: {gotrue.__file__}")
    site_packages = os.path.dirname(os.path.dirname(gotrue.__file__))
    print(f"Site-packages: {site_packages}")
    print(f"Contents of site-packages: {os.listdir(site_packages)}")
except Exception as e:
    print(f"FAIL: gotrue import: {e}")

try:
    import supabase
    print(f"supabase file: {supabase.__file__}")
except Exception as e:
    print(f"FAIL: supabase import: {e}")
