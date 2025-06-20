import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI: str = os.getenv("MONGO_URI")
MONGO_DB: str = os.getenv("MONGO_DB")
SECRET_KEY: str = os.getenv("SECRET_KEY")
ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
PORT: int = int(os.getenv("PORT", 8000))
RELOAD: bool = bool(os.getenv("RELOAD", True))
EMAIL_ID: str = str(os.getenv("EMAIL_ID"))
EMAIL_PASSWORD: str = str(os.getenv("EMAIL_PASSWORD"))