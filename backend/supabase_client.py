"""
Supabase Client Setup
=======================
Two separate clients, deliberately:
- supabase_anon: used for user-facing auth actions (signup/login). Has
  the same limited privileges a browser would have.
- supabase_admin: used for backend-trusted operations (reading/writing
  scores, verifying tokens). Bypasses Row Level Security -- this is
  safe ONLY because every use of it is scoped to a user_id we've
  already verified via a real access token, never trusted from the
  client directly.
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_PUBLISHABLE_KEY = os.environ.get("SUPABASE_PUBLISHABLE_KEY")
SUPABASE_SECRET_KEY = os.environ.get("SUPABASE_SECRET_KEY")

supabase_anon = create_client(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY)
supabase_admin = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)