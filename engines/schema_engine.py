import json
from pathlib import Path

class SchemaEngine:
    def __init__(self, config_path: str = "config/api_schemas.json"):
        with open(config_path) as f:
            self.schemas = json.load(f)
    
    def get_api_config(self, api_name: str) -> dict:
        return self.schemas["apis"].get(api_name, {})
    
    def get_endpoint(self, api_name: str, endpoint_name: str) -> str:
        api = self.get_api_config(api_name)
        return api.get("endpoints", {}).get(endpoint_name)
    
    def get_fields(self, api_name: str) -> list:
        api = self.get_api_config(api_name)
        return api.get("fields", [])
