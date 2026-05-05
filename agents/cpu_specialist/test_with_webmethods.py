"""
Test CPU Specialist Agent with Local webMethods Integration Server
This script demonstrates how to collect CPU metrics and thread dumps from
your local webMethods server and analyze them with the CPU Specialist Agent.
"""

import requests
from requests.auth import HTTPBasicAuth
import json
import psutil
import time
from datetime import datetime
from cpu_agent import CPUSpecialistAgent


class WebMethodsConnector:
    """Connector to fetch data from webMethods Integration Server"""
    
    def __init__(self, server_url: str, username: str, password: str):
        """
        Initialize connector
        
        Args:
            server_url: webMethods server URL (e.g., http://localhost:5555)
            username: Admin username (default: Administrator)
            password: Admin password (default: manage)
        """
        self.server_url = server_url.rstrip('/')
        self.auth = HTTPBasicAuth(username, password)
        self.session = requests.Session()
        self.session.auth = self.auth
    
    def get_server_stats(self) -> dict:
        """
        Fetch server statistics from webMethods
        
        Returns:
            Dictionary with server stats including CPU and thread info
        """
        try:
            # Try to get stats from webMethods Admin API
            response = self.session.get(
                f"{self.server_url}/invoke/wm.server/getServerStats",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Warning: Could not fetch from webMethods API: {e}")
            print("Falling back to system metrics...")
            return self._get_system_metrics()
    
    def get_thread_dump(self) -> dict:
        """
        Fetch thread dump from webMethods
        
        Returns:
            Dictionary with thread dump data
        """
        try:
            # Try to get thread dump from webMethods
            response = self.session.get(
                f"{self.server_url}/invoke/wm.server/getThreadDump",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Warning: Could not fetch thread dump: {e}")
            print("Using simulated thread data...")
            return self._get_simulated_threads()
    
    def _get_system_metrics(self) -> dict:
        """Get system-level CPU metrics using psutil"""
        cpu_percent = psutil.cpu_percent(interval=1, percpu=False)
        cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)
        
        # Get process info for webMethods (Java process)
        java_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'num_threads']):
            try:
                if 'java' in proc.info['name'].lower():
                    java_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Use the first Java process (likely webMethods)
        process_cpu = 0
        thread_count = 0
        if java_processes:
            proc = java_processes[0]
            process_cpu = proc.cpu_percent(interval=1)
            thread_count = proc.num_threads()
        
        return {
            "overall_cpu": cpu_percent,
            "process_cpu": process_cpu,
            "system_cpu": psutil.cpu_percent(interval=0),
            "user_cpu": cpu_percent * 0.8,  # Estimate
            "thread_count": thread_count,
            "runnable_threads": int(thread_count * 0.3),  # Estimate
            "blocked_threads": int(thread_count * 0.1),  # Estimate
            "waiting_threads": int(thread_count * 0.6),  # Estimate
            "cpu_cores": psutil.cpu_count(),
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0],
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_simulated_threads(self) -> dict:
        """Generate simulated thread data for testing"""
        return {
            "threads": [
                {
                    "id": i,
                    "name": f"Thread-{i}",
                    "state": "RUNNABLE" if i % 3 == 0 else ("BLOCKED" if i % 5 == 0 else "WAITING"),
                    "cpu_time": 1000 * (10 - i % 10)
                }
                for i in range(1, 21)
            ]
        }
    
    def test_connection(self) -> bool:
        """Test connection to webMethods server"""
        try:
            response = self.session.get(
                f"{self.server_url}/",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False


def collect_cpu_history(connector: WebMethodsConnector, duration_seconds: int = 60, 
                       interval_seconds: int = 10) -> list:
    """
    Collect CPU metrics over time
    
    Args:
        connector: WebMethods connector
        duration_seconds: How long to collect data
        interval_seconds: Interval between collections
        
    Returns:
        List of CPU metric snapshots
    """
    history = []
    iterations = duration_seconds // interval_seconds
    
    print(f"Collecting CPU metrics for {duration_seconds} seconds...")
    for i in range(iterations):
        print(f"  Collection {i+1}/{iterations}...")
        stats = connector.get_server_stats()
        history.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "cpu": stats.get("overall_cpu", 0)
        })
        if i < iterations - 1:
            time.sleep(interval_seconds)
    
    return history


