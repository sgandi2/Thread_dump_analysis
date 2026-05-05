"""
CPU Specialist Agent - Analyzes CPU usage patterns and correlates with thread activity
Uses LangGraph for workflow orchestration and LLM for intelligent analysis
"""

from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import operator
from datetime import datetime
import json
import re


# State definition for the CPU analysis workflow
class CPUAnalysisState(TypedDict):
    """State object for CPU analysis workflow"""
    cpu_metrics: Dict[str, Any]
    thread_dump: Dict[str, Any]
    correlation_data: Dict[str, Any]
    cpu_hotspots: List[Dict[str, Any]]
    optimization_suggestions: List[Dict[str, Any]]
    analysis_summary: str
    errors: Annotated[List[str], operator.add]


class CPUSpecialistAgent:
    """
    CPU Specialist Agent that analyzes CPU usage patterns, correlates with thread activity,
    and provides optimization recommendations using LangGraph workflow
    """
    
    def __init__(self, model_name: str = "gpt-4", temperature: float = 0.1):
        """
        Initialize the CPU Specialist Agent
        
        Args:
            model_name: LLM model to use for analysis
            temperature: Temperature for LLM responses (lower = more deterministic)
        """
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        self.workflow = self._build_workflow()
        
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for CPU analysis"""
        workflow = StateGraph(CPUAnalysisState)
        
        # Add nodes
        workflow.add_node("collect_cpu_metrics", self.collect_cpu_metrics)
        workflow.add_node("correlate_with_threads", self.correlate_with_threads)
        workflow.add_node("identify_hotspots", self.identify_hotspots)
        workflow.add_node("suggest_optimizations", self.suggest_optimizations)
        
        # Define edges
        workflow.set_entry_point("collect_cpu_metrics")
        workflow.add_edge("collect_cpu_metrics", "correlate_with_threads")
        workflow.add_edge("correlate_with_threads", "identify_hotspots")
        workflow.add_edge("identify_hotspots", "suggest_optimizations")
        workflow.add_edge("suggest_optimizations", END)
        
        return workflow.compile()
    
    def collect_cpu_metrics(self, state: CPUAnalysisState) -> CPUAnalysisState:
        """
        Node 1: Collect and parse CPU metrics from webMethods Integration Server
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with parsed CPU metrics
        """
        try:
            cpu_metrics = state.get("cpu_metrics", {})
            
            if not cpu_metrics:
                state["errors"].append("No CPU metrics provided")
                return state
            
            # Parse and structure CPU metrics
            structured_metrics = self._structure_cpu_metrics(cpu_metrics)
            state["cpu_metrics"] = structured_metrics
            
            print(f"✓ Collected CPU metrics")
            print(f"  - Overall CPU: {structured_metrics.get('overall_cpu_percent', 0):.1f}%")
            print(f"  - Process CPU: {structured_metrics.get('process_cpu_percent', 0):.1f}%")
            print(f"  - Thread count: {structured_metrics.get('thread_count', 0)}")
            
        except Exception as e:
            state["errors"].append(f"Error collecting CPU metrics: {str(e)}")
            
        return state
    
    def correlate_with_threads(self, state: CPUAnalysisState) -> CPUAnalysisState:
        """
        Node 2: Correlate CPU spikes with thread activity using LLM
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with correlation analysis
        """
        try:
            cpu_metrics = state.get("cpu_metrics", {})
            thread_dump = state.get("thread_dump", {})
            
            if not cpu_metrics:
                state["errors"].append("No CPU metrics for correlation")
                return state
            
            # Prepare data for LLM analysis
            analysis_data = self._prepare_correlation_data(cpu_metrics, thread_dump)
            
            # Use LLM to correlate CPU usage with threads
            system_prompt = """You are a CPU performance analysis expert. Analyze the CPU metrics and thread dump data to identify correlations.

Focus on:
1. Which threads are consuming the most CPU
2. CPU spike patterns and their timing
3. Thread states during high CPU periods
4. Blocked or waiting threads that might indicate contention
5. Runnable threads that are CPU-intensive

