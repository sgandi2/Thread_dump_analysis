"""
GC Specialist Agent - Ollama Version
Uses local Ollama with Granite 4 model instead of OpenAI
No API key required!
"""

from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_community.llms import Ollama
from langchain_core.messages import HumanMessage, SystemMessage
import operator
from datetime import datetime
import json
import re


# State definition for the GC analysis workflow
class GCAnalysisState(TypedDict):
    """State object for GC analysis workflow"""
    gc_logs: str
    raw_metrics: Dict[str, Any]
    gc_patterns: Dict[str, Any]
    memory_issues: List[Dict[str, Any]]
    tuning_recommendations: List[Dict[str, Any]]
    analysis_summary: str
    errors: Annotated[List[str], operator.add]


class GCSpecialistAgentOllama:
    """
    GC Specialist Agent using Ollama (local LLM)
    Works with Granite 4 or any other Ollama model
    """
    
    def __init__(self, model_name: str = "granite3-dense:8b", 
                 base_url: str = "http://localhost:11434"):
        """
        Initialize the GC Specialist Agent with Ollama
        
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
        """Build the LangGraph workflow for GC analysis"""
        workflow = StateGraph(GCAnalysisState)
        
        # Add nodes
        workflow.add_node("collect_gc_logs", self.collect_gc_logs)
        workflow.add_node("analyze_gc_patterns", self.analyze_gc_patterns)
        workflow.add_node("detect_memory_issues", self.detect_memory_issues)
        workflow.add_node("recommend_tuning", self.recommend_tuning)
        
        # Define edges
        workflow.set_entry_point("collect_gc_logs")
        workflow.add_edge("collect_gc_logs", "analyze_gc_patterns")
        workflow.add_edge("analyze_gc_patterns", "detect_memory_issues")
        workflow.add_edge("detect_memory_issues", "recommend_tuning")
        workflow.add_edge("recommend_tuning", END)
        
        return workflow.compile()
    
    def collect_gc_logs(self, state: GCAnalysisState) -> GCAnalysisState:
        """Node 1: Collect and parse GC logs"""
        try:
            gc_logs = state.get("gc_logs", "")
            
            if not gc_logs:
                state["errors"].append("No GC logs provided")
                return state
            
            # Parse GC log metrics
            metrics = self._parse_gc_logs(gc_logs)
            state["raw_metrics"] = metrics
            
            print(f"✓ Collected GC logs: {len(gc_logs)} characters")
            print(f"✓ Parsed metrics: {len(metrics)} entries")
            
        except Exception as e:
            state["errors"].append(f"Error collecting GC logs: {str(e)}")
            
        return state
    
    def analyze_gc_patterns(self, state: GCAnalysisState) -> GCAnalysisState:
        """Node 2: Analyze GC patterns using Ollama"""
        try:
            metrics = state.get("raw_metrics", {})
            
            if not metrics:
                state["errors"].append("No metrics available for pattern analysis")
                return state
            
            # Prepare metrics summary for LLM
            metrics_summary = self._format_metrics_for_analysis(metrics)
            
            # Create prompt for Ollama
            prompt = f"""You are a JVM Garbage Collection expert. Analyze the provided GC metrics and identify patterns.

Focus on:
1. GC pause times (Young GC and Full GC)
2. Heap usage patterns (before/after GC)
3. Old generation growth rate
4. Full GC frequency and triggers
5. Memory allocation rate

GC Metrics:
{metrics_summary}

Provide analysis in JSON format with these keys:
- pause_time_analysis: Analysis of GC pause times
- heap_usage_analysis: Heap utilization patterns
- old_gen_analysis: Old generation growth analysis
- full_gc_analysis: Full GC frequency analysis
- allocation_rate: Memory allocation rate assessment

Respond with valid JSON only."""
            
            # Get response from Ollama
            response = self.llm.invoke(prompt)
            
            # Parse LLM response
            try:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    patterns = json.loads(json_match.group())
                else:
                    patterns = {
                        "analysis": response,
                        "timestamp": datetime.now().isoformat()
                    }
            except json.JSONDecodeError:
                patterns = {
                    "analysis": response,
                    "timestamp": datetime.now().isoformat()
                }
            
            state["gc_patterns"] = patterns
            print(f"✓ Analyzed GC patterns")
            
        except Exception as e:
            state["errors"].append(f"Error analyzing GC patterns: {str(e)}")
            
        return state
    
    def detect_memory_issues(self, state: GCAnalysisState) -> GCAnalysisState:
        """Node 3: Detect memory issues, leaks, and excessive GC pauses"""
        try:
            patterns = state.get("gc_patterns", {})
            metrics = state.get("raw_metrics", {})
            
            if not patterns or not metrics:
                state["errors"].append("Insufficient data for issue detection")
                return state
            
            # Create prompt for Ollama
            prompt = f"""You are a JVM memory issue detection expert. Identify memory problems.

