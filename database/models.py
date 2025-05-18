from datetime import datetime, timezone
from typing import Dict, List, Optional, Union
import json

class User:
    def __init__(self, user_id: int, **kwargs):
        self.user_id = user_id
        self.username = kwargs.get('username', '')
        self.first_name = kwargs.get('first_name', '')
        self.language = kwargs.get('language', 'en')
        self.joined_date = kwargs.get('joined_date', datetime.now(timezone.utc).isoformat())
        self.is_premium = kwargs.get('is_premium', False)
        self.settings = kwargs.get('settings', {
            'notifications': True,
            'theme': 'default',
            'auto_report': False,
            'report_delay': 2,
            'max_sessions': 50
        })
        self.stats = kwargs.get('stats', {
            'total_reports': 0,
            'successful_reports': 0,
            'failed_reports': 0,
            'last_report': None
        })

    def to_dict(self) -> dict:
        return {
            'user_id': self.user_id,
            'username': self.username,
            'first_name': self.first_name,
            'language': self.language,
            'joined_date': self.joined_date,
            'is_premium': self.is_premium,
            'settings': self.settings,
            'stats': self.stats
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        return cls(**data)

class Session:
    def __init__(self, **kwargs):
        self.session_id = kwargs.get('session_id', '')
        self.user_id = kwargs.get('user_id', 0)
        self.session_string = kwargs.get('session_string', '')
        self.phone_number = kwargs.get('phone_number', '')
        self.first_name = kwargs.get('first_name', '')
        self.added_date = kwargs.get('added_date', datetime.now(timezone.utc).isoformat())
        self.last_used = kwargs.get('last_used', datetime.now(timezone.utc).isoformat())
        self.last_verified = kwargs.get('last_verified', datetime.now(timezone.utc).isoformat())
        self.is_active = kwargs.get('is_active', True)
        self.reports_count = kwargs.get('reports_count', 0)
        self.success_rate = kwargs.get('success_rate', 0.0)

    def to_dict(self) -> dict:
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'session_string': self.session_string,
            'phone_number': self.phone_number,
            'first_name': self.first_name,
            'added_date': self.added_date,
            'last_used': self.last_used,
            'last_verified': self.last_verified,
            'is_active': self.is_active,
            'reports_count': self.reports_count,
            'success_rate': self.success_rate
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Session':
        return cls(**data)

class Report:
    def __init__(self, **kwargs):
        self.report_id = kwargs.get('report_id', '')
        self.user_id = kwargs.get('user_id', 0)
        self.target_type = kwargs.get('target_type', '')
        self.target_id = kwargs.get('target_id', '')
        self.reason = kwargs.get('reason', '')
        self.timestamp = kwargs.get('timestamp', datetime.now(timezone.utc).isoformat())
        self.sessions_used = kwargs.get('sessions_used', [])
        self.success_count = kwargs.get('success_count', 0)
        self.fail_count = kwargs.get('fail_count', 0)
        self.status = kwargs.get('status', 'pending')

    def to_dict(self) -> dict:
        return {
            'report_id': self.report_id,
            'user_id': self.user_id,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'reason': self.reason,
            'timestamp': self.timestamp,
            'sessions_used': self.sessions_used,
            'success_count': self.success_count,
            'fail_count': self.fail_count,
            'status': self.status
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Report':
        return cls(**data)