Provide a structured analysis in JSON format with keys: 
- cpu_intensive_threads: List of threads with high CPU usage
- spike_patterns: Patterns in CPU spikes
- thread_states_analysis: Analysis of thread states during high CPU
- contention_indicators: Signs of resource contention
- timing_correlation: How CPU usage correlates with thread activity"""
            
            human_prompt = f"""Analyze this CPU and thread data:

CPU Metrics:
{json.dumps(cpu_metrics, indent=2)}

Thread Dump Summary:
{json.dumps(self._summarize_thread_dump(thread_dump), indent=2)}

Provide detailed correlation analysis."""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            # Parse LLM response
            try:
                correlation = json.loads(response.content)
            except json.JSONDecodeError:
                correlation = {
                    "analysis": response.content,
                    "timestamp": datetime.now().isoformat()
                }
            
            state["correlation_data"] = correlation
            print(f"✓ Correlated CPU usage with thread activity")
            
        except Exception as e:
            state["errors"].append(f"Error correlating CPU with threads: {str(e)}")
            
        return state
    
    def identify_hotspots(self, state: CPUAnalysisState) -> CPUAnalysisState:
        """
        Node 3: Identify CPU hotspots and bottlenecks
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with identified CPU hotspots
        """
        try:
            correlation = state.get("correlation_data", {})
            cpu_metrics = state.get("cpu_metrics", {})
            
            if not correlation or not cpu_metrics:
                state["errors"].append("Insufficient data for hotspot identification")
                return state
            
            # Use LLM to identify hotspots
            system_prompt = """You are a CPU performance expert specializing in identifying performance bottlenecks.

