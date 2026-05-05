"""
Continuous Thread Dump Monitoring System
Collects -> Analyzes -> Alerts -> Dashboard Sync
"""
import os
import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from shared.models import ThreadInfo, AlertMessage, AlertSeverity, IssueType
from shared.utils import parse_thread_dump, send_slack_alert
from shared.config import Config

# Import LangGraph analyzer
from agents.analyzer.analyzer_agent import create_analyzer_graph, AnalyzerState


class ContinuousMonitor:
    """Continuous monitoring system with collection, analysis, and alerting"""
    
    def __init__(self, interval: int = 60):
        self.interval = interval
        self.config = Config()
        self.dump_dir = Path("data/thread_dumps")
        self.alert_dir = Path("data/alerts")
        self.analysis_dir = Path("data/analysis_results")
        
        # Create directories
        self.dump_dir.mkdir(parents=True, exist_ok=True)
        self.alert_dir.mkdir(parents=True, exist_ok=True)
        self.analysis_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize analyzer
        self.analyzer = create_analyzer_graph()
        
        print("🚀 Continuous Monitor Initialized")
        print(f"   Interval: {interval} seconds")
        print(f"   Dump directory: {self.dump_dir}")
        print(f"   Alert directory: {self.alert_dir}")
        print(f"   Analysis directory: {self.analysis_dir}")
    
    def collect_thread_dump(self) -> Optional[Path]:
        """Collect a thread dump using jstack"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.dump_dir / f"jstack_dump_{timestamp}.txt"
            
            # Get PID from config
            pid = self.config.integration_server_pid
            if not pid:
                print("❌ No PID configured in .env file")
                return None
            
            print(f"\n📥 Collecting thread dump (PID: {pid})...")
            
            # Find jstack
            jstack_path = self._find_jstack()
            if not jstack_path:
                print("❌ jstack not found")
                return None
            
            # Run jstack
            cmd = [jstack_path, str(pid)]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode != 0:
                print(f"❌ jstack failed: {result.stderr}")
                return None
            
            # Save dump
            output_file.write_text(result.stdout, encoding='utf-8')
            print(f"✅ Thread dump saved: {output_file.name}")
            
            # Parse and save JSON
            threads = parse_thread_dump(result.stdout)
            json_file = output_file.with_suffix('.json')
            
            json_data = {
                "timestamp": timestamp,
                "pid": pid,
                "thread_count": len(threads),
                "threads": [
                    {
                        "name": t.name,
                        "thread_id": t.thread_id,
                        "state": t.state,
                        "cpu_time": t.cpu_time,
                        "is_daemon": t.is_daemon,
                        "priority": t.priority,
                        "stack_trace": t.stack_trace[:10] if t.stack_trace else []
                    }
                    for t in threads
                ]
            }
            
            json_file.write_text(json.dumps(json_data, indent=2), encoding='utf-8')
            print(f"✅ Parsed {len(threads)} threads -> {json_file.name}")
            
            return output_file
            
        except Exception as e:
            print(f"❌ Collection error: {e}")
            return None
    
    def analyze_dump(self, dump_file: Path) -> Optional[Dict[str, Any]]:
        """Analyze thread dump using LangGraph analyzer"""
        try:
            print(f"\n🔍 Analyzing {dump_file.name}...")
            
            # Read and parse dump
            dump_content = dump_file.read_text(encoding='utf-8')
            threads = parse_thread_dump(dump_content)
            
            if not threads:
                print("⚠️  No threads parsed from dump")
                return None
            
            # Detect issues
            hung_threads = [t for t in threads if t.is_hung()]
            long_running = [t for t in threads if 30 <= t.cpu_time < 60]
            blocked_threads = [t for t in threads if 'BLOCKED' in t.state or 'WAITING' in t.state]
            
            print(f"   Total threads: {len(threads)}")
            print(f"   Hung threads (>60s): {len(hung_threads)}")
            print(f"   Long-running (30-60s): {len(long_running)}")
            print(f"   Blocked/Waiting: {len(blocked_threads)}")
            
            # Run AI analysis if issues found
            if hung_threads or long_running or blocked_threads:
                print("   Running AI analysis...")
                
                initial_state = AnalyzerState(
                    thread_dump=dump_content,
                    threads=threads,
                    patterns=[],
                    issues=[],
                    recommendations=[],
                    analysis_complete=False
                )
                
                result = self.analyzer.invoke(initial_state)
                
                analysis_result = {
                    "timestamp": datetime.now().isoformat(),
                    "dump_file": dump_file.name,
                    "thread_count": len(threads),
                    "hung_threads": len(hung_threads),
                    "long_running_threads": len(long_running),
                    "blocked_threads": len(blocked_threads),
                    "patterns": result.get("patterns", []),
                    "issues": result.get("issues", []),
                    "recommendations": result.get("recommendations", []),
                    "severity": self._determine_severity(hung_threads, long_running, blocked_threads)
                }
                
                # Save analysis
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                analysis_file = self.analysis_dir / f"analysis_{timestamp}.json"
                analysis_file.write_text(json.dumps(analysis_result, indent=2), encoding='utf-8')
                print(f"✅ Analysis saved: {analysis_file.name}")
                
                return analysis_result
            else:
                print("✅ No issues detected - system healthy")
                return None
                
        except Exception as e:
            print(f"❌ Analysis error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def send_alert(self, analysis: Dict[str, Any]) -> bool:
        """Send alert to Slack and save to dashboard"""
        try:
            print(f"\n📢 Sending alert...")
            
            severity_map = {
                "CRITICAL": AlertSeverity.CRITICAL,
                "HIGH": AlertSeverity.HIGH,
                "MEDIUM": AlertSeverity.MEDIUM,
                "LOW": AlertSeverity.LOW
            }
            
            severity = severity_map.get(analysis["severity"], AlertSeverity.MEDIUM)
            
            # Determine issue type
            if analysis["hung_threads"] > 0:
                issue_type = IssueType.HUNG_THREAD
                title = f"Hung Thread Alert - {analysis['hung_threads']} thread(s) detected"
            elif analysis["long_running_threads"] > 0:
                issue_type = IssueType.LONG_RUNNING_THREAD
                title = f"Long-Running Thread Alert - {analysis['long_running_threads']} thread(s)"
            else:
                issue_type = IssueType.BLOCKED_THREAD
                title = f"Blocked Thread Alert - {analysis['blocked_threads']} thread(s)"
            
            # Create alert message
            alert = AlertMessage(
                severity=severity,
                title=title,
                timestamp=analysis["timestamp"],
                server_url=self.config.integration_server_url,
                description=f"Thread dump analysis detected {analysis['thread_count']} total threads with issues",
                issue_type=issue_type,
                recommendations=analysis.get("recommendations", [])[:5],
                metadata={
                    "dump_file": analysis["dump_file"],
                    "hung_threads": analysis["hung_threads"],
                    "long_running_threads": analysis["long_running_threads"],
                    "blocked_threads": analysis["blocked_threads"],
                    "patterns": analysis.get("patterns", [])[:3],
                    "issues": analysis.get("issues", [])[:3]
                }
            )
            
            # Save alert for dashboard
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            alert_file = self.alert_dir / f"alert_{timestamp}_{issue_type.value}.json"
            
            alert_dict = {
                "alert_id": None,
                "timestamp": alert.timestamp,
                "severity": str(severity.value) if hasattr(severity, 'value') else str(severity),
                "issue_type": issue_type.value,
                "title": alert.title,
                "description": alert.description,
                "server_url": alert.server_url,
                "recommendations": alert.recommendations,
                "metadata": alert.metadata,
                "status": "active"
            }
            
            alert_file.write_text(json.dumps(alert_dict, indent=2), encoding='utf-8')
            print(f"✅ Alert saved for dashboard: {alert_file.name}")
            
            # Send to Slack
            if self.config.slack_webhook_url:
                success = send_slack_alert(alert)
                if success:
                    print("✅ Alert sent to Slack")
                else:
                    print("⚠️  Failed to send Slack alert")
            else:
                print("⚠️  Slack webhook not configured")
            
            return True
            
        except Exception as e:
            print(f"❌ Alert error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _determine_severity(self, hung: List, long_running: List, blocked: List) -> str:
        """Determine alert severity based on thread counts"""
        if len(hung) >= 3:
            return "CRITICAL"
        elif len(hung) >= 1:
            return "HIGH"
        elif len(long_running) >= 5:
            return "HIGH"
        elif len(long_running) >= 2 or len(blocked) >= 10:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _find_jstack(self) -> Optional[str]:
        """Find jstack executable"""
        # Try common locations
        java_home = os.environ.get('JAVA_HOME')
        if java_home:
            jstack = Path(java_home) / 'bin' / 'jstack.exe'
            if jstack.exists():
                return str(jstack)
        
        # Try PATH
        result = subprocess.run(['where', 'jstack'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip().split('\n')[0]
        
        return None
    
    def run(self):
        """Run continuous monitoring loop"""
        print(f"\n{'='*60}")
        print("🎯 Starting Continuous Monitoring")
        print(f"{'='*60}\n")
        print("Press Ctrl+C to stop\n")
        
        iteration = 0
        
        try:
            while True:
                iteration += 1
                print(f"\n{'='*60}")
                print(f"📊 Monitoring Cycle #{iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'='*60}")
                
                # Step 1: Collect
                dump_file = self.collect_thread_dump()
                
                if dump_file:
                    # Step 2: Analyze
                    analysis = self.analyze_dump(dump_file)
                    
                    if analysis:
                        # Step 3: Alert
                        self.send_alert(analysis)
                
                # Wait for next cycle
                print(f"\n⏳ Waiting {self.interval} seconds until next cycle...")
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped by user")
        except Exception as e:
            print(f"\n\n❌ Monitoring error: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Continuous Thread Dump Monitoring")
    parser.add_argument('--interval', type=int, default=60, help='Collection interval in seconds (default: 60)')
    
    args = parser.parse_args()
    
    monitor = ContinuousMonitor(interval=args.interval)
    monitor.run()


if __name__ == "__main__":
    main()

# Made with Bob
