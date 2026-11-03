from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from shared.jwt_utils import ALGORITHM, SECRET_KEY


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    # Token expires in 60 minutes
    expire = datetime.now(timezone.utc) + timedelta(minutes=60)
    to_encode.update({"exp": expire})

    # Sign the token
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
