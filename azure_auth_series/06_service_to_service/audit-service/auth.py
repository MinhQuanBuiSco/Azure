"""
App-only token validation for Audit Service.

Validates client credential tokens — these have NO user context.
Instead they have a `roles` claim with application permissions
(e.g., AuditLog.Write) granted via admin consent.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
import httpx

from config import AUDIENCE, ALLOWED_TENANT_IDS, ALLOW_ANY_TENANT

security = HTTPBearer()

# Per-tenant JWKS cache
_jwks_cache: dict[str, dict] = {}


async def _get_jwks(tenant_id: str) -> dict:
    """Fetch (and cache) the JWKS for a specific tenant."""
    if tenant_id not in _jwks_cache:
        url = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            resp.raise_for_status()
            _jwks_cache[tenant_id] = resp.json()
    return _jwks_cache[tenant_id]


def _check_tenant_allowed(tenant_id: str) -> None:
    if ALLOW_ANY_TENANT:
        return
    if tenant_id not in ALLOWED_TENANT_IDS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tenant {tenant_id} is not allowed",
        )


def _find_rsa_key(jwks: dict, kid: str) -> dict | None:
    for key in jwks.get("keys", []):
        if key["kid"] == kid:
            return {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"],
            }
    return None


async def validate_app_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Validate app-only Bearer token (client credentials flow).
    Expects `roles` claim (application permissions), NOT `scp` (delegated).
    """
    token = credentials.credentials

    try:
        unverified_header = jwt.get_unverified_header(token)
        unverified_claims = jwt.get_unverified_claims(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    tenant_id = unverified_claims.get("tid", "")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing tenant ID (tid) claim",
        )

    _check_tenant_allowed(tenant_id)

    jwks = await _get_jwks(tenant_id)
    rsa_key = _find_rsa_key(jwks, unverified_header.get("kid", ""))

    if rsa_key is None:
        _jwks_cache.pop(tenant_id, None)
        jwks = await _get_jwks(tenant_id)
        rsa_key = _find_rsa_key(jwks, unverified_header.get("kid", ""))

    if rsa_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to find signing key",
        )

    expected_issuer = f"https://sts.windows.net/{tenant_id}/"

    try:
        claims = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=AUDIENCE,
            issuer=expected_issuer,
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}",
        )

    # Verify this is an app-only token with the required role
    roles = claims.get("roles", [])
    if "AuditLog.Write" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing required application role: AuditLog.Write. Token roles: {roles}",
        )

    return claims