def main():
    """Main test function"""
    print("="*70)
    print("CPU Specialist Agent - webMethods Integration Test")
    print("="*70)
    
    # Configuration
    WEBMETHODS_URL = "http://localhost:5555"
    USERNAME = "Administrator"
    PASSWORD = "manage"
    
    print(f"\n1. Connecting to webMethods at {WEBMETHODS_URL}...")
    connector = WebMethodsConnector(WEBMETHODS_URL, USERNAME, PASSWORD)
    
    # Test connection
    if connector.test_connection():
        print("   ✓ Connected successfully!")
    else:
        print("   ⚠ Could not connect to webMethods")
        print("   → Will use system-level metrics instead")
    
    # Collect CPU metrics
    print("\n2. Collecting CPU metrics...")
    cpu_metrics = connector.get_server_stats()
    print(f"   ✓ Overall CPU: {cpu_metrics.get('overall_cpu', 0):.1f}%")
    print(f"   ✓ Process CPU: {cpu_metrics.get('process_cpu', 0):.1f}%")
    print(f"   ✓ Thread Count: {cpu_metrics.get('thread_count', 0)}")
    
    # Collect CPU history (optional - comment out if you want quick test)
    print("\n3. Collecting CPU history (30 seconds)...")
    cpu_history = collect_cpu_history(connector, duration_seconds=30, interval_seconds=5)
    cpu_metrics['cpu_history'] = cpu_history
    print(f"   ✓ Collected {len(cpu_history)} data points")
    
    # Get thread dump
    print("\n4. Fetching thread dump...")
    thread_dump = connector.get_thread_dump()
    print(f"   ✓ Found {len(thread_dump.get('threads', []))} threads")
    
    # Initialize CPU Specialist Agent
    print("\n5. Initializing CPU Specialist Agent...")
    try:
        agent = CPUSpecialistAgent(model_name="gpt-4", temperature=0.1)
        print("   ✓ Agent initialized")
    except Exception as e:
        print(f"   ✗ Failed to initialize agent: {e}")
        print("   → Make sure OPENAI_API_KEY is set in environment")
        return
    
    # Run analysis
    print("\n6. Running CPU analysis...")
    print("   (This may take 10-30 seconds...)")
    try:
        results = agent.analyze(cpu_metrics, thread_dump)
        print("   ✓ Analysis complete!")
    except Exception as e:
        print(f"   ✗ Analysis failed: {e}")
        return
    
    # Display results
    print("\n" + "="*70)
    print("ANALYSIS RESULTS")
    print("="*70)
    
    # Summary
    print("\n" + results['summary'])
    
    # CPU Metrics
    print("\n--- CPU Metrics ---")
    metrics = results['cpu_metrics']
    print(f"Overall CPU: {metrics.get('overall_cpu_percent', 0):.1f}%")
    print(f"Process CPU: {metrics.get('process_cpu_percent', 0):.1f}%")
    print(f"CPU per Core: {metrics.get('cpu_per_core', 0):.1f}%")
    print(f"Runnable Ratio: {metrics.get('runnable_ratio', 0):.2f}")
    print(f"Blocked Ratio: {metrics.get('blocked_ratio', 0):.2f}")
    
    # Correlation
    if results.get('correlation'):
        print("\n--- CPU-Thread Correlation ---")
        correlation = results['correlation']
        if 'cpu_intensive_threads' in correlation:
            print("CPU-Intensive Threads:")
            for thread in correlation['cpu_intensive_threads'][:5]:
                print(f"  - {thread.get('name', 'Unknown')}: {thread.get('cpu_percentage', 0):.1f}%")
    
    # Hotspots
    print("\n--- CPU Hotspots ---")
    hotspots = results.get('hotspots', [])
    if hotspots:
        for i, hotspot in enumerate(hotspots, 1):
            print(f"\n{i}. [{hotspot.get('severity', 'Unknown')}] {hotspot.get('type', 'Hotspot')}")
            if 'threads' in hotspot:
                print(f"   Threads: {', '.join(hotspot['threads'][:3])}")
            if 'cpu_impact' in hotspot:
                print(f"   CPU Impact: {hotspot['cpu_impact']:.1f}%")
            if 'root_cause' in hotspot:
                print(f"   Root Cause: {hotspot['root_cause']}")
    else:
        print("No critical hotspots detected")
    
    # Optimizations
    print("\n--- Optimization Recommendations ---")
    optimizations = results.get('optimizations', {})
    if isinstance(optimizations, dict):
        opt_list = optimizations.get('optimizations', [])
        if opt_list:
            for i, opt in enumerate(opt_list[:5], 1):
                print(f"\n{i}. [{opt.get('priority', 'Unknown')}] {opt.get('type', 'Optimization')}")
                if 'target' in opt:
                    print(f"   Target: {opt['target']}")
                if 'recommended_solution' in opt:
                    print(f"   Solution: {opt['recommended_solution']}")
                if 'expected_cpu_reduction' in opt:
                    print(f"   Expected CPU Reduction: {opt['expected_cpu_reduction']}%")
        
        # Thread pool tuning
        if 'thread_pool_tuning' in optimizations:
            tuning = optimizations['thread_pool_tuning']
            print(f"\nThread Pool Tuning:")
            print(f"  Current Size: {tuning.get('current_size', 'Unknown')}")
            print(f"  Recommended Size: {tuning.get('recommended_size', 'Unknown')}")
        
        # JVM flags
        if 'jvm_flags' in optimizations:
            flags = optimizations['jvm_flags']
            if flags:
                print(f"\nRecommended JVM Flags:")
                for flag in flags[:5]:
                    print(f"  - {flag}")
    
    # Errors
    if results.get('errors'):
        print("\n--- Errors ---")
        for error in results['errors']:
            print(f"  ⚠ {error}")
    
    # Save results
    print("\n" + "="*70)
    output_file = f"cpu_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to: {output_file}")
    print("="*70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()

# Made with Bob
