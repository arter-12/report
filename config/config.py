from typing import Dict, Any
import json
import os

class Config:
    def __init__(self, config_file: str = "config/config.json"):
        self.config_file = config_file
        self.data = self._load_config()
        self._validate_config()

    def _load_config(self) -> Dict[str, Any]:
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Config file not found: {self.config_file}")
        
        with open(self.config_file, 'r') as f:
            return json.load(f)

    def _validate_config(self):
        required_fields = ['api_id', 'api_hash', 'bot_token', 'owner_id']
        for field in required_fields:
            if field not in self.data:
                raise ValueError(f"Missing required config field: {field}")

    @property
    def api_id(self) -> int:
        return int(self.data['api_id'])

    @property
    def api_hash(self) -> str:
        return self.data['api_hash']

    @property
    def bot_token(self) -> str:
        return self.data['bot_token']

    @property
    def owner_id(self) -> int:
        return int(self.data['owner_id'])

    @property
    def authorized_users(self) -> list:
        return self.data.get('authorized_users', [])

    def update_config(self, key: str, value: Any):
        self.data[key] = value
        with open(self.config_file, 'w') as f:
            json.dump(self.data, f, indent=4)
