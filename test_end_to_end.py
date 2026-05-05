"""
End-to-End Test for Thread Dump Analysis System
Tests: Collector → Analyzer → Remediation workflow
"""
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.collector.collector_agent import ThreadDumpCollectorAgent
from agents.analyzer.analyzer_agent import ThreadDumpAnalyzerAgent
from agents.remediation.remediation_agent import RemediationAgent
from shared.config import config


def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def test_end_to_end():
    """Run end-to-end test of the complete system"""
    
    print_header("Thread Dump Analysis System - End-to-End Test")
    print(f"Server: {config.WEBMETHODS_URL}")
    print(f"User: {config.WEBMETHODS_USER}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Collect Thread Dump
    print_header("STEP 1: Collecting Thread Dump")
    
    try:
        collector = ThreadDumpCollectorAgent()
        collection_result = collector.run()
        
        if collection_result.get("error"):
            print(f"X Collection failed: {collection_result['error']}")
            return False
        
        threads = collection_result["parsed_threads"]
        metadata = collection_result["metadata"]
        
        print(f"+ Collection successful")
        print(f"  Total threads: {metadata.get('thread_count', 0)}")
        print(f"  Hung threads: {metadata.get('hung_threads', 0)}")
        print(f"  Blocked threads: {metadata.get('blocked_threads', 0)}")
        print(f"  Storage: {metadata.get('storage_path', 'N/A')}")
        
    except Exception as e:
        print(f"X Collection error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 2: Analyze Thread Dump
    print_header("STEP 2: Analyzing Thread Dump")
    
    try:
        analyzer = ThreadDumpAnalyzerAgent()
        analysis_result = analyzer.analyze(threads)
        
        print(f"+ Analysis successful")
        print(f"  Severity: {analysis_result.severity.value.upper()}")
        print(f"  Total threads: {analysis_result.total_threads}")
        print(f"  Hung threads: {analysis_result.hung_threads}")
        print(f"  Blocked threads: {analysis_result.blocked_threads}")
        print(f"  Deadlocks: {len(analysis_result.deadlocks)}")
        print(f"  Patterns: {len(analysis_result.details.get('patterns', []))}")
        
        print(f"\n  Recommendations:")
        for i, rec in enumerate(analysis_result.recommendations, 1):
            print(f"    {i}. {rec}")
        
    except Exception as e:
        print(f"X Analysis error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 3: Remediation (if needed)
    print_header("STEP 3: Remediation Assessment")
    
    try:
        # Check if remediation is needed
        needs_remediation = (
            analysis_result.severity.value in ["critical", "high"] or
            analysis_result.hung_threads > 0 or
            len(analysis_result.deadlocks) > 0
        )
        
        if needs_remediation:
            print(f"! Remediation required (Severity: {analysis_result.severity.value.upper()})")
            
            # Find threads that need remediation
            hung_threads = [t for t in threads if t.is_hung()]
            
            if hung_threads:
                print(f"\n  Found {len(hung_threads)} hung thread(s) to remediate:")
                for thread in hung_threads[:3]:  # Show first 3
                    print(f"    - {thread.name} (CPU: {thread.cpu_time:.2f}s)")
                
                # Test remediation with first hung thread
                print(f"\n  Testing remediation for: {hung_threads[0].name}")
                
                agent = RemediationAgent(auto_approve=True)
                remediation_result = agent.run(
                    thread_info=hung_threads[0],
                    analysis_result=analysis_result.to_dict()
                )
                
                if remediation_result.get("error"):
                    print(f"  X Remediation failed: {remediation_result['error']}")
                else:
                    exec_result = remediation_result.get("execution_result", {})
                    print(f"  + Remediation successful")
                    print(f"    Action: {exec_result.get('action', 'N/A')}")
                    print(f"    Status: {exec_result.get('status', 'N/A')}")
            
            elif analysis_result.deadlocks:
                print(f"\n  Deadlock detected - would recommend server restart")
                print(f"  (Skipping actual restart in test)")
            
        else:
            print(f"+ No remediation needed")
            print(f"  Severity: {analysis_result.severity.value.upper()}")
            print(f"  System is healthy")
        
    except Exception as e:
        print(f"X Remediation error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Summary
    print_header("TEST SUMMARY")
    
    print(f"+ Collection: SUCCESS")
    print(f"  - Collected {len(threads)} threads")
    print(f"  - Stored at: {metadata.get('storage_path', 'N/A')}")
    
    print(f"\n+ Analysis: SUCCESS")
    print(f"  - Severity: {analysis_result.severity.value.upper()}")
    print(f"  - Patterns identified: {len(analysis_result.details.get('patterns', []))}")
    print(f"  - Recommendations: {len(analysis_result.recommendations)}")
    
    print(f"\n+ Remediation: {'EXECUTED' if needs_remediation else 'NOT NEEDED'}")
    if needs_remediation:
        print(f"  - Action taken: {exec_result.get('action', 'N/A')}")
    
    print(f"\n+ Overall: END-TO-END TEST PASSED")
    print("=" * 70)
    
    return True


def main():
    """Main entry point"""
    try:
        success = test_end_to_end()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
