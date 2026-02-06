import codecs
import re

try:
    with codecs.open("profiles.xml", "r", "utf-16") as f:
        content = f.read()
    
    user_match = re.search(r'userName="([^"]+)"', content)
    pwd_match = re.search(r'userPWD="([^"]+)"', content)
    
    if user_match and pwd_match:
        user = user_match.group(1)
        # Escape $ in username if needed, though python subprocess handles args better. 
        # But for the URL string, we just format it.
        # Actually userPWD usually doesn't have special URL chars needing encoding, but purely in case...
        # Let's hope urllib isn't needed or import it.
        import urllib.parse
        pwd = urllib.parse.quote(pwd_match.group(1))
        
        # Username often starts with $. $ needs to be encoded? No, in URL it's fine usually, but let's safe quote.
        user_encoded = urllib.parse.quote(user)

        url = f"https://{user_encoded}:{pwd}@outing-backend-api.scm.azurewebsites.net/outing-backend-api.git"
        
        print("Credentials found. Configuring git remote...")
        import subprocess
        
        # Remove existing
        subprocess.run(["git", "remote", "remove", "azure"], capture_output=True)
        
        # Add new
        print("Adding remote 'azure'...")
        subprocess.run(["git", "remote", "add", "azure", url], check=True)
        
        # Push
        print("Pushing to azure (this may take a minute)...")
        try:
            # Capture output to print it on error
            result = subprocess.run(["git", "push", "azure", "main:master"], check=True, capture_output=True, text=True)
            print("Push Successful!")
            print(result.stdout)
            print(result.stderr)
        except subprocess.CalledProcessError as e:
            print(f"Git Push Failed!")
            print(f"STDOUT: {e.stdout}")
            print(f"STDERR: {e.stderr}")
        
    else:
        print("Error: Credentials not found in match")
except Exception as e:
    print(f"Error: {e}")