GC Patterns:
{json.dumps(patterns, indent=2)}

Raw Metrics:
{json.dumps(self._summarize_metrics(metrics), indent=2)}

Identify issues and provide as JSON array with these fields for each issue:
- type: Issue type (e.g., "Memory Leak", "Excessive GC", "Long Pause")
- severity: Critical/High/Medium/Low
- evidence: Evidence from metrics
- impact: Impact on application performance

Focus on:
1. Memory leaks (continuously growing old generation)
2. Excessive GC pauses (pause times > 1 second)
3. Frequent Full GCs (more than 1 per minute)
4. Heap sizing issues
5. Memory pressure indicators

Respond with valid JSON array only."""
            
            response = self.llm.invoke(prompt)
            
            # Parse issues
            try:
                json_match = re.search(r'\[.*\]', response, re.DOTALL)
                if json_match:
                    issues = json.loads(json_match.group())
                else:
                    issues = [{
                        "type": "Analysis Result",
                        "severity": "Info",
                        "description": response
                    }]
            except json.JSONDecodeError:
                issues = [{
                    "type": "Analysis Result",
                    "severity": "Info",
                    "description": response
                }]
            
            state["memory_issues"] = issues
            print(f"✓ Detected {len(issues)} memory issues")
            
        except Exception as e:
            state["errors"].append(f"Error detecting memory issues: {str(e)}")
            
        return state
    
    def recommend_tuning(self, state: GCAnalysisState) -> GCAnalysisState:
        """Node 4: Generate JVM tuning recommendations"""
        try:
            issues = state.get("memory_issues", [])
            patterns = state.get("gc_patterns", {})
            metrics = state.get("raw_metrics", {})
            
            # Create prompt for Ollama
            prompt = f"""You are a JVM tuning expert. Provide specific JVM tuning recommendations.

Memory Issues:
{json.dumps(issues, indent=2)}

GC Patterns:
{json.dumps(patterns, indent=2)}

Current Metrics:
{json.dumps(self._summarize_metrics(metrics), indent=2)}

Provide recommendations as JSON with these keys:
- jvm_parameters: Array of JVM parameter recommendations, each with:
  - parameter: JVM flag (e.g., -Xmx, -Xms)
  - recommended: Recommended value
  - justification: Why this change
  - priority: Critical/High/Medium/Low
- gc_algorithm: Recommended GC algorithm (G1GC, ZGC, etc.)
- heap_sizing: Heap sizing recommendations
- additional_flags: Other useful JVM flags
- summary: Brief summary of recommendations

Respond with valid JSON only."""
            
            response = self.llm.invoke(prompt)
            
            # Parse recommendations
            try:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    recommendations = json.loads(json_match.group())
                else:
                    recommendations = {"recommendations": response}
            except json.JSONDecodeError:
                recommendations = {"recommendations": response}
            
            state["tuning_recommendations"] = recommendations
            
            # Generate analysis summary
            summary = self._generate_summary(state)
            state["analysis_summary"] = summary
            
            print(f"✓ Generated tuning recommendations")
            print(f"✓ Analysis complete")
            
        except Exception as e:
            state["errors"].append(f"Error generating recommendations: {str(e)}")
            
        return state
    
    def _parse_gc_logs(self, gc_logs: str) -> Dict[str, Any]:
        """Parse GC logs and extract metrics"""
        metrics = {
            "young_gc_count": 0,
            "full_gc_count": 0,
            "total_pause_time": 0.0,
            "max_pause_time": 0.0,
            "heap_before": [],
            "heap_after": [],
            "timestamps": []
        }
        
        # Parse GC log patterns
        young_gc_pattern = r'\[GC.*?(\d+\.\d+).*?secs\]'
        full_gc_pattern = r'\[Full GC.*?(\d+\.\d+).*?secs\]'
        heap_pattern = r'(\d+)K->(\d+)K\((\d+)K\)'
        
        # Count Young GCs
        young_gcs = re.findall(young_gc_pattern, gc_logs)
        metrics["young_gc_count"] = len(young_gcs)
        
        # Count Full GCs
        full_gcs = re.findall(full_gc_pattern, gc_logs)
        metrics["full_gc_count"] = len(full_gcs)
        
        # Calculate pause times
        all_pauses = [float(p) for p in young_gcs + full_gcs]
        if all_pauses:
            metrics["total_pause_time"] = sum(all_pauses)
            metrics["max_pause_time"] = max(all_pauses)
            metrics["avg_pause_time"] = sum(all_pauses) / len(all_pauses)
        
        # Extract heap usage
        heap_matches = re.findall(heap_pattern, gc_logs)
        for before, after, total in heap_matches:
            metrics["heap_before"].append(int(before))
            metrics["heap_after"].append(int(after))
        
        return metrics
    
    def _format_metrics_for_analysis(self, metrics: Dict[str, Any]) -> str:
        """Format metrics for LLM analysis"""
        return f"""
