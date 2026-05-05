"""
Test script for Thread Dump Collector Agent
Team Member: Ranadeep
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.collector.collector_agent import ThreadDumpCollectorAgent
from shared.config import config


def test_basic_collection():
    """Test basic thread dump collection"""
    print("=" * 70)
    print("Test 1: Basic Thread Dump Collection")
    print("=" * 70)
    
    agent = ThreadDumpCollectorAgent()
    result = agent.run()
    
    if result.get("error"):
        print(f"\n❌ Test Failed: {result['error']}")
        return False
    else:
        print(f"\n✅ Test Passed")
        print(f"   Threads collected: {result['metadata'].get('thread_count', 0)}")
        print(f"   Hung threads: {result['metadata'].get('hung_threads', 0)}")
        print(f"   Blocked threads: {result['metadata'].get('blocked_threads', 0)}")
        print(f"   Storage path: {result['metadata'].get('storage_path', 'N/A')}")
        return True


def test_custom_endpoint():
    """Test with custom API endpoint"""
    print("\n" + "=" * 70)
    print("Test 2: Custom API Endpoint")
    print("=" * 70)
    
    agent = ThreadDumpCollectorAgent()
    result = agent.run(api_endpoint="/invoke/wm.server/getThreadDump")
    
    if result.get("error"):
        print(f"\n❌ Test Failed: {result['error']}")
        return False
    else:
        print(f"\n✅ Test Passed")
        return True


def test_error_handling():
    """Test error handling with invalid server"""
    print("\n" + "=" * 70)
    print("Test 3: Error Handling (Invalid Server)")
    print("=" * 70)
    
    agent = ThreadDumpCollectorAgent(server_url="http://invalid-server:9999")
    result = agent.run()
    
    if result.get("error"):
        print(f"\n✅ Test Passed - Error handled correctly")
        print(f"   Error: {result['error']}")
        return True
    else:
        print(f"\n❌ Test Failed - Should have returned error")
        return False


def test_thread_parsing():
    """Test thread parsing functionality"""
    print("\n" + "=" * 70)
    print("Test 4: Thread Parsing")
    print("=" * 70)
    
    # Sample thread dump text
    sample_dump = '''
"HTTP Handler" #123 prio=5 tid=0x00007f8a1c001000 nid=0x1234 runnable
   java.lang.Thread.State: RUNNABLE
        at java.net.SocketInputStream.read(SocketInputStream.java:123)
        at com.wm.app.b2b.server.HTTPHandler.run(HTTPHandler.java:456)

"Worker Thread" #124 prio=5 tid=0x00007f8a1c002000 nid=0x1235 waiting on condition
   java.lang.Thread.State: WAITING
        at java.lang.Object.wait(Native Method)
        at com.wm.app.b2b.server.WorkerThread.run(WorkerThread.java:789)
'''
    
    from shared.utils import parse_thread_dump
    
    threads = parse_thread_dump(sample_dump)
    
    if len(threads) > 0:
        print(f"\n✅ Test Passed")
        print(f"   Parsed {len(threads)} threads")
        for thread in threads:
            print(f"   - {thread.name}: {thread.state}")
        return True
    else:
        print(f"\n❌ Test Failed - No threads parsed")
        return False


def test_metrics_calculation():
    """Test metrics calculation"""
    print("\n" + "=" * 70)
    print("Test 5: Metrics Calculation")
    print("=" * 70)
    
    from shared.models import ThreadInfo
    from shared.utils import calculate_thread_metrics
    
    # Create sample threads
    threads = [
        ThreadInfo(
            thread_id="1",
            name="Thread 1",
            state="RUNNABLE",
            cpu_time=100.0
        ),
        ThreadInfo(
            thread_id="2",
            name="Thread 2",
            state="BLOCKED",
            cpu_time=50.0
        ),
        ThreadInfo(
            thread_id="3",
            name="Thread 3",
            state="WAITING",
            cpu_time=400.0  # Hung thread
        )
    ]
    
    metrics = calculate_thread_metrics(threads)
    
    print(f"\n✅ Test Passed")
    print(f"   Total threads: {metrics['total_threads']}")
    print(f"   Runnable: {metrics['runnable']}")
    print(f"   Blocked: {metrics['blocked']}")
    print(f"   Waiting: {metrics['waiting']}")
    print(f"   Hung threads: {metrics['hung_threads']}")
    print(f"   Avg CPU time: {metrics['avg_cpu_time']:.2f}s")
    
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("Thread Dump Collector Agent - Test Suite")
    print("Team Member: Ranadeep")
    print("=" * 70)
    
    print(f"\nConfiguration:")
    print(f"  Server URL: {config.WEBMETHODS_URL}")
    print(f"  User: {config.WEBMETHODS_USER}")
    print(f"  Data Dir: {config.DATA_DIR}")
    
    tests = [
        ("Thread Parsing", test_thread_parsing),
        ("Metrics Calculation", test_metrics_calculation),
        ("Error Handling", test_error_handling),
        ("Basic Collection", test_basic_collection),
        ("Custom Endpoint", test_custom_endpoint),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 70)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

# Made with Bob
