import logging
from database.supabase_http_client import supabase_http_client

# --- Prices ---
PRICE_EARLY_BIRD = 400
PRICE_REGULAR = 600

async def get_current_price() -> int:
    """
    Determines the current price based on the Early Bird counter.
    """
    try:
        # Fetch counter and limit from the settings table
        settings = await supabase_http_client.select("settings", params={"key": "in.(early_bird_counter,early_bird_limit)"})
        
        counter = 0
        limit = 50 # Default limit

        for setting in settings:
            if setting['key'] == 'early_bird_counter':
                counter = int(setting['value'])
            elif setting['key'] == 'early_bird_limit':
                limit = int(setting['value'])
        
        if counter < limit:
            return PRICE_EARLY_BIRD
        else:
            return PRICE_REGULAR
    except Exception as e:
        logging.error(f"Could not determine price from DB, falling back to regular price. Error: {e}")
        return PRICE_REGULAR
