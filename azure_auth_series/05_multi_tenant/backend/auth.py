"""
Multi-tenant token validation.

Key differences from single-tenant (Blog 3-4):
  - JWKS endpoint is dynamic: each tenant has its own signing keys.
  - Issuer is dynamic: https://sts.windows.net/{tid}/
  - A tenant allow-list gates access before we even fetch keys.
"""

from typing import Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
import httpx

from config import AUDIENCE, ALLOWED_TENANT_IDS, ALLOW_ANY_TENANT

security = HTTPBearer()

# ── Per-tenant JWKS cache ────────────────────────────
# In single-tenant we cached one JWKS. Now we cache per tenant ID.

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
    """Raise 403 if the tenant is not on the allow-list."""
    if ALLOW_ANY_TENANT:
        return
    if tenant_id not in ALLOWED_TENANT_IDS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tenant {tenant_id} is not allowed to access this application",
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


async def validate_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Validate the Bearer token and return the decoded claims."""
    token = credentials.credentials

    # 1. Peek at the header (for kid) and claims (for tid) — unverified
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

    # 2. Gate: is this tenant allowed?
    _check_tenant_allowed(tenant_id)

    # 3. Fetch JWKS for this tenant and find the signing key
    jwks = await _get_jwks(tenant_id)
    rsa_key = _find_rsa_key(jwks, unverified_header.get("kid", ""))

    if rsa_key is None:
        # Key might have rotated — clear cache and retry once
        _jwks_cache.pop(tenant_id, None)
        jwks = await _get_jwks(tenant_id)
        rsa_key = _find_rsa_key(jwks, unverified_header.get("kid", ""))

    if rsa_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to find signing key",
        )

    # 4. Verify — dynamic issuer per tenant
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

    return claims


def get_user_roles(claims: dict) -> list[str]:
    """Extract roles from the token claims."""
    return claims.get("roles", [])


def require_role(*allowed_roles: str) -> Callable:
    """Dependency that checks if the user has one of the allowed roles."""

    async def check_role(claims: dict = Depends(validate_token)) -> dict:
        user_roles = get_user_roles(claims)
        if not any(role in user_roles for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {', '.join(allowed_roles)}. Your roles: {', '.join(user_roles) or 'none'}",
            )
        return claims

    return check_role