Based on the correlation analysis and CPU metrics, identify:
1. CPU hotspots (specific threads or operations consuming excessive CPU)
2. Performance bottlenecks (what's limiting throughput)
3. Inefficient operations (unnecessary CPU consumption)
4. Contention points (threads competing for resources)
5. Scalability issues (CPU usage patterns that won't scale)

For each hotspot, provide:
- Hotspot type (e.g., "Busy Loop", "Inefficient Algorithm", "Lock Contention")
- Severity (Critical/High/Medium/Low)
- Thread(s) involved
- CPU impact (percentage of total CPU)
- Root cause analysis
- Performance impact description

Return as JSON array of hotspots."""
            
            human_prompt = f"""Correlation Analysis:
{json.dumps(correlation, indent=2)}

CPU Metrics:
{json.dumps(cpu_metrics, indent=2)}

Identify all CPU hotspots and bottlenecks."""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            # Parse hotspots
            try:
                hotspots = json.loads(response.content)
                if not isinstance(hotspots, list):
                    hotspots = [hotspots]
            except json.JSONDecodeError:
                hotspots = [{
                    "type": "Analysis Result",
                    "severity": "Info",
                    "description": response.content
                }]
            
            state["cpu_hotspots"] = hotspots
            print(f"✓ Identified {len(hotspots)} CPU hotspots")
            
        except Exception as e:
            state["errors"].append(f"Error identifying hotspots: {str(e)}")
            
        return state
    
    def suggest_optimizations(self, state: CPUAnalysisState) -> CPUAnalysisState:
        """
        Node 4: Generate optimization suggestions based on analysis
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with optimization suggestions and summary
        """
        try:
            hotspots = state.get("cpu_hotspots", [])
            correlation = state.get("correlation_data", {})
            cpu_metrics = state.get("cpu_metrics", {})
            
            # Use LLM to generate optimization suggestions
            system_prompt = """You are a performance optimization expert. Based on identified CPU hotspots and analysis, provide specific, actionable optimization recommendations.

For each recommendation, provide:
1. Optimization type (e.g., "Algorithm Optimization", "Caching", "Parallelization")
2. Target (specific thread, service, or component)
3. Current issue description
4. Recommended solution with implementation details
5. Expected CPU reduction (percentage)
6. Implementation complexity (Low/Medium/High)
7. Priority (Critical/High/Medium/Low)
8. Potential risks or side effects
9. Code-level suggestions if applicable

Also provide:
- Thread pool tuning recommendations
- JVM optimization flags for CPU performance
- Architecture-level improvements
- Monitoring recommendations

Return as JSON with keys: optimizations, thread_pool_tuning, jvm_flags, architecture_improvements, monitoring, summary."""
            
            human_prompt = f"""CPU Hotspots:
{json.dumps(hotspots, indent=2)}

Correlation Analysis:
{json.dumps(correlation, indent=2)}

CPU Metrics:
{json.dumps(cpu_metrics, indent=2)}

Provide comprehensive optimization recommendations."""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            # Parse suggestions
            try:
                suggestions = json.loads(response.content)
                if not isinstance(suggestions, dict):
                    suggestions = {"recommendations": response.content}
            except json.JSONDecodeError:
                suggestions = {"recommendations": response.content}
            
            state["optimization_suggestions"] = suggestions
            
            # Generate analysis summary
            summary = self._generate_summary(state)
            state["analysis_summary"] = summary
            
            print(f"✓ Generated optimization suggestions")
            print(f"✓ CPU analysis complete")
            
        except Exception as e:
            state["errors"].append(f"Error generating suggestions: {str(e)}")
            
        return state
    
    def _structure_cpu_metrics(self, raw_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Structure raw CPU metrics into standardized format"""
        structured = {
            "overall_cpu_percent": raw_metrics.get("overall_cpu", 0),
            "process_cpu_percent": raw_metrics.get("process_cpu", 0),
            "system_cpu_percent": raw_metrics.get("system_cpu", 0),
            "user_cpu_percent": raw_metrics.get("user_cpu", 0),
            "thread_count": raw_metrics.get("thread_count", 0),
            "runnable_threads": raw_metrics.get("runnable_threads", 0),
            "blocked_threads": raw_metrics.get("blocked_threads", 0),
            "waiting_threads": raw_metrics.get("waiting_threads", 0),
            "cpu_cores": raw_metrics.get("cpu_cores", 1),
            "load_average": raw_metrics.get("load_average", []),
            "timestamp": raw_metrics.get("timestamp", datetime.now().isoformat()),
            "cpu_history": raw_metrics.get("cpu_history", [])
        }
        
        # Calculate derived metrics
        if structured["cpu_cores"] > 0:
            structured["cpu_per_core"] = structured["overall_cpu_percent"] / structured["cpu_cores"]
        
        if structured["thread_count"] > 0:
            structured["runnable_ratio"] = structured["runnable_threads"] / structured["thread_count"]
            structured["blocked_ratio"] = structured["blocked_threads"] / structured["thread_count"]
        
        return structured
    
    def _prepare_correlation_data(self, cpu_metrics: Dict[str, Any], 
                                  thread_dump: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for correlation analysis"""
        return {
            "cpu_snapshot": {
                "overall_cpu": cpu_metrics.get("overall_cpu_percent", 0),
                "process_cpu": cpu_metrics.get("process_cpu_percent", 0),
                "runnable_threads": cpu_metrics.get("runnable_threads", 0)
            },
            "thread_snapshot": self._summarize_thread_dump(thread_dump),
            "timing": cpu_metrics.get("timestamp", datetime.now().isoformat())
        }
    
    def _summarize_thread_dump(self, thread_dump: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of thread dump for analysis"""
        if not thread_dump:
            return {"threads": [], "total_threads": 0}
        
        threads = thread_dump.get("threads", [])
        
        summary = {
            "total_threads": len(threads),
            "thread_states": {},
            "top_cpu_threads": [],
            "blocked_threads": [],
            "waiting_threads": []
        }
        
        # Count thread states
        for thread in threads:
            state = thread.get("state", "UNKNOWN")
            summary["thread_states"][state] = summary["thread_states"].get(state, 0) + 1
            
            # Collect threads by state
            if state == "BLOCKED":
                summary["blocked_threads"].append({
                    "name": thread.get("name", "Unknown"),
                    "id": thread.get("id", 0)
                })
            elif state in ["WAITING", "TIMED_WAITING"]:
                summary["waiting_threads"].append({
                    "name": thread.get("name", "Unknown"),
                    "id": thread.get("id", 0)
                })
            elif state == "RUNNABLE":
                cpu_time = thread.get("cpu_time", 0)
                if cpu_time > 0:
                    summary["top_cpu_threads"].append({
                        "name": thread.get("name", "Unknown"),
                        "id": thread.get("id", 0),
                        "cpu_time": cpu_time
                    })
        
        # Sort top CPU threads
        summary["top_cpu_threads"].sort(key=lambda x: x["cpu_time"], reverse=True)
        summary["top_cpu_threads"] = summary["top_cpu_threads"][:10]  # Top 10
        
        return summary
    
    def _generate_summary(self, state: CPUAnalysisState) -> str:
        """Generate a human-readable summary of the analysis"""
        hotspots = state.get("cpu_hotspots", [])
        suggestions = state.get("optimization_suggestions", {})
        cpu_metrics = state.get("cpu_metrics", {})
        
        summary = f"""
=== CPU Analysis Summary ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

CPU Metrics:
- Overall CPU: {cpu_metrics.get('overall_cpu_percent', 0):.1f}%
- Process CPU: {cpu_metrics.get('process_cpu_percent', 0):.1f}%
- Thread Count: {cpu_metrics.get('thread_count', 0)}
- Runnable Threads: {cpu_metrics.get('runnable_threads', 0)}

Hotspots Identified: {len(hotspots)}
"""
        
        for i, hotspot in enumerate(hotspots, 1):
            summary += f"\n{i}. [{hotspot.get('severity', 'Unknown')}] {hotspot.get('type', 'Hotspot')}"
        
        opt_count = len(suggestions.get('optimizations', [])) if isinstance(suggestions.get('optimizations'), list) else 1
        summary += f"\n\nOptimization Recommendations: {opt_count}"
        
        if state.get("errors"):
            summary += f"\n\nErrors: {len(state['errors'])}"
        
        return summary
    
    def analyze(self, cpu_metrics: Dict[str, Any], 
                thread_dump: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main entry point to analyze CPU metrics
        
        Args:
            cpu_metrics: CPU metrics data
            thread_dump: Optional thread dump data for correlation
            
        Returns:
            Complete analysis results including hotspots and optimization suggestions
        """
        initial_state = CPUAnalysisState(
            cpu_metrics=cpu_metrics,
            thread_dump=thread_dump or {},
            correlation_data={},
            cpu_hotspots=[],
            optimization_suggestions=[],
            analysis_summary="",
            errors=[]
        )
        
        print("Starting CPU analysis workflow...")
        final_state = self.workflow.invoke(initial_state)
        
        return {
            "cpu_metrics": final_state.get("cpu_metrics", {}),
            "correlation": final_state.get("correlation_data", {}),
            "hotspots": final_state.get("cpu_hotspots", []),
            "optimizations": final_state.get("optimization_suggestions", {}),
            "summary": final_state.get("analysis_summary", ""),
            "errors": final_state.get("errors", [])
        }


# Example usage
if __name__ == "__main__":
    # Sample CPU metrics for testing
    sample_cpu_metrics = {
        "overall_cpu": 85.5,
        "process_cpu": 78.2,
        "system_cpu": 15.3,
        "user_cpu": 70.2,
        "thread_count": 150,
        "runnable_threads": 45,
        "blocked_threads": 12,
        "waiting_threads": 93,
        "cpu_cores": 8,
        "load_average": [6.5, 5.8, 5.2],
        "timestamp": datetime.now().isoformat(),
        "cpu_history": [
            {"time": "10:00", "cpu": 45.2},
            {"time": "10:05", "cpu": 67.8},
            {"time": "10:10", "cpu": 85.5}
        ]
    }
    
    sample_thread_dump = {
        "threads": [
            {"id": 1, "name": "http-nio-8080-exec-1", "state": "RUNNABLE", "cpu_time": 5000},
            {"id": 2, "name": "http-nio-8080-exec-2", "state": "RUNNABLE", "cpu_time": 4500},
            {"id": 3, "name": "pool-1-thread-1", "state": "BLOCKED", "cpu_time": 100},
            {"id": 4, "name": "pool-1-thread-2", "state": "WAITING", "cpu_time": 50}
        ]
    }
    
    # Initialize agent
    agent = CPUSpecialistAgent()
    
    # Run analysis
    results = agent.analyze(sample_cpu_metrics, sample_thread_dump)
    
    # Print results
    print("\n" + "="*60)
    print("CPU ANALYSIS RESULTS")
    print("="*60)
    print(json.dumps(results, indent=2))

# Made with Bob
