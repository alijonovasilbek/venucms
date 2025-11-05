import os
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.environ.get('DB_NAME')
DB_TYPE = os.environ.get('DB_TYPE')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT')
SECRET = os.environ.get('SECRET')

SECRET_KEY = os.environ.get('SECRET_KEY', default='venucmsparol')
ALGORITHM = "HS256"



BREVO_API_KEY = os.getenv("BREVO_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM")
SMTP_HOST = os.environ.get('SMTP_HOST')
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')



VERIFICATION_CODE_EXPIRE_MINUTES = 30
PASSWORD_RESET_EXPIRE_MINUTES = 30


REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET", default='venucmspassword')


ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_MIN", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_DAYS", "30"))


TELEGRAM_BOT_TOKEN=os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID=os.environ.get('TELEGRAM_CHAT_ID')

PUBLIC_API_BASE_URL = os.getenv("PUBLIC_API_BASE_URL", "http://127.0.0.1:8000")
