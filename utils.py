# Token generation utilities
from itsdangerous import URLSafeTimedSerializer
from flask import current_app

def generate_token(email: str) -> str:
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY']).dumps(email, salt='email-confirm')

def confirm_token(token: str, expiration: int = 3600) -> str | bool:
    try:
        return URLSafeTimedSerializer(current_app.config['SECRET_KEY']).loads(token, salt='email-confirm', max_age=expiration)
    except:
        return False
