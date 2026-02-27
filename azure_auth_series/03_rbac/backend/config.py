import os
from dotenv import load_dotenv

load_dotenv()

TENANT_ID = os.getenv("AZURE_TENANT_ID", "")
API_CLIENT_ID = os.getenv("AZURE_API_CLIENT_ID", "")

AUDIENCE = f"api://{API_CLIENT_ID}"

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
JWKS_URI = f"{AUTHORITY}/discovery/v2.0/keys"
ISSUER = f"https://sts.windows.net/{TENANT_ID}/"
