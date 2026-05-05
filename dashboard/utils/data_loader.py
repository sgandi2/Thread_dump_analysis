"""
Dashboard Data Loader Utilities
Handles data loading from various agents and sources
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class DataLoader:
    """Load data from analysis results, alerts, and agent outputs"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.analysis_dir = self.data_dir / "analysis_results"
        self.alerts_dir = self.data_dir / "alerts"
        self.thread_dumps_dir = self.data_dir / "thread_dumps"
    
    def load_latest_analysis(self) -> Optional[Dict]:
        """Load the most recent analysis result"""
        try:
            if not self.analysis_dir.exists():
                return None
            
            files = sorted(self.analysis_dir.glob("*.json"), key=os.path.getmtime, reverse=True)
            if not files:
                return None
            
            with open(files[0], 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading analysis: {e}")
            return None
    
    def load_active_alerts(self) -> List[Dict]:
        """Load all active alerts"""
        try:
            if not self.alerts_dir.exists():
                return []
            
            alerts = []
            for file in self.alerts_dir.glob("*.json"):
                with open(file, 'r') as f:
                    alert = json.load(f)
                    if alert.get('status') == 'active':
                        alerts.append(alert)
            
            return sorted(alerts, key=lambda x: x.get('timestamp', ''), reverse=True)
        except Exception as e:
            print(f"Error loading alerts: {e}")
            return []
    
    def load_thread_dump(self, filename: str) -> Optional[Dict]:
        """Load a specific thread dump"""
        try:
            filepath = self.thread_dumps_dir / filename
            if not filepath.exists():
                return None
            
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading thread dump: {e}")
            return None
    
    def get_server_metrics(self) -> Dict:
        """Get current server metrics (mock for now)"""
        # In production, this would call the monitor agent or MCP server
        return {
            'server_health': 'Healthy',
            'active_threads': 45,
            'hung_threads': 2,
            'blocked_threads': 1,
            'cpu_usage': 67.5,
            'memory_usage': 78.3,
            'gc_count': 15,
            'last_gc_time': 0.023,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_thread_list(self) -> List[Dict]:
        """Get list of all threads with their status"""
        # In production, this would call the collector agent
        return [
            {
                'thread_id': 'Thread-1',
                'name': 'HTTP-Worker-1',
                'state': 'RUNNABLE',
                'cpu_time': 450.2,
                'blocked_time': 0,
                'status': 'Normal'
            },
            {
                'thread_id': 'Thread-2',
                'name': 'DB-Connection-Pool',
                'state': 'WAITING',
                'cpu_time': 120.5,
                'blocked_time': 305.0,
                'status': 'Hung'
            },
            {
                'thread_id': 'Thread-3',
                'name': 'JMS-Listener',
                'state': 'BLOCKED',
                'cpu_time': 89.3,
                'blocked_time': 45.2,
                'status': 'Blocked'
            }
        ]
    
    def get_performance_history(self, metric: str, duration_minutes: int = 10) -> List[Dict]:
        """Get historical performance data"""
        # In production, this would query a time-series database
        import random
        from datetime import timedelta
        
        data = []
        now = datetime.now()
        
        for i in range(duration_minutes * 2):  # Every 30 seconds
            timestamp = now - timedelta(seconds=30 * (duration_minutes * 2 - i))
            
            if metric == 'cpu':
                value = random.uniform(50, 85)
            elif metric == 'memory':
                value = random.uniform(65, 82)
            else:
                value = random.uniform(0, 100)
            
            data.append({
                'timestamp': timestamp.isoformat(),
                'value': value
            })
        
        return data

# Made with Bob
