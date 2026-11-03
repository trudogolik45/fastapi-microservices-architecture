import os

import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Shared secret: every service must use the same value
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "my_super_secret_jwt_key_for_microservices")
ALGORITHM = "HS256"

security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Validates the JWT and returns the payload (user info)."""
    try:
        # Decode the token using our shared secret
        return jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
