from typing import Dict, List, Union, Optional
from datetime import datetime, timezone
import asyncio
import logging
import json
import re

class SessionManager:
    def __init__(self, db, config):
        self.db = db
        self.config = config
        self.active_clients = {}
        self.client_locks = {}

    async def get_client(self, session_string: str):
        """Get or create client for session"""
        if session_string in self.active_clients:
            return self.active_clients[session_string]

        if session_string not in self.client_locks:
            self.client_locks[session_string] = asyncio.Lock()

        async with self.client_locks[session_string]:
            try:
                client = Client(
                    session_name=f"session_{len(self.active_clients)}",
                    session_string=session_string,
                    api_id=self.config.api_id,
                    api_hash=self.config.api_hash,
                    in_memory=True
                )
                await client.start()
                self.active_clients[session_string] = client
                return client
            except Exception as e:
                logging.error(f"Failed to create client: {str(e)}")
                raise

    async def close_all_clients(self):
        """Close all active clients"""
        for session_string, client in self.active_clients.items():
            try:
                await client.stop()
            except Exception as e:
                logging.error(f"Error closing client: {str(e)}")
        self.active_clients.clear()

class ReportManager:
    def __init__(self, db, session_manager):
        self.db = db
        self.session_manager = session_manager
        self.report_queue = asyncio.Queue()
        self.is_processing = False

    async def add_report(self, report: Dict):
        """Add report to queue"""
        await self.report_queue.put(report)
        if not self.is_processing:
            asyncio.create_task(self.process_reports())

    async def process_reports(self):
        """Process reports from queue"""
        self.is_processing = True
        while not self.report_queue.empty():
            report = await self.report_queue.get()
            try:
                await self.execute_report(report)
            except Exception as e:
                logging.error(f"Report processing error: {str(e)}")
            finally:
                self.report_queue.task_done()
        self.is_processing = False

    async def execute_report(self, report: Dict):
        """Execute a single report"""
        sessions = self.db.get_user_sessions(report['user_id'])
        results = {
            'success': 0,
            'failed': 0,
            'total': len(sessions)
        }

        for session in sessions:
            try:
                client = await self.session_manager.get_client(session['session_string'])
                # Execute report based on target_type
                if report['target_type'] == 'channel':
                    await client.report_chat(report['target_id'], report['reason'])
                elif report['target_type'] == 'message':
                    chat_id, message_id = report['target_id'].split('/')
                    await client.report_message(chat_id, int(message_id), report['reason'])
                
                results['success'] += 1
                session['success_count'] += 1
            except Exception as e:
                results['failed'] += 1
                session['fail_count'] += 1
                logging.error(f"Report execution error: {str(e)}")
            
            # Update session stats
            session['total_reports'] += 1
            session['success_rate'] = (session['success_count'] / session['total_reports']) * 100
            self.db.update_session(session)
            
            await asyncio.sleep(report.get('delay', 2))  # Anti-flood delay

        # Update report status
        report['status'] = 'completed'
        report['success_count'] = results['success']
        report['fail_count'] = results['failed']
        self.db.update_report(report)

        return results

class StatsManager:
    def __init__(self, db):
        self.db = db

    def update_user_stats(self, user_id: int, report_result: Dict):
        """Update user statistics"""
        user = self.db.get_user(user_id)
        stats = user.stats
        
        stats['total_reports'] += 1
        stats['successful_reports'] += report_result['success']
        stats['failed_reports'] += report_result['failed']
        stats['last_report'] = datetime.now(timezone.utc).isoformat()
        
        if stats['total_reports'] > 0:
            stats['success_rate'] = (stats['successful_reports'] / stats['total_reports']) * 100
        
        user.stats = stats
        self.db.update_user(user)

    def get_user_stats(self, user_id: int) -> Dict:
        """Get user statistics"""
        user = self.db.get_user(user_id)
        return {
            'total_reports': user.stats['total_reports'],
            'successful_reports': user.stats['successful_reports'],
            'failed_reports': user.stats['failed_reports'],
            'success_rate': user.stats['success_rate'],
            'last_report': user.stats['last_report'],
            'active_sessions': len(self.db.get_user_sessions(user_id))
        }
