#!/usr/bin/env python3
"""
Analyze thread dumps from Integration Server
Supports both TXT (raw thread dumps) and JSON (parsed dumps)
"""
import json
import sys
import io
import os
import re
import argparse
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from shared.models import ThreadInfo, AlertMessage, IssueType, AlertSeverity
from shared.utils import parse_thread_dump
from agents.analyzer.analyzer_agent import ThreadDumpAnalyzerAgent
from agents.monitor.slack_notifier import SlackNotifier
from generate_ai_recommendations import generate_ai_recommendations
from get_is_stats import get_integration_server_stats


def get_pid_from_env():
    """Get PID from .env file"""
    try:
        from shared.config import config
        # Try to get from config
        if hasattr(config, 'INTEGRATION_SERVER_PID'):
            return config.INTEGRATION_SERVER_PID
    except:
        pass
    
    # Try to read from .env directly
    env_file = Path('.env')
    if env_file.exists():
        content = env_file.read_text()
        match = re.search(r'INTEGRATION_SERVER_PID=(\d+)', content)
        if match:
            return int(match.group(1))
    
    return None

def get_process_stats(pid):
    """Get CPU and memory stats for a process"""
    try:
        import psutil
        process = psutil.Process(pid)
        return {
            'cpu_percent': process.cpu_percent(interval=0.1),
            'memory_percent': process.memory_percent(),
            'memory_mb': process.memory_info().rss / (1024 * 1024)
        }
    except:
        return None

