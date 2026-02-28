"""
Dual-mode OBO token validation for Notification Service.

Blog 7 adds TRUST_GATEWAY mode:
  - When TRUST_GATEWAY=true:  Skip JWT validation, extract claims from APIM headers
  - When TRUST_GATEWAY=false: Validate OBO JWT locally (Blog 6 behavior)
"""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
import httpx

from config import AUDIENCE, ALLOWED_TENANT_IDS, ALLOW_ANY_TENANT, TRUST_GATEWAY

security = HTTPBearer(auto_error=not TRUST_GATEWAY)

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
    """Raise 403 if the tenant is not on the allow-list."""
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


def _extract_claims_from_headers(request: Request) -> dict:
    """Extract user claims from APIM-injected headers."""
    oid = request.headers.get("X-User-OID", "")
    name = request.headers.get("X-User-Name", "")
    email = request.headers.get("X-User-Email", "")
    tenant_id = request.headers.get("X-Tenant-ID", "")
    roles_header = request.headers.get("X-User-Roles", "")

    if not oid or not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing required gateway headers (X-User-OID, X-Tenant-ID)",
        )

    roles = [r.strip() for r in roles_header.split(",") if r.strip()]

    return {
        "oid": oid,
        "name": name,
        "preferred_username": email,
        "tid": tenant_id,
        "roles": roles,
        "scp": "Notify.Send",
        "_source": "gateway_headers",
    }


async def _validate_jwt(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Validate OBO Bearer token — expects user context (oid, name, tid)."""
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

    return claims


async def validate_token(request: Request) -> dict:
    """
    Dual-mode validation:
    - TRUST_GATEWAY=true + APIM headers present → extract claims from headers
    - TRUST_GATEWAY=true + no APIM headers       → fall back to JWT (direct S2S call)
    - TRUST_GATEWAY=false                         → validate OBO JWT locally
    """
    if TRUST_GATEWAY:
        # Check if APIM headers are present (request came through gateway)
        oid = request.headers.get("X-User-OID", "")
        tenant_id = request.headers.get("X-Tenant-ID", "")
        if oid and tenant_id:
            return _extract_claims_from_headers(request)
        # No APIM headers → direct S2S call, fall back to JWT validation

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token",
        )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials=auth_header[7:]
    )
    return await _validate_jwt(credentials)
