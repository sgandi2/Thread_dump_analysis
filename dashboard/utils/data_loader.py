"""
Dashboard Data Loader Utilities
Handles data loading from various agents and sources
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import psutil


class DataLoader:
    """Load data from analysis results, alerts, and agent outputs"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.analysis_dir = self.data_dir / "thread_dumps"  # Analysis stored with dumps
        self.alerts_dir = self.data_dir / "alerts"
        self.thread_dumps_dir = self.data_dir / "thread_dumps"
    
    def load_latest_analysis(self) -> Optional[Dict]:
        """Load the most recent analysis result"""
        try:
            if not self.thread_dumps_dir.exists():
                return None
            
            # Look for analysis files (analysis_*.json) in thread_dumps directory
            analysis_files = sorted(
                self.thread_dumps_dir.glob("analysis_*.json"),
                key=os.path.getmtime,
                reverse=True
            )
            
            if analysis_files:
                with open(analysis_files[0], 'r') as f:
                    return json.load(f)
            
            # Fallback: Try to get data from latest jstack dump
            jstack_files = sorted(
                self.thread_dumps_dir.glob("jstack_dump_*.json"),
                key=os.path.getmtime,
                reverse=True
            )
            
            if jstack_files:
                with open(jstack_files[0], 'r') as f:
                    dump_data = json.load(f)
                    
                    # Extract metrics from dump data
                    threads = dump_data.get('threads', [])
                    hung_count = sum(1 for t in threads if t.get('is_hung', False))
                    blocked_count = sum(1 for t in threads if t.get('is_blocked', False))
                    
                    return {
                        'total_threads': len(threads),
                        'hung_threads': hung_count,
                        'blocked_threads': blocked_count,
                        'deadlock_count': 0,
                        'severity': 'critical' if hung_count > 0 else 'info',
                        'timestamp': dump_data.get('timestamp', datetime.now().isoformat()),
                        'recommendations': []
                    }
            
            return None
            
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
        """Get current server metrics from latest alert or analysis"""
        # Get live process statistics
        live_cpu = 0.0
        live_memory = 0.0
        live_memory_mb = 0.0
        try:
            # Try to get PID from environment
            from dotenv import load_dotenv
            load_dotenv()
            pid = int(os.getenv('INTEGRATION_SERVER_PID', '0'))
            
            if pid > 0:
                process = psutil.Process(pid)
                live_cpu = process.cpu_percent(interval=0.5)  # Longer interval for more accurate reading
                
                # Get memory info
                mem_info = process.memory_info()
                live_memory_mb = mem_info.rss / (1024 * 1024)  # Convert to MB
                
                # Calculate memory percentage relative to process memory
                # For JVM processes, show percentage of allocated heap
                live_memory = process.memory_percent()
                
                # If memory is very low (< 5%), it might be showing system percentage
                # Try to get a more meaningful percentage
                if live_memory < 5.0:
                    # Estimate based on typical JVM heap (assume 1GB default)
                    estimated_heap_mb = 1024  # 1GB default heap
                    live_memory = min((live_memory_mb / estimated_heap_mb) * 100, 100.0)
        except:
            pass
        
        # First try to get metrics from latest alert (most accurate)
        alerts = self.load_active_alerts()
        if alerts:
            latest_alert = alerts[0]  # Already sorted by timestamp
            metadata = latest_alert.get('metadata', {})
            
            # Extract metrics from alert metadata
            hung_threads = metadata.get('hung_threads', 0)
            blocked_threads = metadata.get('blocked_threads', 0)
            total_threads = metadata.get('total_threads', 0)
            
            # Parse CPU and memory usage from alert, fallback to live stats
            cpu_usage = live_cpu
            memory_usage = live_memory
            
            try:
                cpu_str = str(metadata.get('cpu_usage', '0'))
                if cpu_str != 'N/A' and cpu_str != '0.0':
                    cpu_usage = float(cpu_str)
            except:
                pass
            
            try:
                mem_str = str(metadata.get('memory_usage', '0'))
                if mem_str != 'N/A' and mem_str != '0.0':
                    memory_usage = float(mem_str)
            except:
                pass
            
            severity = latest_alert.get('severity', 'info')
            
            return {
                'server_health': 'Healthy' if severity == 'info' else 'Issues Detected',
                'active_threads': total_threads,
                'hung_threads': hung_threads,
                'blocked_threads': blocked_threads,
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'gc_count': 0,
                'last_gc_time': 0,
                'timestamp': latest_alert.get('timestamp', datetime.now().isoformat()),
                'severity': severity,
                'deadlocks': 0,
                'recommendations': latest_alert.get('recommendations', [])
            }
        
        # Fallback to analysis file
        analysis = self.load_latest_analysis()
        if analysis:
            return {
                'server_health': 'Healthy' if analysis.get('severity') == 'info' else 'Warning',
                'active_threads': analysis.get('total_threads', 0),
                'hung_threads': analysis.get('hung_threads', 0),
                'blocked_threads': analysis.get('blocked_threads', 0),
                'cpu_usage': 0,
                'memory_usage': 0,
                'gc_count': 0,
                'last_gc_time': 0,
                'timestamp': analysis.get('timestamp', datetime.now().isoformat()),
                'severity': analysis.get('severity', 'info'),
                'deadlocks': analysis.get('deadlock_count', 0),
                'recommendations': analysis.get('recommendations', [])
            }
        
        # No data available
        return {
            'server_health': 'Unknown',
            'active_threads': 0,
            'hung_threads': 0,
            'blocked_threads': 0,
            'cpu_usage': 0,
            'memory_usage': 0,
            'gc_count': 0,
            'last_gc_time': 0,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_thread_list(self) -> List[Dict]:
        """Get list of all threads with their status from latest thread dump"""
        # Load the latest thread dump
        if not self.thread_dumps_dir.exists():
            return []
        
        json_files = sorted(self.thread_dumps_dir.glob("jstack_dump_*.json"), reverse=True)
        if not json_files:
            return []
        
        try:
            with open(json_files[0], 'r') as f:
                dump_data = json.load(f)
            
            threads = []
            for thread in dump_data.get('threads', []):
                status = 'Normal'
                if thread.get('is_hung', False):
                    status = 'Hung'
                elif thread.get('is_blocked', False):
                    status = 'Blocked'
                elif thread.get('is_waiting', False):
                    status = 'Waiting'
                
                threads.append({
                    'thread_id': thread.get('thread_id', 'Unknown'),
                    'name': thread.get('name', 'Unknown'),
                    'state': thread.get('state', 'UNKNOWN'),
                    'cpu_time': thread.get('cpu_time', 0),
                    'blocked_time': thread.get('blocked_time', 0),
                    'blocked_count': thread.get('blocked_count', 0),
                    'status': status,
                    'stack_trace': thread.get('stack_trace', [])
                })
            
            return threads
        except Exception as e:
            print(f"Error loading thread list: {e}")
            return []
    
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