def main():
    """Analyze thread dumps"""
    
    parser = argparse.ArgumentParser(description='Analyze thread dumps')
    parser.add_argument('--file', help='Specific file to analyze')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    dump_dir = Path("data/thread_dumps")
    
    if args.file:
        latest_dump = Path(args.file)
        if not latest_dump.exists():
            print(f"❌ File not found: {args.file}")
            return 1
    else:
        # Find most recent file
        all_files = sorted(dump_dir.glob("*.txt"), key=lambda x: x.stat().st_mtime, reverse=True)
        if not all_files:
            print("❌ No thread dumps found!")
            return 1
        latest_dump = all_files[0]
    
    # Get PID from environment
    pid = get_pid_from_env()
    
    # Get Integration Server statistics via REST API
    from shared.config import config
    is_stats = None
    try:
        is_stats = get_integration_server_stats(
            server_url=config.WEBMETHODS_URL,
            username=config.WEBMETHODS_USER,
            password=config.WEBMETHODS_PASSWORD
        )
    except Exception as e:
        print(f"   Note: Could not fetch IS REST API stats: {str(e)[:50]}")
    
    # Fallback to psutil if IS stats not available
    process_stats = None
    if pid and (not is_stats or is_stats.get('memory_percent', 0) == 0):
        process_stats = get_process_stats(pid)
    
    print(f"📊 Analyzing: {latest_dump.name}")
    print("=" * 70)
    
    if pid:
        print(f"\n🔧 Integration Server Information:")
        print(f"   Process ID: {pid}")
        print(f"   Server URL: {config.WEBMETHODS_URL}")
        
        if is_stats and is_stats.get('memory_percent', 0) > 0:
            print(f"   Memory Usage: {is_stats.get('memory_used_mb', 0):.1f}MB / {is_stats.get('memory_max_mb', 0):.1f}MB ({is_stats.get('memory_percent', 0):.1f}%)")
            print(f"   Thread Count: {is_stats.get('thread_count', 0)} total, {is_stats.get('active_threads', 0)} active")
            if 'cpu_percent' in is_stats:
                print(f"   CPU Usage: {is_stats.get('cpu_percent', 0):.1f}%")
        elif process_stats:
            print(f"   CPU Usage: {process_stats.get('cpu_percent', 0):.1f}% (from process)")
            print(f"   Memory Usage: {process_stats.get('memory_mb', 0):.1f}MB ({process_stats.get('memory_percent', 0):.1f}%)")
        else:
            print(f"   ⚠️  Could not fetch server statistics")
    else:
        print(f"\n⚠️  Process ID not found in .env file")
    
    # Parse thread dump
    with open(latest_dump, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    threads = parse_thread_dump(content)
    
    if not threads:
        print("❌ No threads found in dump")
        return 1
    
    print(f"\n📈 Thread Dump Statistics:")
    print(f"   Total Threads: {len(threads)}")
    
    # Calculate statistics
    states = {}
    hung_threads = []
    long_running_threads = []
    blocked_threads = []
    waiting_threads = []
    
    for thread in threads:
        # Count states
        state = thread.state
        states[state] = states.get(state, 0) + 1
        
        # Check for issues
        if thread.cpu_time > 60:  # Hung threshold (demo: 60s)
            hung_threads.append(thread)
        elif thread.cpu_time > 30:  # Long-running threshold
            long_running_threads.append(thread)
        
        if thread.state == "BLOCKED":
            blocked_threads.append(thread)
        if thread.state == "WAITING":
            waiting_threads.append(thread)
    
    print(f"\n🔍 Thread States:")
    for state, count in sorted(states.items()):
        print(f"   {state}: {count}")
    
    print(f"\n⚠️  Potential Issues:")
    print(f"   Hung Threads (>60s CPU): {len(hung_threads)}")
    print(f"   Long-Running Threads (30-60s): {len(long_running_threads)}")
    print(f"   Blocked Threads: {len(blocked_threads)}")
    print(f"   Waiting Threads: {len(waiting_threads)}")
    # Analyze root causes from stack traces
    def analyze_root_cause(threads_list, issue_type):
        """Analyze stack traces to determine root cause"""
        if not threads_list:
            return "No specific root cause identified"
        
        root_causes = []
        operations = {
            'database': [],
            'network': [],
            'file_io': [],
            'lock_wait': [],
            'computation': []
        }
        
        for thread in threads_list[:5]:  # Analyze top 5
            if not thread.stack_trace:
                continue
            
            stack_str = '\n'.join(thread.stack_trace[:10])
            
            # Detect operation types
            if any(keyword in stack_str.lower() for keyword in ['jdbc', 'sql', 'database', 'query']):
                operations['database'].append(thread.name)
                method = next((line for line in thread.stack_trace if 'jdbc' in line.lower() or 'sql' in line.lower()), thread.stack_trace[0] if thread.stack_trace else 'Unknown')
                root_causes.append(f"Database operation in {thread.name}: {method[:80]}")
            
            elif any(keyword in stack_str.lower() for keyword in ['socket', 'http', 'network', 'connect']):
                operations['network'].append(thread.name)
                method = next((line for line in thread.stack_trace if any(k in line.lower() for k in ['socket', 'http', 'network'])), thread.stack_trace[0] if thread.stack_trace else 'Unknown')
                root_causes.append(f"Network I/O in {thread.name}: {method[:80]}")
            
            elif any(keyword in stack_str.lower() for keyword in ['file', 'stream', 'reader', 'writer']):
                operations['file_io'].append(thread.name)
                method = next((line for line in thread.stack_trace if any(k in line.lower() for k in ['file', 'stream'])), thread.stack_trace[0] if thread.stack_trace else 'Unknown')
                root_causes.append(f"File I/O in {thread.name}: {method[:80]}")
            
            elif any(keyword in stack_str.lower() for keyword in ['lock', 'synchronized', 'wait', 'park']):
                operations['lock_wait'].append(thread.name)
                method = next((line for line in thread.stack_trace if any(k in line.lower() for k in ['lock', 'wait', 'park'])), thread.stack_trace[0] if thread.stack_trace else 'Unknown')
                root_causes.append(f"Lock contention in {thread.name}: {method[:80]}")
            
            else:
                operations['computation'].append(thread.name)
                if thread.stack_trace:
                    root_causes.append(f"CPU-intensive operation in {thread.name}: {thread.stack_trace[0][:80]}")
        
        # Build summary
        summary_parts = []
        if operations['database']:
            summary_parts.append(f"{len(operations['database'])} thread(s) blocked on database operations")
        if operations['network']:
            summary_parts.append(f"{len(operations['network'])} thread(s) waiting on network I/O")
        if operations['file_io']:
            summary_parts.append(f"{len(operations['file_io'])} thread(s) performing file I/O")
        if operations['lock_wait']:
            summary_parts.append(f"{len(operations['lock_wait'])} thread(s) waiting on locks")
        if operations['computation']:
            summary_parts.append(f"{len(operations['computation'])} thread(s) in CPU-intensive operations")
        
        if summary_parts:
            return "; ".join(summary_parts) + ". " + (root_causes[0] if root_causes else "")
        
        return "Threads consuming excessive CPU time. " + (root_causes[0] if root_causes else "Review application logic.")
    
    
    if hung_threads:
        print(f"\n🚨 Hung Threads Detected:")
        for thread in hung_threads[:5]:
            print(f"   - {thread.name} (CPU: {thread.cpu_time}s, State: {thread.state})")
    
    if long_running_threads:
        print(f"\n⚠️  Long-Running Threads:")
        for thread in long_running_threads[:5]:
            print(f"   - {thread.name} (CPU: {thread.cpu_time}s, State: {thread.state})")
    
    # Run AI analysis
    print(f"\n🤖 Running AI Analysis with LangGraph Analyzer...")
    print("=" * 70)
    
    try:
        analyzer = ThreadDumpAnalyzerAgent()
        analysis_result = analyzer.analyze(threads)
        
        print(f"\n📋 Analysis Results:")
        print(f"   Severity: {analysis_result.severity}")
        print(f"   Hung Threads: {analysis_result.hung_threads}")
        print(f"   Blocked Threads: {analysis_result.blocked_threads}")
        print(f"   Deadlocks: {len(analysis_result.deadlocks)}")
        
        if analysis_result.recommendations:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(analysis_result.recommendations, 1):
                print(f"   {i}. {rec}")
        
        if analysis_result.summary:
            print(f"\n📝 Summary:")
            print(f"   {analysis_result.summary}")
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_dir = Path("data/analysis_results")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        result_file = results_dir / f"analysis_{timestamp}.json"
        
        result_dict = {
            'timestamp': timestamp,
            'source_file': str(latest_dump),
            'severity': str(analysis_result.severity) if hasattr(analysis_result.severity, 'value') else analysis_result.severity,
            'total_threads': analysis_result.total_threads,
            'hung_threads': analysis_result.hung_threads,
            'long_running_threads': getattr(analysis_result, 'long_running_threads', 0),
            'blocked_threads': analysis_result.blocked_threads,
            'deadlocks': len(analysis_result.deadlocks),
            'recommendations': analysis_result.recommendations,
            'summary': analysis_result.summary
        }
        
        with open(result_file, 'w') as f:
            json.dump(result_dict, f, indent=2)
        
        print(f"\n✅ Analysis saved to: {result_file}")
        
        # Send to Slack if there are issues
        if hung_threads or long_running_threads or blocked_threads:
            print(f"\n📤 Sending alerts to Slack...")
            try:
                notifier = SlackNotifier()
                
                # Determine issue type and severity
                if hung_threads:
                    issue_type = IssueType.HUNG_THREAD
                    severity = AlertSeverity.CRITICAL
                    description = f"Detected {len(hung_threads)} hung thread(s) with CPU time > 60s"
                elif long_running_threads:
                    issue_type = IssueType.PERFORMANCE
                    severity = AlertSeverity.MEDIUM
                    description = f"Detected {len(long_running_threads)} long-running thread(s) with CPU time 30-60s"
                else:
                    issue_type = IssueType.BLOCKED_THREAD
                    severity = AlertSeverity.HIGH
                    description = f"Detected {len(blocked_threads)} blocked thread(s)"
                
                # Analyze root cause
                if hung_threads:
                    root_cause = analyze_root_cause(hung_threads, "hung")
                elif long_running_threads:
                    root_cause = analyze_root_cause(long_running_threads, "long_running")
                else:
                    root_cause = analyze_root_cause(blocked_threads, "blocked")
                
                print(f"\n🔍 Root Cause Analysis:")
                print(f"   {root_cause}")
                
                # Generate AI-powered recommendations
                threads_for_ai = []
                for t in (hung_threads + long_running_threads + blocked_threads)[:3]:
                    threads_for_ai.append({
                        'name': t.name,
                        'state': t.state,
                        'cpu_time': t.cpu_time,
                        'stack_trace': t.stack_trace[:5] if t.stack_trace else []
                    })
                
                ai_recommendations = generate_ai_recommendations(
                    threads_for_ai,
                    root_cause,
                    "hung" if hung_threads else ("long_running" if long_running_threads else "blocked")
                )
                
                # Combine AI recommendations with analyzer recommendations
                all_recommendations = ai_recommendations + (analysis_result.recommendations[:2] if analysis_result.recommendations else [])
                
                print(f"\n💡 AI-Powered Recommendations:")
                for i, rec in enumerate(ai_recommendations, 1):
                    print(f"   {i}. {rec}")
                
                # Create alert message
                from shared.config import config
                alert = AlertMessage(
                    severity=severity,
                    title=f"Thread Dump Analysis Alert - {severity}",
                    timestamp=datetime.now(),
                    server_url=config.WEBMETHODS_URL,
                    description=description,
                    issue_type=issue_type,
                    recommendations=all_recommendations[:5],
                    metadata={
                        'source_file': str(latest_dump),
                        'pid': pid if pid else 'N/A',
                        'server_url': config.WEBMETHODS_URL,
                        # Use IS stats if available and valid, otherwise use process stats
                        'cpu_usage': (
                            f"{is_stats.get('cpu_percent', 0):.1f}" if (is_stats and 'cpu_percent' in is_stats)
                            else f"{process_stats.get('cpu_percent', 0):.1f}" if process_stats
                            else 'N/A'
                        ),
                        'memory_usage': (
                            f"{is_stats.get('memory_percent', 0):.1f}" if (is_stats and is_stats.get('memory_percent', 0) > 0)
                            else f"{process_stats.get('memory_percent', 0):.1f}" if process_stats
                            else '0.0'
                        ),
                        'memory_used_mb': (
                            f"{is_stats.get('memory_used_mb', 0):.1f}" if (is_stats and is_stats.get('memory_used_mb', 0) > 0)
                            else f"{process_stats.get('memory_mb', 0):.1f}" if process_stats
                            else '0.0'
                        ),
                        'memory_max_mb': f"{is_stats.get('memory_max_mb', 0):.1f}" if is_stats else 'N/A',
                        'is_thread_count': is_stats.get('thread_count', 0) if is_stats else 0,
                        'is_active_threads': is_stats.get('active_threads', 0) if is_stats else 0,
                        'total_threads': len(threads),
                        'hung_threads': len(hung_threads),
                        'long_running_threads': len(long_running_threads),
                        'blocked_threads': len(blocked_threads),
                        'analysis_file': str(result_file),
                        'affected_threads': [t.name for t in (hung_threads + long_running_threads + blocked_threads)[:5]],
                        'root_cause': root_cause
                    }
                )
                
                # Send to Slack
                success = notifier.send_alert(alert)
                if success:
                    print(f"   ✅ Alert sent to Slack successfully")
                else:
                    print(f"   ⚠️  Failed to send alert to Slack")
                    
            except Exception as e:
                print(f"   ❌ Slack notification failed: {e}")
                if args.verbose:
                    import traceback
                    traceback.print_exc()
        else:
            print(f"\n✅ No critical issues detected - no alerts sent")
        
    except Exception as e:
        print(f"\n❌ AI Analysis failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
    
    print("=" * 70)
    print(f"\n📊 Summary:")
    print(f"   - Analysis results: {result_file if 'result_file' in locals() else 'N/A'}")
    print(f"   - Dashboard: http://localhost:8502")
    print(f"   - Alerts: data/alerts/")
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Made with Bob
