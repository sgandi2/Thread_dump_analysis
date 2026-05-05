"""
Thread Dump Analyzer Agent using LangGraph
Analyzes thread dumps and identifies patterns
Team Member: Ranadeep
"""
import json
import re
from typing import TypedDict, List, Optional, Dict, Any
from datetime import datetime
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from collections import Counter, defaultdict

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.config import config
from shared.models import ThreadInfo, AnalysisResult, AlertSeverity
from shared.utils import detect_deadlocks, calculate_thread_metrics


class AnalyzerState(TypedDict):
    """State for analyzer workflow"""
    threads: List[ThreadInfo]
    metrics: Dict[str, Any]
    patterns: List[Dict[str, Any]]
    deadlocks: List[Dict[str, Any]]
    recommendations: List[str]
    severity: AlertSeverity
    summary: str
    error: Optional[str]
    timestamp: datetime
    metadata: Dict[str, Any]


class ThreadPattern:
    """Thread pattern types"""
    HUNG_THREADS = "hung_threads"
    BLOCKED_THREADS = "blocked_threads"
    WAITING_THREADS = "waiting_threads"
    DEADLOCK = "deadlock"
    THREAD_POOL_EXHAUSTION = "thread_pool_exhaustion"
    MEMORY_LEAK = "memory_leak"
    CPU_SPIKE = "cpu_spike"
    LOCK_CONTENTION = "lock_contention"
    RECURSIVE_CALLS = "recursive_calls"
    INFINITE_LOOP = "infinite_loop"


