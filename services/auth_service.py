from datetime import datetime, timedelta
from typing import Optional, Tuple
from cachetools import TTLCache
from jose import JWTError

from config import SECRET_KEY, ALGORITHM
from schemas.user_schema import UserInDB
from utils.jwt_utils import create_access_token
from utils.email_utils import EmailSender
from utils.common_utils import generate_otp
from utils.logger import logger
import jwt
from fastapi import status, HTTPException

# Configure caches
otp_cache = TTLCache(maxsize=1000, ttl=600)  # 10 minutes for OTP
resend_cache = TTLCache(maxsize=1000, ttl=30)  # 30 sec cooldown


class AuthService:
    def __init__(self, mongo):
        self.users_collection = mongo["users"]
        self.email_sender = EmailSender()

    async def can_resend_otp(self, email: str) -> Tuple[bool, int]:
        """Check if OTP can be resent and return remaining cooldown seconds"""
        if email not in resend_cache:
            return True, 0

        remaining = (resend_cache[email] - datetime.utcnow()).total_seconds()
        return False, max(0, int(remaining))

    async def send_login_otp(self, email: str) -> bool:
        """Send OTP to user's email for authentication"""
        try:
            # Check resend cooldown
            can_resend, _ = await self.can_resend_otp(email)
            if not can_resend:
                logger.warning(f"Resend attempt too soon for {email}")
                return False

            otp = generate_otp()
            expires_at = datetime.utcnow() + timedelta(minutes=5)

            otp_cache[email] = {
                "otp": otp,
                "expires_at": expires_at,
                "attempts": 0
            }

            # Set resend cooldown
            resend_cache[email] = datetime.utcnow() + timedelta(minutes=3)

            subject = "Your Login Verification Code"
            body = f"Your OTP is: {otp}. Valid for 5 minutes."

            await self.email_sender.send_mail(email, subject, body)
            logger.info(f"OTP sent to {email} - {otp}")
            return True

        except Exception as e:
            logger.error(f"Failed to send OTP to {email}: {str(e)}")
            return False

    async def verify_otp(
            self,
            email: str,
            otp: str
    ) -> Tuple[bool, Optional[UserInDB]]:
        """Verify OTP and return (success, user) tuple"""
        try:
            stored = otp_cache.get(email)

            if not stored:
                logger.warning(f"No OTP found for {email}")
                return False, None

            if datetime.utcnow() > stored["expires_at"]:
                logger.warning(f"Expired OTP attempt for {email}")
                return False, None

            if stored["otp"] != otp:
                stored["attempts"] += 1
                logger.warning(f"Invalid OTP attempt for {email}")
                return False, None

            # OTP verified, check if user exists
            user = await self.users_collection.find_one({"email": email})

            if user:
                user["_id"] = str(user["_id"])
                return True, UserInDB(**user)

            return True, None

        except Exception as e:
            logger.error(f"OTP verification failed for {email}: {str(e)}")
            return False, None

    async def create_new_user(
            self,
            email: str,
            full_name: str
    ) -> UserInDB:
        """Create new user with verified email"""
        try:
            if await self.users_collection.find_one({"email": email}):
                raise ValueError("Email already registered")

            user_data = {
                "email": email,
                "full_name": full_name,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            result = await self.users_collection.insert_one(user_data)
            created_user = await self.users_collection.find_one(
                {"_id": result.inserted_id}
            )

            created_user["_id"] = str(created_user["_id"])
            logger.info(f"New user created: {email}")
            return UserInDB(**created_user)

        except Exception as e:
            logger.error(f"Failed to create user {email}: {str(e)}")
            raise

    async def generate_auth_token(self, email: str) -> str:
        """Generate JWT token for authenticated user"""
        try:
            token = create_access_token({"sub": email})
            logger.info(f"Token generated for {email}")
            return token
        except Exception as e:
            logger.error(f"Token generation failed for {email}: {str(e)}")
            raise

    def verify_token(self, token: str) -> dict:
        """
        Verify JWT token and return payload if valid

        Args:
            token: JWT token to verify

        Returns:
            dict: Decoded token payload

        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            # Decode the token using your secret key and algorithm
            payload = jwt.decode(
                token,
                SECRET_KEY,  # Your secret key from settings
                algorithms=[ALGORITHM]  # Typically "HS256"
            )

            # Check if token is expired
            expire = payload.get("exp")
            if expire is None or datetime.utcnow() > datetime.fromtimestamp(expire):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired"
                )

            return payload

        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )