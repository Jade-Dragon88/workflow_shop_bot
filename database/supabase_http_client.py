import httpx
import logging
from typing import List, Dict, Any, Optional

from config import SUPABASE_URL, SUPABASE_KEY

# The schema where all our tables are located
SCHEMA_NAME = "n8n_workflows_sales"

class SupabaseHttpClient:
    """
    A simple asynchronous HTTP client for interacting with the Supabase PostgREST API.
    This client is tailored for the needs of this specific bot.
    """

    def __init__(self, url: str, key: str, schema: str):
        if not url or not key:
            raise ValueError("Supabase URL and Key must be set.")
        
        self._url = f"{url}/rest/v1"
        self._schema = schema
        # Base headers, schema-specific headers will be added per request
        self._base_headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
        }
        self._client = httpx.AsyncClient()

    async def select(self, table: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Performs a SELECT operation on a table.
        """
        headers = self._base_headers.copy()
        headers["Accept-Profile"] = self._schema # Correct header for GET

        try:
            response = await self._client.get(
                f"{self._url}/{table}", 
                params=params, 
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error during SELECT on '{table}': {e.response.status_code} - {e.response.text}")
            return []
        except Exception as e:
            logging.error(f"Unexpected error during SELECT on '{table}': {e}", exc_info=True)
            return []

    async def insert(self, table: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Performs an INSERT operation on a table.
        """
        headers = self._base_headers.copy()
        headers["Content-Profile"] = self._schema # Correct header for POST
        headers["Content-Type"] = "application/json"
        headers["Prefer"] = "return=representation"

        try:
            response = await self._client.post(
                f"{self._url}/{table}", 
                json=data, 
                headers=headers
            )
            response.raise_for_status()
            
            result = response.json()
            return result[0] if result else None
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error during INSERT on '{table}': {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error during INSERT on '{table}': {e}", exc_info=True)
            return None

    async def rpc(self, function_name: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Calls a PostgreSQL function (RPC).
        """
        headers = self._base_headers.copy()
        headers["Content-Type"] = "application/json"
        
        try:
            response = await self._client.post(
                f"{self._url}/rpc/{function_name}",
                json=params,
                headers=headers
            )
            response.raise_for_status()
            if response.status_code == 204 or not response.content:
                return None
            return response.json()
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error during RPC call to '{function_name}': {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error during RPC call to '{function_name}': {e}", exc_info=True)
            return None

    async def update(self, table: str, match: Dict[str, Any], new_data: Dict[str, Any]) -> Any:
        """
        Performs an UPDATE operation on a table.
        """
        headers = self._base_headers.copy()
        headers["Content-Profile"] = self._schema
        headers["Content-Type"] = "application/json"
        
        query_params = {key: f"eq.{value}" for key, value in match.items()}
        
        try:
            response = await self._client.patch(
                f"{self._url}/{table}",
                params=query_params,
                json=new_data,
                headers=headers
            )
            response.raise_for_status()
            if response.status_code == 204:
                return True
            return response.json()
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error during UPDATE on '{table}': {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error during UPDATE on '{table}': {e}", exc_info=True)
            return None

# Initialize the HTTP client instance for global use
supabase_http_client = SupabaseHttpClient(url=SUPABASE_URL, key=SUPABASE_KEY, schema=SCHEMA_NAME)
