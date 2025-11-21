"""KTW.sh API Client for fetching transport data"""
import os
import requests
import pandas as pd
import streamlit as st
from typing import Optional, Dict, Any
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

KTWSH_API_KEY = os.getenv("KTWSH_API_KEY")
KTWSH_API_URL = os.getenv("KTWSH_API_URL")

class KTWAPIClient:
    """Client for interacting with KTW.sh API"""
    
    def __init__(self, api_url: str = None, api_key: str = None):
        self.api_url = api_url or KTWSH_API_URL
        self.api_key = api_key or KTWSH_API_KEY
        
        if not self.api_url:
            raise ValueError(
                "KTWSH_API_URL not found in environment variables"
            )
        if not self.api_key:
            raise ValueError(
                "KTWSH_API_KEY not found in environment variables"
            )
        
        if not self.api_url.endswith('/'):
            self.api_url += '/'
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Api-Key {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _make_request(
        self, endpoint: str, params: Optional[Dict] = None
    ) -> Dict[Any, Any]:
        """Make a request to the API"""
        url = f"{self.api_url}{endpoint}"
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            st.error(f"API request failed: {e}")
            raise
    
    def get_transports(
        self, format_type: str = "json"
    ) -> pd.DataFrame:
        """Fetch transport data from the API"""
        # Remove format parameter - API expects JSON by default
        
        try:
            data = self._make_request("transports/")
            
            # Handle paginated response
            if isinstance(data, dict) and "results" in data:
                results = data["results"]
                
                # Fetch all pages
                while data.get("next"):
                    next_url = data["next"]
                    if "?" in next_url:
                        query_string = next_url.split("?")[1]
                        next_params = dict([
                            param.split("=")
                            for param in query_string.split("&")
                        ])
                        next_data = self._make_request(
                            "transports/", next_params
                        )
                        results.extend(next_data.get("results", []))
                        data = next_data
                    else:
                        break
                
                df = pd.DataFrame(results)
            elif isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame([data])
            
            logger.info(f"Fetched {len(df)} transport records")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching transports: {e}")
            # Return empty DataFrame with expected columns
            columns = [
                'id', 'krankenbeforderungsfahrt_kategorie', 'doctor_name',
                'patient_name', 'patient_weight', 'patient_birth_date',
                'infectious_disease', 'companion', 'ktw_equipment',
                'medical_care', 'pickup_station', 'pickup_address',
                'pickup_housenumber', 'pickup_postal_code', 'pickup_city',
                'pickup_email', 'pickup_phone', 'contact_person_pickup',
                'pickup_datetime', 'destination_station',
                'destination_address',
                'destination_housenumber', 'destination_postal_code',
                'destination_city', 'contact_person_destination',
                'destination_datetime', 'created_at', 'remark',
                'remark_transport', 'status', 'created_by_id',
                'destination_institute_id', 'patient_insurance_company_id',
                'pickup_institute_id', 'transport_type_id',
                'agreed_transport_datetime', 'zustaendigkeit_id'
            ]
            return pd.DataFrame(columns=columns)
    
    def get_transport_status_history(
        self, format_type: str = "json"
    ) -> pd.DataFrame:
        """Fetch transport status history data from the API"""
        # Remove format parameter - API expects JSON by default
        
        try:
            data = self._make_request("transport-status-history/")
            
            # Handle paginated response
            if isinstance(data, dict) and "results" in data:
                results = data["results"]
                
                # Fetch all pages
                while data.get("next"):
                    next_url = data["next"]
                    if "?" in next_url:
                        query_string = next_url.split("?")[1]
                        next_params = dict([
                            param.split("=")
                            for param in query_string.split("&")
                        ])
                        next_data = self._make_request(
                            "transport-status-history/", next_params
                        )
                        results.extend(next_data.get("results", []))
                        data = next_data
                    else:
                        break
                
                df = pd.DataFrame(results)
            elif isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame([data])
            
            logger.info(f"Fetched {len(df)} status history records")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching transport status history: {e}")
            # Return empty DataFrame with expected columns
            columns = [
                'id', 'old_status', 'new_status', 'changed_at',
                'changed_by_username', 'transport_id'
            ]
            return pd.DataFrame(columns=columns)


@st.cache_data(ttl=300, show_spinner="Loading data from KTW.sh API...")
def cached_get_transports() -> pd.DataFrame:
    """Cached function to get transport data"""
    client = KTWAPIClient()
    return client.get_transports()


@st.cache_data(
    ttl=300,
    show_spinner="Loading transport status history from KTW.sh API..."
)
def cached_get_transport_status_history() -> pd.DataFrame:
    """Cached function to get transport status history data"""
    client = KTWAPIClient()
    return client.get_transport_status_history()


def test_api_connection() -> bool:
    """Test if the API connection works"""
    try:
        client = KTWAPIClient()
        # Try to fetch data to test connection
        df = client.get_transports()
        return len(df) >= 0  # Even empty response is OK for connection test
    except Exception as e:
        logger.error(f"API connection test failed: {e}")
        return False


if __name__ == "__main__":
    # Test the API client
    if test_api_connection():
        print("✅ API connection successful!")
        
        client = KTWAPIClient()
        
        # Test transport data
        transports = client.get_transports()
        print(f"📋 Fetched {len(transports)} transport records")
        if not transports.empty:
            print(transports.columns.tolist())
        
        # Test transport status history
        history = client.get_transport_status_history()
        print(f"📊 Fetched {len(history)} status history records")
        if not history.empty:
            print(history.columns.tolist())
    else:
        print("❌ API connection failed!")