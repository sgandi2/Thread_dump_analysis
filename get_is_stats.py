"""
Get Integration Server Statistics via REST API
Fetches memory, CPU, and thread statistics from webMethods Integration Server
"""
import requests
import json
from typing import Dict, Any, Optional
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_integration_server_stats(
    server_url: str = "https://localhost:5555",
    username: str = "Administrator", 
    password: str = "manage"
) -> Optional[Dict[str, Any]]:
    """
    Fetch Integration Server statistics via REST API
    
    Args:
        server_url: Integration Server URL
        username: Admin username
        password: Admin password
    
    Returns:
        Dictionary with server statistics or None if failed
    """
    try:
        # Prepare authentication
        auth = (username, password)
        headers = {
            'Accept': 'application/json'
        }
        
        stats = {}
        
        # 1. Get Memory Statistics
        memory_url = f"{server_url}/admin/server/memory"
        print(f"[INFO] Fetching memory stats from {memory_url}...")
        
        response = requests.get(
            memory_url,
            auth=auth,
            headers=headers,
            verify=False,  # Skip SSL verification for self-signed certs
            timeout=10
        )
        
        if response.status_code == 200:
            memory_data = response.json()
            stats['memory'] = memory_data
            
            # Extract key metrics
            if 'output' in memory_data and 'memory' in memory_data['output']:
                mem = memory_data['output']['memory']
                stats['memory_used_mb'] = float(mem.get('serverMemUsed', 0)) / (1024 * 1024)
                stats['memory_max_mb'] = float(mem.get('serverMemMax', 0)) / (1024 * 1024)
                stats['memory_free_mb'] = float(mem.get('serverMemFree', 0)) / (1024 * 1024)
                stats['memory_percent'] = (stats['memory_used_mb'] / stats['memory_max_mb'] * 100) if stats['memory_max_mb'] > 0 else 0
            
            print(f"[SUCCESS] Memory: {stats.get('memory_used_mb', 0):.1f}MB / {stats.get('memory_max_mb', 0):.1f}MB ({stats.get('memory_percent', 0):.1f}%)")
        else:
            print(f"[WARNING] Memory API returned {response.status_code}: {response.text}")
        
        # 2. Get Thread Statistics
        threads_url = f"{server_url}/admin/server/threads"
        print(f"[INFO] Fetching thread stats from {threads_url}...")
        
        response = requests.get(
            threads_url,
            auth=auth,
            headers=headers,
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            thread_data = response.json()
            stats['threads'] = thread_data
            
            # Extract thread counts
            if 'output' in thread_data and 'threads' in thread_data['output']:
                threads = thread_data['output']['threads']
                stats['thread_count'] = len(threads.get('thread', []))
                stats['active_threads'] = sum(1 for t in threads.get('thread', []) if t.get('state') == 'RUNNABLE')
            
            print(f"[SUCCESS] Threads: {stats.get('thread_count', 0)} total, {stats.get('active_threads', 0)} active")
        else:
            print(f"[WARNING] Threads API returned {response.status_code}")
        
        # 3. Get Server Statistics (includes CPU if available)
        stats_url = f"{server_url}/admin/server/stats"
        print(f"[INFO] Fetching server stats from {stats_url}...")
        
        response = requests.get(
            stats_url,
            auth=auth,
            headers=headers,
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            server_data = response.json()
            stats['server'] = server_data
            
            # Extract CPU if available
            if 'output' in server_data and 'stats' in server_data['output']:
                server_stats = server_data['output']['stats']
                # CPU usage might be in different fields depending on IS version
                stats['cpu_percent'] = float(server_stats.get('cpuUsage', 0))
            
            print(f"[SUCCESS] Server stats retrieved")
        else:
            print(f"[WARNING] Stats API returned {response.status_code}")
        
        return stats
        
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] Cannot connect to Integration Server at {server_url}")
        print("   Make sure the server is running and accessible")
        return None
    except requests.exceptions.Timeout:
        print(f"[ERROR] Connection timeout to {server_url}")
        return None
    except Exception as e:
        print(f"[ERROR] Error fetching stats: {e}")
        import traceback
        traceback.print_exc()
        return None


def format_stats_summary(stats: Dict[str, Any]) -> str:
    """Format statistics into a readable summary"""
    if not stats:
        return "No statistics available"
    
    summary = []
    summary.append("Integration Server Statistics:")
    summary.append(f"  Memory: {stats.get('memory_used_mb', 0):.1f}MB / {stats.get('memory_max_mb', 0):.1f}MB ({stats.get('memory_percent', 0):.1f}%)")
    summary.append(f"  Threads: {stats.get('thread_count', 0)} total, {stats.get('active_threads', 0)} active")
    
    if 'cpu_percent' in stats:
        summary.append(f"  CPU: {stats.get('cpu_percent', 0):.1f}%")
    
    return "\n".join(summary)


if __name__ == "__main__":
    # Test the stats fetcher
    print("Testing Integration Server Statistics Fetcher")
    print("=" * 60)
    
    stats = get_integration_server_stats()
    
    if stats:
        print("\n" + "=" * 60)
        print(format_stats_summary(stats))
        print("=" * 60)
        
        # Save to file for inspection
        with open('is_stats_sample.json', 'w') as f:
            json.dump(stats, f, indent=2)
        print("\n[SUCCESS] Full stats saved to: is_stats_sample.json")
    else:
        print("\n[ERROR] Failed to fetch statistics")

# Made with Bob
