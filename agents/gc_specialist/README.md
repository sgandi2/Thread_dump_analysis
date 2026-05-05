# GC Specialist Agent

## Overview
The GC Specialist Agent is an AI-powered tool that analyzes Java Garbage Collection (GC) logs from webMethods Integration Server and provides actionable JVM tuning recommendations using LangGraph workflow orchestration.

## Features

### 🔍 Analysis Capabilities
- **GC Pause Time Analysis**: Identifies excessive pause times affecting application performance
- **Heap Usage Pattern Detection**: Analyzes heap utilization before and after GC events
- **Old Generation Growth Tracking**: Detects potential memory leaks
- **Full GC Frequency Monitoring**: Identifies excessive Full GC events
- **Memory Allocation Rate Analysis**: Evaluates object creation patterns

### 🤖 AI-Powered Insights
- Uses LLM (GPT-4) for intelligent pattern recognition
- Provides context-aware recommendations
- Explains root causes of memory issues
- Suggests specific JVM parameters with justification

### 🔧 Tuning Recommendations
- JVM heap sizing recommendations (-Xmx, -Xms)
- GC algorithm selection (G1GC, ZGC, Shenandoah)
- GC tuning flags and parameters
- Performance optimization strategies
- Risk assessment for each recommendation

## Architecture

### LangGraph Workflow
The agent uses a 4-node LangGraph workflow:

```
collect_gc_logs → analyze_gc_patterns → detect_memory_issues → recommend_tuning
```

#### Node 1: collect_gc_logs
- Parses raw GC log data
- Extracts key metrics (pause times, heap usage, GC counts)
- Structures data for analysis

#### Node 2: analyze_gc_patterns
- Uses LLM to identify GC behavior patterns
- Analyzes pause times, heap usage, and allocation rates
- Detects trends and anomalies

#### Node 3: detect_memory_issues
- Identifies memory leaks
- Detects excessive GC pauses
- Flags frequent Full GCs
- Assesses heap sizing issues

#### Node 4: recommend_tuning
- Generates specific JVM parameter recommendations
- Suggests GC algorithm optimizations
- Provides implementation priorities
- Includes risk assessment

## Installation

### Prerequisites
```bash
pip install langgraph langchain-openai langchain-core
```

### Environment Variables
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

### Basic Usage
```python
from agents.gc_specialist import GCSpecialistAgent

# Initialize the agent
agent = GCSpecialistAgent(model_name="gpt-4", temperature=0.1)

# Analyze GC logs
gc_logs = """
[GC (Allocation Failure) 2023-01-15T10:30:45.123+0000: 1024K->512K(2048K), 0.0234567 secs]
[Full GC (Ergonomics) 2023-01-15T10:31:00.789+0000: 1800K->600K(2048K), 1.2345678 secs]
"""

results = agent.analyze(gc_logs)

# Access results
print(results['summary'])
print(results['issues'])
print(results['recommendations'])
```

### Integration with webMethods
```python
import requests
from agents.gc_specialist import GCSpecialistAgent

# Fetch GC logs from webMethods Integration Server
def fetch_gc_logs(server_url: str, auth_token: str) -> str:
    response = requests.get(
        f"{server_url}/admin/gc/logs",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    return response.text

# Analyze
agent = GCSpecialistAgent()
gc_logs = fetch_gc_logs("http://localhost:5555", "your-token")
results = agent.analyze(gc_logs)
```

## Output Format

### Analysis Results
```json
{
  "patterns": {
    "pause_time_analysis": "...",
    "heap_usage_analysis": "...",
    "old_gen_analysis": "...",
    "full_gc_analysis": "...",
    "allocation_rate": "..."
  },
  "issues": [
    {
      "type": "Memory Leak",
      "severity": "Critical",
      "evidence": "Old generation growing continuously",
      "impact": "Application will eventually run out of memory"
    }
  ],
  "recommendations": {
    "jvm_parameters": [
      {
        "parameter": "-Xmx",
        "current": "2048m",
        "recommended": "4096m",
        "justification": "Heap too small for workload",
        "impact": "Reduce Full GC frequency",
        "risk": "Low",
        "priority": "High"
      }
    ],
    "gc_algorithm": "G1GC",
    "heap_sizing": "...",
    "additional_flags": [...],
    "monitoring": "..."
  },
  "summary": "Analysis summary text",
  "errors": []
}
```

## Key Metrics Analyzed

### GC Pause Times
- Young GC pause duration
- Full GC pause duration
- Maximum pause time
- Average pause time
- Pause time distribution

### Heap Usage
- Heap size before/after GC
- Heap utilization percentage
- Old generation growth rate
- Young generation turnover

### GC Frequency
- Young GC count per minute
- Full GC count per minute
- Time between GCs
- GC trigger causes

## Tuning Recommendations

### Common Issues & Solutions

#### Issue: Frequent Full GCs
**Recommendations:**
- Increase heap size (-Xmx)
- Tune old generation size (-XX:NewRatio)
- Consider G1GC for better pause time control

#### Issue: Long GC Pauses
**Recommendations:**
- Switch to low-latency GC (ZGC, Shenandoah)
- Reduce heap size if over-provisioned
- Tune GC threads (-XX:ParallelGCThreads)

#### Issue: Memory Leak
**Recommendations:**
- Investigate object retention
- Enable heap dump on OOM (-XX:+HeapDumpOnOutOfMemoryError)
- Use memory profiler
- Review application code

## Integration Points

### Input Sources
- webMethods Integration Server GC logs
- JVM GC log files
- Real-time GC monitoring data

### Output Destinations
- Remediation Agent (for automated actions)
- Dashboard (for visualization)
- Slack notifications (for alerts)
- Log files (for audit trail)

## Configuration

### Agent Parameters
```python
agent = GCSpecialistAgent(
    model_name="gpt-4",        # LLM model to use
    temperature=0.1            # Lower = more deterministic
)
```

### Thresholds (Customizable)
- Max acceptable pause time: 1 second
- Full GC frequency threshold: 1 per minute
- Old generation growth rate: 10% per hour
- Heap utilization warning: 85%

## Error Handling

The agent includes comprehensive error handling:
- Invalid log format detection
- Missing data handling
- LLM API failure recovery
- Graceful degradation

Errors are collected in the `errors` field of the output.

## Performance

- **Analysis Time**: ~5-10 seconds for typical log files
- **Memory Usage**: ~100MB
- **API Calls**: 3-4 LLM calls per analysis

## Testing

Run the included test:
```bash
python gc_agent.py
```

This will analyze a sample GC log and display results.

## Future Enhancements

- [ ] Support for multiple GC log formats
- [ ] Historical trend analysis
- [ ] Predictive alerts
- [ ] Automated JVM parameter application
- [ ] Integration with APM tools
- [ ] Custom threshold configuration
- [ ] Multi-server analysis

## Contributing

When contributing to the GC Specialist Agent:
1. Maintain the LangGraph workflow structure
2. Add comprehensive error handling
3. Include docstrings for all functions
4. Test with various GC log formats
5. Update this README with new features

## License

Part of the Thread Dump Analysis AI Agent project.

## Support

For issues or questions:
- Check the main project documentation
- Review the implementation plan
- Contact the development team

---

**Author**: Vinay  
**Version**: 1.0.0  
**Last Updated**: 2026-05-05