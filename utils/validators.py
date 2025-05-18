import re
from typing import Union, Tuple

class Validators:
    @staticmethod
    def validate_session_string(session_string: str) -> bool:
        """Validate session string format"""
        if not session_string:
            return False
        
        # Basic format check for Pyrogram session string
        pattern = r'^[A-Za-z0-9+/]{279}={1}$'
        return bool(re.match(pattern, session_string))

    @staticmethod
    def validate_chat_link(link: str) -> Tuple[bool, str]:
        """Validate Telegram chat link"""
        patterns = {
            'public_channel': r'^https?://t\.me/([a-zA-Z0-9_]{5,})$',
            'private_channel': r'^https?://t\.me/\+([a-zA-Z0-9_-]+)$',
            'message_link': r'^https?://t\.me/[a-zA-Z0-9_]{5,}/(\d+)$'
        }
        
        for link_type, pattern in patterns.items():
            if match := re.match(pattern, link):
                return True, link_type
        
        return False, 'invalid'

    @staticmethod
    def validate_report_reason(reason: str) -> bool:
        """Validate report reason"""
        valid_reasons = [
            'spam', 'violence', 'pornography', 'child_abuse',
            'copyright', 'fake', 'illegal', 'personal',
            'other'
        ]
        return reason in valid_reasons

    @staticmethod
    def validate_language_code(code: str) -> bool:
        """Validate language code"""
        valid_languages = ['en', 'es', 'ru', 'ar', 'hi', 'zh']
        return code in valid_languages

class InputFormatter:
    @staticmethod
    def format_phone_number(phone: str) -> str:
        """Format phone number"""
        # Remove all non-numeric characters
        numbers_only = re.sub(r'\D', '', phone)
        
        # Ensure it starts with '+'
        if not numbers_only.startswith('+'):
            numbers_only = '+' + numbers_only
            
        return numbers_only

    @staticmethod
    def format_username(username: str) -> str:
        """Format username"""
        # Remove '@' if present
        username = username.lstrip('@')
        
        # Ensure it only contains valid characters
        if not re.match(r'^[a-zA-Z0-9_]{5,32}$', username):
            raise ValueError("Invalid username format")
            
        return username

    @staticmethod
    def format_chat_link(link: str) -> str:
        """Format chat link"""
        # Ensure https://
        if not link.startswith('https://'):
            link = 'https://' + link.lstrip('http://')
            
        # Ensure t.me domain
        if 'telegram.me' in link:
            link = link.replace('telegram.me', 't.me')
            
        return link