GC Metrics Summary:
- Young GC Count: {metrics.get('young_gc_count', 0)}
- Full GC Count: {metrics.get('full_gc_count', 0)}
- Total Pause Time: {metrics.get('total_pause_time', 0):.3f}s
- Max Pause Time: {metrics.get('max_pause_time', 0):.3f}s
- Average Pause Time: {metrics.get('avg_pause_time', 0):.3f}s
- Heap Usage Pattern: {len(metrics.get('heap_before', []))} samples
"""
    
    def _summarize_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of metrics for LLM"""
        return {
            "gc_counts": {
                "young_gc": metrics.get("young_gc_count", 0),
                "full_gc": metrics.get("full_gc_count", 0)
            },
            "pause_times": {
                "total": metrics.get("total_pause_time", 0),
                "max": metrics.get("max_pause_time", 0),
                "avg": metrics.get("avg_pause_time", 0)
            },
            "heap_samples": len(metrics.get("heap_before", []))
        }
    
    def _generate_summary(self, state: GCAnalysisState) -> str:
        """Generate a human-readable summary of the analysis"""
        issues = state.get("memory_issues", [])
        recommendations = state.get("tuning_recommendations", {})
        
        summary = f"""
=== GC Analysis Summary ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Issues Detected: {len(issues)}
"""
        
        for i, issue in enumerate(issues, 1):
            summary += f"\n{i}. [{issue.get('severity', 'Unknown')}] {issue.get('type', 'Issue')}"
        
        summary += f"\n\nRecommendations: {len(recommendations)} categories"
        
        if state.get("errors"):
            summary += f"\n\nErrors: {len(state['errors'])}"
        
        return summary
    
    def analyze(self, gc_logs: str) -> Dict[str, Any]:
        """
        Main entry point to analyze GC logs
        
        Args:
            gc_logs: Raw GC log data as string
            
        Returns:
            Complete analysis results
        """
        initial_state = GCAnalysisState(
            gc_logs=gc_logs,
            raw_metrics={},
            gc_patterns={},
            memory_issues=[],
            tuning_recommendations=[],
            analysis_summary="",
            errors=[]
        )
        
        print("Starting GC analysis workflow with Ollama...")
        final_state = self.workflow.invoke(initial_state)
        
        return {
            "patterns": final_state.get("gc_patterns", {}),
            "issues": final_state.get("memory_issues", []),
            "recommendations": final_state.get("tuning_recommendations", {}),
            "summary": final_state.get("analysis_summary", ""),
            "errors": final_state.get("errors", [])
        }


# Example usage
if __name__ == "__main__":
    # Sample GC log for testing
    sample_gc_log = """
    [GC (Allocation Failure) 2023-01-15T10:30:45.123+0000: 1024K->512K(2048K), 0.0234567 secs]
    [GC (Allocation Failure) 2023-01-15T10:30:50.456+0000: 1536K->768K(2048K), 0.0345678 secs]
    [Full GC (Ergonomics) 2023-01-15T10:31:00.789+0000: 1800K->600K(2048K), 1.2345678 secs]
    [GC (Allocation Failure) 2023-01-15T10:31:10.012+0000: 1280K->640K(2048K), 0.0456789 secs]
    """
    
    # Initialize agent with Ollama
    print("Initializing GC Specialist Agent with Ollama...")
    agent = GCSpecialistAgentOllama(model_name="granite3-dense:8b")
    
    # Run analysis
    results = agent.analyze(sample_gc_log)
    
    # Print results
    print("\n" + "="*60)
    print("GC ANALYSIS RESULTS")
    print("="*60)
    print(json.dumps(results, indent=2))

# Made with Bob
