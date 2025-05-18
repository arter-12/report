import os
from typing import Dict, Any
import json

class Config:
    def __init__(self):
        self.api_id = int(os.getenv('API_ID', ''))
        self.api_hash = os.getenv('API_HASH', '')
        self.bot_token = os.getenv('BOT_TOKEN', '')
        self.owner_id = int(os.getenv('OWNER_ID', '0'))
        
        # Load additional config from file if exists
        self.config_file = 'config/config.json'
        self.data = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {}

    @property
    def authorized_users(self) -> list:
        return self.data.get('authorized_users', [])

    @property
    def report_delay(self) -> int:
        return int(self.data.get('report_delay', 2))

    @property
    def max_sessions(self) -> int:
        return int(self.data.get('max_sessions', 50))

    def update_config(self, key: str, value: Any):
        self.data[key] = value
        with open(self.config_file, 'w') as f:
            json.dump(self.data, f, indent=4)
