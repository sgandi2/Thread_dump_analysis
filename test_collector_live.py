"""Test collector agent with live Integration Server."""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from agents.collector.collector_agent import ThreadDumpCollectorAgent
from shared.config import config

def main():
    """Test collection from live Integration Server."""
    print("="*70)
    print("LIVE INTEGRATION SERVER - THREAD DUMP COLLECTION TEST")
    print("="*70)
    print(f"\nServer URL: {config.WEBMETHODS_URL}")
    print(f"Username: {config.WEBMETHODS_USER}")
    print(f"Password: {'*' * len(config.WEBMETHODS_PASSWORD)}")
    print("\n" + "="*70)
    
    # Create collector agent
    print("\nInitializing collector agent...")
    collector = ThreadDumpCollectorAgent()
    
    # Run collection
    print("\nStarting thread dump collection...\n")
    result = collector.run()
    
    # Display results
    print("\n" + "="*70)
    print("COLLECTION RESULTS")
    print("="*70)
    
    if result.get("error"):
        print(f"\n[FAILED] Error: {result['error']}")
        print("\nTroubleshooting:")
        print("1. Verify Integration Server is running on port 5555")
        print("2. Check credentials in .env file")
        print("3. Verify API endpoint is accessible")
        print(f"4. Try accessing: {config.WEBMETHODS_URL}/invoke/wm.server/ping")
        return False
    
    print(f"\n[SUCCESS] Thread dump collected!")
    print(f"\nTimestamp: {result.get('timestamp')}")
    print(f"Total threads: {len(result.get('parsed_threads', []))}")
    
    # Thread statistics
    threads = result.get('parsed_threads', [])
    if threads:
        hung_count = sum(1 for t in threads if t.is_hung())
        blocked_count = sum(1 for t in threads if t.is_blocked())
        waiting_count = sum(1 for t in threads if t.is_waiting())
        
        print(f"\nThread Statistics:")
        print(f"  - Total: {len(threads)}")
        print(f"  - Hung: {hung_count}")
        print(f"  - Blocked: {blocked_count}")
        print(f"  - Waiting: {waiting_count}")
        print(f"  - Running: {len(threads) - hung_count - blocked_count - waiting_count}")
    
    # Storage info
    metadata = result.get('metadata', {})
    storage_path = metadata.get('storage_path')
    if storage_path:
        print(f"\nStorage:")
        print(f"  - Path: {storage_path}")
        print(f"  - Size: {metadata.get('file_size', 'unknown')}")
    
    # Show sample threads
    if threads:
        print(f"\nSample Threads (first 5):")
        for i, thread in enumerate(threads[:5], 1):
            print(f"\n  {i}. {thread.name}")
            print(f"     - ID: {thread.thread_id}")
            print(f"     - State: {thread.state}")
            print(f"     - CPU Time: {thread.cpu_time:.2f}s")
            if thread.is_hung():
                print(f"     - [WARNING] HUNG THREAD!")
            if thread.is_blocked():
                print(f"     - [WARNING] BLOCKED!")
    
    print("\n" + "="*70)
    print("[SUCCESS] Collection test completed!")
    print("="*70)
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)

# Made with Bob
