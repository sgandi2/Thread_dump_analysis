"""
CPU Specialist Agent - Ollama Version
Uses local Ollama with Granite 4 model instead of OpenAI
No API key required!
"""

from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_community.llms import Ollama
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
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


class CPUSpecialistAgentOllama:
    """
    CPU Specialist Agent using Ollama (local LLM)
    Works with Granite 4 or any other Ollama model
    """
    
    def __init__(self, model_name: str = "granite3-dense:8b", 
                 base_url: str = "http://localhost:11434"):
        """
        Initialize the CPU Specialist Agent with Ollama
        
        Args:
            model_name: Ollama model to use (e.g., "granite3-dense:8b", "llama2", "mistral")
            base_url: Ollama server URL (default: http://localhost:11434)
        """
        self.llm = Ollama(
            model=model_name,
            base_url=base_url,
            temperature=0.1
        )
        self.workflow = self._build_workflow()
        print(f"✓ Initialized with Ollama model: {model_name}")
        
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
        """Node 1: Collect and parse CPU metrics"""
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
        """Node 2: Correlate CPU spikes with thread activity using Ollama"""
        try:
            cpu_metrics = state.get("cpu_metrics", {})
            thread_dump = state.get("thread_dump", {})
            
            if not cpu_metrics:
                state["errors"].append("No CPU metrics for correlation")
                return state
            
            # Prepare data for LLM analysis
            analysis_data = self._prepare_correlation_data(cpu_metrics, thread_dump)
            
            # Create prompt for Ollama
            prompt = f"""You are a CPU performance analysis expert. Analyze the CPU metrics and thread dump data to identify correlations.

CPU Metrics:
{json.dumps(cpu_metrics, indent=2)}

Thread Dump Summary:
{json.dumps(self._summarize_thread_dump(thread_dump), indent=2)}

Provide analysis in JSON format with these keys:
- cpu_intensive_threads: List of threads with high CPU usage
- spike_patterns: Patterns in CPU spikes
- thread_states_analysis: Analysis of thread states during high CPU
- contention_indicators: Signs of resource contention
- timing_correlation: How CPU usage correlates with thread activity

Respond with valid JSON only."""

            # Get response from Ollama
            response = self.llm.invoke(prompt)
            
            # Parse response
            try:
                # Try to extract JSON from response
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    correlation = json.loads(json_match.group())
                else:
                    correlation = {
                        "analysis": response,
                        "timestamp": datetime.now().isoformat()
                    }
            except json.JSONDecodeError:
                correlation = {
                    "analysis": response,
                    "timestamp": datetime.now().isoformat()
                }
            
            state["correlation_data"] = correlation
            print(f"✓ Correlated CPU usage with thread activity")
            
        except Exception as e:
            state["errors"].append(f"Error correlating CPU with threads: {str(e)}")
            
        return state
    
    def identify_hotspots(self, state: CPUAnalysisState) -> CPUAnalysisState:
        """Node 3: Identify CPU hotspots and bottlenecks"""
        try:
            correlation = state.get("correlation_data", {})
            cpu_metrics = state.get("cpu_metrics", {})
            
            if not correlation or not cpu_metrics:
                state["errors"].append("Insufficient data for hotspot identification")
                return state
            
            # Create prompt for Ollama
            prompt = f"""You are a CPU performance expert. Identify CPU hotspots and bottlenecks.

Correlation Analysis:
{json.dumps(correlation, indent=2)}

CPU Metrics:
{json.dumps(cpu_metrics, indent=2)}

Identify CPU hotspots and provide as JSON array with these fields for each hotspot:
- type: Hotspot type (e.g., "Busy Loop", "Inefficient Algorithm", "Lock Contention")
- severity: Critical/High/Medium/Low
- threads: List of thread names involved
- cpu_impact: Percentage of total CPU
- root_cause: Root cause analysis
- performance_impact: Description of performance impact

Respond with valid JSON array only."""

            response = self.llm.invoke(prompt)
            
            # Parse hotspots
            try:
                json_match = re.search(r'\[.*\]', response, re.DOTALL)
                if json_match:
                    hotspots = json.loads(json_match.group())
                else:
                    hotspots = [{
                        "type": "Analysis Result",
                        "severity": "Info",
                        "description": response
                    }]
            except json.JSONDecodeError:
                hotspots = [{
                    "type": "Analysis Result",
                    "severity": "Info",
                    "description": response
                }]
            
            state["cpu_hotspots"] = hotspots
            print(f"✓ Identified {len(hotspots)} CPU hotspots")
            
        except Exception as e:
            state["errors"].append(f"Error identifying hotspots: {str(e)}")
            
        return state
    
    def suggest_optimizations(self, state: CPUAnalysisState) -> CPUAnalysisState:
        """Node 4: Generate optimization suggestions"""
        try:
            hotspots = state.get("cpu_hotspots", [])
            correlation = state.get("correlation_data", {})
            cpu_metrics = state.get("cpu_metrics", {})
            
            # Create prompt for Ollama
            prompt = f"""You are a performance optimization expert. Provide specific optimization recommendations.

CPU Hotspots:
{json.dumps(hotspots, indent=2)}

CPU Metrics:
{json.dumps(cpu_metrics, indent=2)}

Provide optimization recommendations as JSON with these keys:
- optimizations: Array of optimization recommendations, each with:
  - type: Optimization type
  - target: What to optimize
  - recommended_solution: Specific solution
  - expected_cpu_reduction: Percentage
  - priority: Critical/High/Medium/Low
- thread_pool_tuning: Thread pool recommendations
- jvm_flags: Recommended JVM flags
- summary: Brief summary

Respond with valid JSON only."""

            response = self.llm.invoke(prompt)
            
            # Parse suggestions
            try:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    suggestions = json.loads(json_match.group())
                else:
                    suggestions = {"recommendations": response}
            except json.JSONDecodeError:
                suggestions = {"recommendations": response}
            
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
        summary["top_cpu_threads"] = summary["top_cpu_threads"][:10]
        
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
            Complete analysis results
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
        
        print("Starting CPU analysis workflow with Ollama...")
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
        "timestamp": datetime.now().isoformat()
    }
    
    sample_thread_dump = {
        "threads": [
            {"id": 1, "name": "http-nio-8080-exec-1", "state": "RUNNABLE", "cpu_time": 5000},
            {"id": 2, "name": "http-nio-8080-exec-2", "state": "RUNNABLE", "cpu_time": 4500},
            {"id": 3, "name": "pool-1-thread-1", "state": "BLOCKED", "cpu_time": 100},
            {"id": 4, "name": "pool-1-thread-2", "state": "WAITING", "cpu_time": 50}
        ]
    }
    
    # Initialize agent with Ollama
    print("Initializing CPU Specialist Agent with Ollama...")
    agent = CPUSpecialistAgentOllama(model_name="granite3-dense:8b")
    
    # Run analysis
    results = agent.analyze(sample_cpu_metrics, sample_thread_dump)
    
    # Print results
    print("\n" + "="*60)
    print("CPU ANALYSIS RESULTS")
    print("="*60)
    print(json.dumps(results, indent=2))

# Made with Bob
