import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase credentials missing from environment variables.")

# Create a single client instance
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Dependency injection provider for FastAPI routes
def get_supabase():
    try:
        yield supabase
    except Exception as e:
        print(f"Database error: {e}")
        raise
    finally:
        supabase.close()