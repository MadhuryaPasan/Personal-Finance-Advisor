from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError


SECRET_KEY = "your-secret-key"   # must match FastAPI
ALGORITHM = "HS256"

def generate_email_jwt(email: str) -> str:
    token = jwt.encode(
        {
            "username": email,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    return token

