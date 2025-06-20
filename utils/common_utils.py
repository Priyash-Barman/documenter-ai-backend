# utils/common_utils.py
import random
from datetime import datetime, timedelta

def generate_otp(length: int = 6) -> str:
    """Generate a random numeric OTP of specified length"""
    return str(random.randint(10**(length-1), (10**length)-1))

def get_otp_expiry_time(expiry_minutes: int = 5) -> datetime:
    """Get the expiry time for OTP"""
    return datetime.now() + timedelta(minutes=expiry_minutes)