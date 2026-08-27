"""
Authentication
================
Thin wrapper around Supabase Auth. Passwords are never touched or
stored by our own code -- Supabase handles hashing, verification,
and session tokens entirely. We only ever pass email/password
straight through to Supabase and hand back whatever it returns.
"""

from supabase_client import supabase_anon, supabase_admin


def sign_up(email: str, password: str):
    result = supabase_anon.auth.sign_up({"email": email, "password": password})
    return result


def sign_in(email: str, password: str):
    result = supabase_anon.auth.sign_in_with_password({"email": email, "password": password})
    return result


def get_user_from_token(access_token: str):
    """
    Verifies a token and returns the associated user, or None if the
    token is invalid/expired. This is what proves a request actually
    belongs to a logged-in user, rather than trusting a client-supplied
    user_id (which anyone could fake).
    """
    try:
        result = supabase_admin.auth.get_user(access_token)
        return result.user
    except Exception:
        return None