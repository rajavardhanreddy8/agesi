import os
from cryptography.fernet import Fernet

# Generate a new stable key
new_key = Fernet.generate_key().decode()

print(f"Generated new stable ENCRYPTION_KEY:")
print(f"{new_key}")
print(f"\nAdd this to your .env file:")
print(f"ENCRYPTION_KEY={new_key}")
print(f"\nAnd set it in Azure App Service:")
print(f"az webapp config appsettings set --name outing-backend-api --resource-group rg-outing-agent --settings ENCRYPTION_KEY={new_key}")