class ThreadDumpAnalyzerAgent:
    """
    LangGraph-based agent for analyzing thread dumps
    Identifies patterns, detects issues, and provides recommendations
    """
    
    def __init__(self):
        """Initialize the analyzer agent"""
        self.config = config
        self.memory = MemorySaver()
        self.graph = self._create_graph()
    
    def _create_graph(self) -> StateGraph:
        """Create LangGraph workflow for analysis"""
        workflow = StateGraph(AnalyzerState)
        
        # Add nodes
        workflow.add_node("calculate_metrics", self.calculate_metrics)
        workflow.add_node("detect_deadlocks", self.detect_deadlocks_node)
        workflow.add_node("identify_patterns", self.identify_patterns)
        workflow.add_node("analyze_stack_traces", self.analyze_stack_traces)
        workflow.add_node("determine_severity", self.determine_severity)
        workflow.add_node("generate_recommendations", self.generate_recommendations)
        workflow.add_node("create_summary", self.create_summary)
        workflow.add_node("handle_error", self.handle_error)
        
        # Define workflow
        workflow.set_entry_point("calculate_metrics")
        
        # Metrics -> Deadlocks
        workflow.add_conditional_edges(
            "calculate_metrics",
            self._check_metrics_status,
            {
                "success": "detect_deadlocks",
                "error": "handle_error"
            }
        )
        
        # Deadlocks -> Patterns
        workflow.add_edge("detect_deadlocks", "identify_patterns")
        
        # Patterns -> Stack Traces
        workflow.add_edge("identify_patterns", "analyze_stack_traces")
        
        # Stack Traces -> Severity
        workflow.add_edge("analyze_stack_traces", "determine_severity")
        
        # Severity -> Recommendations
        workflow.add_edge("determine_severity", "generate_recommendations")
        
        # Recommendations -> Summary
        workflow.add_edge("generate_recommendations", "create_summary")
        
        # Summary -> End
        workflow.add_edge("create_summary", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    def calculate_metrics(self, state: AnalyzerState) -> AnalyzerState:
        """
        Calculate basic metrics from threads
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with metrics
        """
        print("[1/7] Calculating thread metrics...")
        
        try:
            threads = state["threads"]
            metrics = calculate_thread_metrics(threads)
            
            # Add additional metrics
            metrics["hung_percentage"] = (metrics["hung_threads"] / metrics["total_threads"] * 100) if metrics["total_threads"] > 0 else 0
            metrics["blocked_percentage"] = (metrics["blocked"] / metrics["total_threads"] * 100) if metrics["total_threads"] > 0 else 0
            
            state["metrics"] = metrics
            state["metadata"]["metrics_calculated"] = True
            
            print(f"+ Metrics calculated:")
            print(f"   Total threads: {metrics['total_threads']}")
            print(f"   Hung: {metrics['hung_threads']} ({metrics['hung_percentage']:.1f}%)")
            print(f"   Blocked: {metrics['blocked']} ({metrics['blocked_percentage']:.1f}%)")
            
        except Exception as e:
            state["error"] = f"Metrics calculation error: {str(e)}"
            state["metadata"]["metrics_calculated"] = False
        
        return state
    
    def detect_deadlocks_node(self, state: AnalyzerState) -> AnalyzerState:
        """
        Detect deadlocks in thread dump
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with deadlock information
        """
        print("[2/7] Detecting deadlocks...")
        
        try:
            threads = state["threads"]
            deadlocks = detect_deadlocks(threads)
            
            state["deadlocks"] = deadlocks
            state["metadata"]["deadlock_count"] = len(deadlocks)
            
            if deadlocks:
                print(f"! Found {len(deadlocks)} deadlock(s)")
                for i, dl in enumerate(deadlocks, 1):
                    print(f"   {i}. Lock: {dl['lock']}, Owner: {dl['owner']['name']}")
            else:
                print("+ No deadlocks detected")
            
        except Exception as e:
            state["error"] = f"Deadlock detection error: {str(e)}"
        
        return state
    
    def identify_patterns(self, state: AnalyzerState) -> AnalyzerState:
        """
        Identify thread patterns
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with identified patterns
        """
        print("[3/7] Identifying thread patterns...")
        
        try:
            threads = state["threads"]
            metrics = state["metrics"]
            patterns = []
            
            # Pattern 1: Hung Threads
            if metrics["hung_threads"] > 0:
                hung_threads = [t for t in threads if t.is_hung()]
                patterns.append({
                    "type": ThreadPattern.HUNG_THREADS,
                    "count": len(hung_threads),
                    "severity": "high" if len(hung_threads) > 5 else "medium",
                    "description": f"{len(hung_threads)} thread(s) hung for over {self.config.HUNG_THREAD_THRESHOLD}s",
                    "threads": [t.name for t in hung_threads[:5]]  # Top 5
                })
            
            # Pattern 2: Long-Running Threads (30-60s)
            long_running_threads = [t for t in threads if 30 < t.cpu_time <= 60]
            if long_running_threads:
                patterns.append({
                    "type": "LONG_RUNNING_THREADS",
                    "count": len(long_running_threads),
                    "severity": "medium",
                    "description": f"{len(long_running_threads)} thread(s) running 30-60s",
                    "threads": [t.name for t in long_running_threads[:5]]
                })
            
            # Pattern 3: Blocked Threads
            if metrics["blocked"] > 10:
                blocked_threads = [t for t in threads if t.is_blocked()]
                patterns.append({
                    "type": ThreadPattern.BLOCKED_THREADS,
                    "count": len(blocked_threads),
                    "severity": "medium",
                    "description": f"{len(blocked_threads)} thread(s) blocked",
                    "threads": [t.name for t in blocked_threads[:5]]
                })
            
            # Pattern 4: Deadlock
            if state["deadlocks"]:
                patterns.append({
                    "type": ThreadPattern.DEADLOCK,
                    "count": len(state["deadlocks"]),
                    "severity": "critical",
                    "description": f"{len(state['deadlocks'])} deadlock(s) detected",
                    "details": state["deadlocks"]
                })
            
            # Pattern 5: Thread Pool Exhaustion
            if metrics["total_threads"] > 150:  # Threshold
                patterns.append({
                    "type": ThreadPattern.THREAD_POOL_EXHAUSTION,
                    "count": metrics["total_threads"],
                    "severity": "high",
                    "description": f"Thread pool near capacity ({metrics['total_threads']} threads)",
                    "recommendation": "Consider increasing thread pool size"
                })
            
            # Pattern 6: Lock Contention
            lock_counts = Counter()
            for thread in threads:
                if thread.lock_name:
                    lock_counts[thread.lock_name] += 1
            
            contended_locks = [(lock, count) for lock, count in lock_counts.items() if count > 5]
            if contended_locks:
                patterns.append({
                    "type": ThreadPattern.LOCK_CONTENTION,
                    "count": len(contended_locks),
                    "severity": "medium",
                    "description": f"{len(contended_locks)} lock(s) with high contention",
                    "locks": [{"lock": lock, "waiters": count} for lock, count in contended_locks[:5]]
                })
            
            # Pattern 7: Waiting Threads
            waiting_count = metrics["waiting"] + metrics["timed_waiting"]
            if waiting_count > metrics["total_threads"] * 0.5:  # >50% waiting
                patterns.append({
                    "type": ThreadPattern.WAITING_THREADS,
                    "count": waiting_count,
                    "severity": "medium",
                    "description": f"{waiting_count} thread(s) waiting ({waiting_count/metrics['total_threads']*100:.1f}%)",
                    "recommendation": "Investigate what threads are waiting for"
                })
            
            state["patterns"] = patterns
            state["metadata"]["pattern_count"] = len(patterns)
            
            print(f"+ Identified {len(patterns)} pattern(s):")
            for pattern in patterns:
                print(f"   - {pattern['type']}: {pattern['description']}")
            
        except Exception as e:
            state["error"] = f"Pattern identification error: {str(e)}"
        
        return state
    
    def analyze_stack_traces(self, state: AnalyzerState) -> AnalyzerState:
        """
        Analyze stack traces for common issues
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with stack trace analysis
        """
        print("[4/7] Analyzing stack traces...")
        
        try:
            threads = state["threads"]
            patterns = state["patterns"]
            
            # Analyze stack traces
            stack_patterns = defaultdict(list)
            
            for thread in threads:
                if not thread.stack_trace:
                    continue
                
                # Check for common patterns in stack traces
                stack_str = "\n".join(thread.stack_trace)
                
                # Pattern: Infinite loop (same method repeated)
                if len(thread.stack_trace) > 10:
                    method_counts = Counter(thread.stack_trace)
                    for method, count in method_counts.items():
                        if count > 5:
                            stack_patterns[ThreadPattern.INFINITE_LOOP].append({
                                "thread": thread.name,
                                "method": method,
                                "count": count
                            })
                
                # Pattern: Recursive calls
                if len(thread.stack_trace) > 20:
                    # Check for repeated method names
                    methods = [line.split("(")[0].strip() if "(" in line else line for line in thread.stack_trace]
                    if len(set(methods)) < len(methods) * 0.3:  # <30% unique methods
                        stack_patterns[ThreadPattern.RECURSIVE_CALLS].append({
                            "thread": thread.name,
                            "depth": len(thread.stack_trace)
                        })
                
                # Pattern: Database operations
                if any("jdbc" in line.lower() or "sql" in line.lower() for line in thread.stack_trace):
                    stack_patterns["database_operations"].append(thread.name)
                
                # Pattern: Network I/O
                if any("socket" in line.lower() or "http" in line.lower() for line in thread.stack_trace):
                    stack_patterns["network_io"].append(thread.name)
            
            # Add stack patterns to main patterns
            if stack_patterns[ThreadPattern.INFINITE_LOOP]:
                patterns.append({
                    "type": ThreadPattern.INFINITE_LOOP,
                    "count": len(stack_patterns[ThreadPattern.INFINITE_LOOP]),
                    "severity": "high",
                    "description": f"{len(stack_patterns[ThreadPattern.INFINITE_LOOP])} thread(s) in potential infinite loop",
                    "threads": [p["thread"] for p in stack_patterns[ThreadPattern.INFINITE_LOOP][:5]]
                })
            
            if stack_patterns[ThreadPattern.RECURSIVE_CALLS]:
                patterns.append({
                    "type": ThreadPattern.RECURSIVE_CALLS,
                    "count": len(stack_patterns[ThreadPattern.RECURSIVE_CALLS]),
                    "severity": "medium",
                    "description": f"{len(stack_patterns[ThreadPattern.RECURSIVE_CALLS])} thread(s) with deep recursion",
                    "threads": [p["thread"] for p in stack_patterns[ThreadPattern.RECURSIVE_CALLS][:5]]
                })
            
            state["patterns"] = patterns
            state["metadata"]["stack_analysis_complete"] = True
            
            print(f"+ Stack trace analysis complete")
            if stack_patterns:
                print(f"   Found {len(stack_patterns)} stack trace pattern(s)")
            
        except Exception as e:
            state["error"] = f"Stack trace analysis error: {str(e)}"
        
        return state
    
    def determine_severity(self, state: AnalyzerState) -> AnalyzerState:
        """
        Determine overall severity
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with severity
        """
        print("[5/7] Determining severity...")
        
        try:
            patterns = state["patterns"]
            metrics = state["metrics"]
            
            # Calculate severity based on patterns
            severity_scores = {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }
            
            for pattern in patterns:
                severity_scores[pattern["severity"]] += 1
            
            # Determine overall severity
            if severity_scores["critical"] > 0 or state["deadlocks"]:
                severity = AlertSeverity.CRITICAL
            elif severity_scores["high"] > 0 or metrics["hung_threads"] > 5:
                severity = AlertSeverity.HIGH
            elif severity_scores["medium"] > 0 or metrics["blocked"] > 10:
                severity = AlertSeverity.MEDIUM
            elif metrics["hung_threads"] > 0 or metrics["blocked"] > 0:
                severity = AlertSeverity.LOW
            else:
                severity = AlertSeverity.INFO
            
            state["severity"] = severity
            state["metadata"]["severity"] = severity.value
            
            print(f"+ Severity determined: {severity.value.upper()}")
            
        except Exception as e:
            state["error"] = f"Severity determination error: {str(e)}"
            state["severity"] = AlertSeverity.INFO
        
        return state
    
    def generate_recommendations(self, state: AnalyzerState) -> AnalyzerState:
        """
        Generate recommendations based on analysis
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with recommendations
        """
        print("[6/7] Generating recommendations...")
        
        try:
            patterns = state["patterns"]
            metrics = state["metrics"]
            recommendations = []
            
            # Recommendations based on patterns
            for pattern in patterns:
                if pattern["type"] == ThreadPattern.HUNG_THREADS:
                    recommendations.append(
                        f"Kill or cancel {pattern['count']} hung thread(s): {', '.join(pattern['threads'][:3])}"
                    )
                
                elif pattern["type"] == ThreadPattern.DEADLOCK:
                    recommendations.append(
                        "CRITICAL: Restart server to resolve deadlock"
                    )
                
                elif pattern["type"] == ThreadPattern.THREAD_POOL_EXHAUSTION:
                    recommendations.append(
                        f"Increase thread pool size (current: {metrics['total_threads']} threads)"
                    )
                
                elif pattern["type"] == ThreadPattern.LOCK_CONTENTION:
                    recommendations.append(
                        "Review locking strategy to reduce contention"
                    )
                
                elif pattern["type"] == ThreadPattern.INFINITE_LOOP:
                    recommendations.append(
                        f"Investigate infinite loop in: {', '.join(pattern['threads'][:3])}"
                    )
                
                elif pattern["type"] == ThreadPattern.RECURSIVE_CALLS:
                    recommendations.append(
                        "Review recursive calls for potential stack overflow"
                    )
            
            # General recommendations
            if metrics["hung_percentage"] > 10:
                recommendations.append(
                    "High percentage of hung threads - investigate application logic"
                )
            
            if metrics["blocked_percentage"] > 20:
                recommendations.append(
                    "High percentage of blocked threads - review synchronization"
                )
            
            if not recommendations:
                recommendations.append("No immediate action required - continue monitoring")
            
            state["recommendations"] = recommendations
            state["metadata"]["recommendation_count"] = len(recommendations)
            
            print(f"+ Generated {len(recommendations)} recommendation(s)")
            
        except Exception as e:
            state["error"] = f"Recommendation generation error: {str(e)}"
        
        return state
    
    def create_summary(self, state: AnalyzerState) -> AnalyzerState:
        """
        Create analysis summary
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with summary
        """
        print("[7/7] Creating analysis summary...")
        
        try:
            metrics = state["metrics"]
            patterns = state["patterns"]
            severity = state["severity"]
            
            summary_parts = [
                f"Thread Dump Analysis - Severity: {severity.value.upper()}",
                f"Total Threads: {metrics['total_threads']}",
                f"Hung: {metrics['hung_threads']}, Blocked: {metrics['blocked']}, Waiting: {metrics['waiting']}"
            ]
            
            if state["deadlocks"]:
                summary_parts.append(f"! DEADLOCK DETECTED: {len(state['deadlocks'])} deadlock(s)")
            
            if patterns:
                summary_parts.append(f"Patterns: {', '.join([p['type'] for p in patterns])}")
            
            state["summary"] = " | ".join(summary_parts)
            state["metadata"]["analysis_complete"] = True
            
            print(f"+ Summary created")
            
        except Exception as e:
            state["error"] = f"Summary creation error: {str(e)}"
        
        return state
    
    def handle_error(self, state: AnalyzerState) -> AnalyzerState:
        """Handle errors in the workflow"""
        print(f"\nX Error occurred: {state['error']}")
        state["metadata"]["final_status"] = "failed"
        return state
    
    # Conditional edge functions
    
    def _check_metrics_status(self, state: AnalyzerState) -> str:
        """Check metrics calculation status"""
        return "success" if state["metadata"].get("metrics_calculated") else "error"
    
    def analyze(self, threads: List[ThreadInfo]) -> AnalysisResult:
        """
        Analyze thread dump
        
        Args:
            threads: List of ThreadInfo objects
        
        Returns:
            AnalysisResult object
        """
        print("=" * 70)
        print("Thread Dump Analysis Workflow - LangGraph Agent")
        print("=" * 70)
        
        # Initialize state
        initial_state: AnalyzerState = {
            "threads": threads,
            "metrics": {},
            "patterns": [],
            "deadlocks": [],
            "recommendations": [],
            "severity": AlertSeverity.INFO,
            "summary": "",
            "error": None,
            "timestamp": datetime.now(),
            "metadata": {
                "workflow_start": datetime.now().isoformat(),
                "thread_count": len(threads)
            }
        }
        
        # Execute workflow
        try:
            # Add thread_id for checkpointer
            config = {"configurable": {"thread_id": "analyzer_1"}}
            result = self.graph.invoke(initial_state, config)
            
            # Print summary
            print("\n" + "=" * 70)
            if result.get("error"):
                print("X Analysis Failed")
                print(f"Error: {result['error']}")
            else:
                print("+ Analysis Complete")
                print(f"Severity: {result['severity'].value.upper()}")
                print(f"Patterns: {len(result['patterns'])}")
                print(f"Recommendations: {len(result['recommendations'])}")
                print(f"\nSummary: {result['summary']}")
            print("=" * 70)
            
            # Create AnalysisResult
            if not result.get("error"):
                # Count long-running threads from patterns
                long_running_count = 0
                for pattern in result["patterns"]:
                    if pattern.get("type") == "LONG_RUNNING_THREADS":
                        long_running_count = pattern.get("count", 0)
                        break
                
                return AnalysisResult(
                    timestamp=result["timestamp"],
                    server_url=self.config.WEBMETHODS_URL,
                    total_threads=result["metrics"]["total_threads"],
                    hung_threads=result["metrics"]["hung_threads"],
                    blocked_threads=result["metrics"]["blocked"],
                    long_running_threads=long_running_count,
                    deadlocks=result["deadlocks"],
                    recommendations=result["recommendations"],
                    severity=result["severity"],
                    summary=result["summary"],
                    details={
                        "patterns": result["patterns"],
                        "metrics": result["metrics"],
                        "metadata": result["metadata"]
                    }
                )
            else:
                raise Exception(result["error"])
        
        except Exception as e:
            print(f"\nX Workflow execution failed: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Return error result
            return AnalysisResult(
                timestamp=datetime.now(),
                server_url=self.config.WEBMETHODS_URL,
                total_threads=len(threads),
                hung_threads=0,
                blocked_threads=0,
                long_running_threads=0,
                deadlocks=[],
                recommendations=["Analysis failed - manual review required"],
                severity=AlertSeverity.INFO,
                summary=f"Analysis error: {str(e)}"
            )


def main():
    """Main entry point for analyzer agent"""
    print("Thread Dump Analyzer Agent - LangGraph Implementation")
    print("Team Member: Ranadeep\n")
    
    # Create sample threads for testing
    from shared.models import ThreadInfo
    
    sample_threads = [
        ThreadInfo(
            thread_id="0x1000",
            name="HTTP Handler-1",
            state="RUNNABLE",
            cpu_time=650.0,  # Hung
            stack_trace=[
                "at java.net.SocketInputStream.read(SocketInputStream.java:123)",
                "at com.wm.app.b2b.server.HTTPHandler.run(HTTPHandler.java:456)"
            ]
        ),
        ThreadInfo(
            thread_id="0x2000",
            name="Worker Thread-1",
            state="BLOCKED",
            cpu_time=100.0,
            blocked_count=15,
            lock_name="0x3000",
            stack_trace=[
                "at java.lang.Object.wait(Native Method)",
                "at com.wm.app.b2b.server.WorkerThread.run(WorkerThread.java:789)"
            ]
        ),
        ThreadInfo(
            thread_id="0x3000",
            name="Worker Thread-2",
            state="WAITING",
            cpu_time=50.0,
            waited_count=10,
            stack_trace=[
                "at java.lang.Thread.sleep(Native Method)",
                "at com.wm.app.b2b.server.WorkerThread.run(WorkerThread.java:789)"
            ]
        )
    ]
    
    # Add more normal threads
    for i in range(4, 20):
        sample_threads.append(ThreadInfo(
            thread_id=f"0x{i}000",
            name=f"Thread-{i}",
            state="RUNNABLE",
            cpu_time=10.0 + i
        ))
    
    # Create and run analyzer
    analyzer = ThreadDumpAnalyzerAgent()
    result = analyzer.analyze(sample_threads)
    
    # Print detailed results
    print("\n" + "=" * 70)
    print("Detailed Analysis Results")
    print("=" * 70)
    print(f"Severity: {result.severity.value.upper()}")
    print(f"Total Threads: {result.total_threads}")
    print(f"Hung Threads: {result.hung_threads}")
    print(f"Blocked Threads: {result.blocked_threads}")
    print(f"Deadlocks: {len(result.deadlocks)}")
    print(f"\nRecommendations:")
    for i, rec in enumerate(result.recommendations, 1):
        print(f"  {i}. {rec}")
    print("=" * 70)
    
    # Exit with appropriate code
    exit(0 if result.severity != AlertSeverity.CRITICAL else 1)


if __name__ == "__main__":
    main()

# Made with Bob
