from datetime import datetime, timedelta
from flask import  request
import jwt
import pytz
import config

def jwt_get_principal():
    """
    Get the principal from the JWT token.

    Returns:
        dict: The principal of the user.
    """
    token = jwt_get()
    return jwt_decode(token)["profile"]

def jwt_decode(token):
    return jwt.decode(token, config.JWT_SECRET_KEY, algorithms=['HS256'], audience=config.JWT_AUD)

def jwt_create_access_token(sub, profile=None, authorities=None):
    timezone = pytz.timezone("UTC")
    now = datetime.now(timezone)
    payload = {
        'exp': int((now + timedelta(seconds=config.JWT_EXPIRE)).timestamp()),
        'iat': int(now.timestamp()),
        'sub': sub,
        'profile':profile,
        'authorities':authorities,
        "aud": config.JWT_AUD
    }
    return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm='HS256')

def jwt_create_refresh_token(sub):
    timezone = pytz.timezone("UTC")
    now = (datetime.now(timezone) + timedelta(hours=24))

    payload={'exp': int(now.timestamp()), 'sub': sub,"aud": config.JWT_AUD}
    return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm='HS256')


def jwt_get():
    token = request.headers.get("Authorization",None)
    if token:
        ts=token.split(" ")
        return ts[1] if len(ts)>1 else token
    return None

def jwt_get_refresh():
    return request.headers.get("Refresh-Token")


def jwt_decode(token):
    return jwt.decode(token, config.JWT_SECRET_KEY, algorithms=["HS256"], audience=config.JWT_AUD)


def jwt_create_access_token(sub, profile=None, authorities=None):
    now = datetime.now(config.TZ)
    if profile:
        profile.pop("created_at", None)
        profile.pop("updated_at", None)
        profile.pop("password", None)
    payload = {
        "exp": int((now + timedelta(seconds=config.JWT_EXPIRE)).timestamp()),
        "iat": int(now.timestamp()),
        "sub": sub,
        "profile": profile,
        "authorities": authorities,
        "aud": config.JWT_AUD,
    }
    return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm="HS256")


def jwt_create_refresh_token(sub):
    now = datetime.now(config.TZ) + timedelta(hours=24)
    payload = {"exp": int(now.timestamp()), "sub": sub, "aud": config.JWT_AUD}
    return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm="HS256")