from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
import httpx

from config import AUDIENCE, JWKS_URI, ISSUER

security = HTTPBearer()

# Cache JWKS keys in memory
_jwks_cache: dict | None = None


async def _get_jwks() -> dict:
    """Fetch and cache the JSON Web Key Set from Microsoft."""
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(JWKS_URI)
            resp.raise_for_status()
            _jwks_cache = resp.json()
    return _jwks_cache


def _find_rsa_key(jwks: dict, kid: str) -> dict | None:
    """Find the signing key matching the token's kid header."""
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

    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token header",
        )

    jwks = await _get_jwks()
    rsa_key = _find_rsa_key(jwks, unverified_header.get("kid", ""))

    if rsa_key is None:
        # Key not found — clear cache and retry once (key rotation)
        global _jwks_cache
        _jwks_cache = None
        jwks = await _get_jwks()
        rsa_key = _find_rsa_key(jwks, unverified_header.get("kid", ""))

    if rsa_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to find signing key",
        )

    # Debug: decode without verification to see actual claims
    unverified = jwt.get_unverified_claims(token)
    print(f"[DEBUG] Token aud: {unverified.get('aud')}")
    print(f"[DEBUG] Token iss: {unverified.get('iss')}")
    print(f"[DEBUG] Expected aud: {AUDIENCE}")
    print(f"[DEBUG] Expected iss: {ISSUER}")

    try:
        claims = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=AUDIENCE,
            issuer=ISSUER,
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
