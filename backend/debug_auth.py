import sys, os, traceback
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Simulate exactly what the FastAPI auth system does
from app.db import get_db
from app.config import JWT_SECRET_KEY, JWT_ALGORITHM
from jose import jwt

print("=== Testing JWT decode ===")
db = get_db()
user = db["users"].find_one({"email": "manager@apex.com"})
print("User found:", user["email"] if user else "None")
print("User organizationId:", user.get("organizationId"))

# Generate a token
from datetime import datetime, timedelta
expire = datetime.utcnow() + timedelta(minutes=60)
data = {"sub": user["email"], "role": user["role"], "name": user["name"], "exp": expire}
token = jwt.encode(data, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
print("Token generated:", token[:40] + "...")

# Decode it back
payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
print("Decoded payload:", payload)

# Check if UserSession works
from app.auth import UserSession
session = UserSession(
    userId=user.get("userId", ""),
    email=payload["sub"],
    role=payload["role"],
    name=payload.get("name", ""),
    organizationId=user.get("organizationId", "")
)
print("UserSession:", session)
print("\nAll auth checks PASSED!")
