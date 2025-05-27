import os
import requests
from typing import List, Dict

class ParserService:
    def __init__(self):
        self.api_key = os.getenv('COMPANY_API_KEY')
        self.api_endpoint = os.getenv('COMPANY_API_ENDPOINT')
    
    async def process_resumes(self, resumes: List[str], job_description: str) -> Dict:
        # Prepare data for company API
        payload = {
            "resumes": resumes,
            "job_description": job_description,
            "api_key": self.api_key
        }
        
        try:
            response = requests.post(self.api_endpoint, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # Handle errors appropriately
            raise Exception(f"API call failed: {str(e)}")