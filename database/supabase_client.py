from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

def get_supabase_client() -> Client:
    """
    Initializes and returns a synchronous Supabase client.
    For async operations, this client needs to be properly wrapped or its async
    counterpart used, which will be handled when building the async bot itself.
    This is a temporary synchronous client for table verification.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase URL and Key must be set in the .env file.")
    
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return supabase

print("Synchronous Supabase client function defined for temporary use.")
