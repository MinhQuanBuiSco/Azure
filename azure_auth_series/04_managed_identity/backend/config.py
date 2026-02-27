import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Key Vault via Managed Identity (deployed) with .env fallback (local) ──

KEY_VAULT_URL = os.getenv("AZURE_KEY_VAULT_URL", "")

if KEY_VAULT_URL:
    from azure.identity import DefaultAzureCredential
    from azure.keyvault.secrets import SecretClient

    logger.info("AZURE_KEY_VAULT_URL detected — loading config from Key Vault")
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=KEY_VAULT_URL, credential=credential)

    TENANT_ID = client.get_secret("azure-tenant-id").value
    API_CLIENT_ID = client.get_secret("azure-api-client-id").value
    logger.info("Loaded TENANT_ID and API_CLIENT_ID from Key Vault")
else:
    logger.info("No AZURE_KEY_VAULT_URL — loading config from .env / environment")
    TENANT_ID = os.getenv("AZURE_TENANT_ID", "")
    API_CLIENT_ID = os.getenv("AZURE_API_CLIENT_ID", "")

# ── Derived values (same as Blog 3) ──

AUDIENCE = f"api://{API_CLIENT_ID}"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
JWKS_URI = f"{AUTHORITY}/discovery/v2.0/keys"
ISSUER = f"https://sts.windows.net/{TENANT_ID}/"

# ── CORS ──

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
