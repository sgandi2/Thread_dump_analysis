# CPU Specialist Agent

## Overview
The CPU Specialist Agent is an AI-powered tool that analyzes CPU usage patterns, correlates them with thread activity, identifies performance bottlenecks, and provides actionable optimization recommendations using LangGraph workflow orchestration.

## Features

### 🔍 Analysis Capabilities
- **CPU Metrics Collection**: Gathers comprehensive CPU usage data
- **Thread Correlation**: Links CPU spikes to specific thread activity
- **Hotspot Identification**: Pinpoints CPU-intensive operations
- **Bottleneck Detection**: Identifies performance limiting factors
- **Pattern Recognition**: Detects inefficient CPU usage patterns

### 🤖 AI-Powered Insights
- Uses LLM (GPT-4) for intelligent correlation analysis
- Provides context-aware optimization recommendations
- Explains root causes of CPU bottlenecks
- Suggests specific code-level improvements

### 🔧 Optimization Recommendations
- Algorithm optimization suggestions
- Thread pool tuning recommendations
- JVM CPU optimization flags
- Caching strategies
- Parallelization opportunities
- Architecture-level improvements

## Architecture

### LangGraph Workflow
The agent uses a 4-node LangGraph workflow:

```
collect_cpu_metrics → correlate_with_threads → identify_hotspots → suggest_optimizations
```

#### Node 1: collect_cpu_metrics
- Collects CPU metrics from webMethods Integration Server
- Structures data (overall CPU, process CPU, thread counts)
- Calculates derived metrics (CPU per core, thread ratios)

#### Node 2: correlate_with_threads
- Uses LLM to correlate CPU spikes with thread activity
- Identifies CPU-intensive threads
- Analyzes thread states during high CPU periods
- Detects contention indicators

#### Node 3: identify_hotspots
- Identifies specific CPU hotspots
- Classifies bottleneck types (busy loops, inefficient algorithms, lock contention)
- Assesses severity and impact
- Provides root cause analysis

#### Node 4: suggest_optimizations
- Generates specific optimization recommendations
- Provides implementation details
- Estimates CPU reduction potential
- Assesses implementation complexity and risks

## Installation

### Prerequisites
```bash
pip install langgraph langchain-openai langchain-core psutil
```

### Environment Variables
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

### Basic Usage
```python
from agents.cpu_specialist import CPUSpecialistAgent

# Initialize the agent
agent = CPUSpecialistAgent(model_name="gpt-4", temperature=0.1)

# Prepare CPU metrics
cpu_metrics = {
    "overall_cpu": 85.5,
    "process_cpu": 78.2,
    "thread_count": 150,
    "runnable_threads": 45,
    "blocked_threads": 12,
    "cpu_cores": 8,
    "timestamp": "2023-01-15T10:30:00Z"
}

# Optional: Include thread dump for better correlation
thread_dump = {
    "threads": [
        {"id": 1, "name": "http-exec-1", "state": "RUNNABLE", "cpu_time": 5000},
        {"id": 2, "name": "pool-thread-1", "state": "BLOCKED", "cpu_time": 100}
    ]
}

# Analyze
results = agent.analyze(cpu_metrics, thread_dump)

# Access results
print(results['summary'])
print(results['hotspots'])
print(results['optimizations'])
```

### Integration with webMethods
```python
import requests
from agents.cpu_specialist import CPUSpecialistAgent

def fetch_cpu_metrics(server_url: str, auth_token: str) -> dict:
    """Fetch CPU metrics from webMethods Integration Server"""
    response = requests.get(
        f"{server_url}/admin/stats/cpu",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    return response.json()

def fetch_thread_dump(server_url: str, auth_token: str) -> dict:
    """Fetch thread dump from webMethods"""
    response = requests.get(
        f"{server_url}/admin/threads/dump",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    return response.json()

# Analyze
agent = CPUSpecialistAgent()
cpu_metrics = fetch_cpu_metrics("http://localhost:5555", "your-token")
thread_dump = fetch_thread_dump("http://localhost:5555", "your-token")
results = agent.analyze(cpu_metrics, thread_dump)
```

## Output Format

### Analysis Results
```json
{
  "cpu_metrics": {
    "overall_cpu_percent": 85.5,
    "process_cpu_percent": 78.2,
    "thread_count": 150,
    "runnable_threads": 45,
    "cpu_per_core": 10.7,
    "runnable_ratio": 0.3
  },
  "correlation": {
    "cpu_intensive_threads": [
      {"name": "http-exec-1", "cpu_time": 5000, "percentage": 25.5}
    ],
    "spike_patterns": "CPU spikes correlate with HTTP request processing",
    "contention_indicators": "12 blocked threads indicate lock contention"
  },
  "hotspots": [
    {
      "type": "Inefficient Algorithm",
      "severity": "High",
      "threads": ["http-exec-1", "http-exec-2"],
      "cpu_impact": 45.2,
      "root_cause": "O(n²) algorithm in data processing",
      "performance_impact": "Response time degradation under load"
    }
  ],
  "optimizations": {
    "optimizations": [
      {
        "type": "Algorithm Optimization",
        "target": "DataProcessor.process()",
        "current_issue": "Nested loops causing O(n²) complexity",
        "recommended_solution": "Use HashMap for O(n) lookup",
        "expected_cpu_reduction": 40,
        "complexity": "Medium",
        "priority": "High"
      }
    ],
    "thread_pool_tuning": {
      "current_size": 50,
      "recommended_size": 100,
      "justification": "High runnable thread ratio indicates pool saturation"
    },
    "jvm_flags": [
      "-XX:+UseParallelGC",
      "-XX:ParallelGCThreads=8"
    ]
  },
  "summary": "Analysis summary text",
  "errors": []
}
```

## Key Metrics Analyzed

### CPU Metrics
- Overall CPU utilization
- Process-specific CPU usage
- System vs User CPU time
- CPU per core utilization
- Load average

### Thread Metrics
- Total thread count
- Runnable threads (actively using CPU)
- Blocked threads (waiting for locks)
- Waiting threads (idle)
- Thread state distribution

### Correlation Metrics
- CPU-intensive threads
- Thread CPU time
- State transitions during CPU spikes
- Lock contention patterns

## Hotspot Types

### Common CPU Hotspots
1. **Busy Loops**: Threads spinning without yielding
2. **Inefficient Algorithms**: O(n²) or worse complexity
3. **Lock Contention**: Threads competing for locks
4. **Excessive Object Creation**: High allocation rate
5. **Blocking I/O**: Synchronous operations blocking threads
6. **Regex Compilation**: Repeated pattern compilation
7. **String Concatenation**: Inefficient string operations
8. **Reflection**: Heavy use of reflection APIs

## Optimization Strategies

### Algorithm Optimization
- Replace O(n²) with O(n log n) or O(n)
- Use appropriate data structures (HashMap vs ArrayList)
- Implement caching for repeated calculations
- Lazy evaluation where possible

### Thread Pool Tuning
- Adjust pool size based on workload
- Configure queue sizes appropriately
- Use separate pools for different task types
- Monitor pool saturation

### Parallelization
- Identify parallelizable operations
- Use parallel streams for data processing
- Implement work stealing algorithms
- Balance load across threads

### Caching
- Cache expensive computations
- Implement result memoization
- Use distributed caching for scalability
- Set appropriate TTL values

## Integration Points

### Input Sources
- webMethods Integration Server CPU metrics
- Thread dumps from JVM
- System monitoring tools (top, vmstat)
- APM tools (New Relic, AppDynamics)

### Output Destinations
- Remediation Agent (for automated fixes)
- Dashboard (for visualization)
- Slack notifications (for alerts)
- Log files (for audit trail)

## Configuration

### Agent Parameters
```python
agent = CPUSpecialistAgent(
    model_name="gpt-4",        # LLM model to use
    temperature=0.1            # Lower = more deterministic
)
```

### Thresholds (Customizable)
- High CPU threshold: 80%
- Critical CPU threshold: 95%
- Runnable thread ratio warning: 0.5
- Blocked thread ratio warning: 0.1

## Performance

- **Analysis Time**: ~5-10 seconds for typical metrics
- **Memory Usage**: ~100MB
- **API Calls**: 3-4 LLM calls per analysis

## Testing

Run the included test:
```bash
python cpu_agent.py
```

This will analyze sample CPU metrics and display results.

## Use Cases

### Use Case 1: Identify CPU Bottlenecks
```python
agent = CPUSpecialistAgent()
results = agent.analyze(cpu_metrics, thread_dump)

# Find critical hotspots
critical_hotspots = [
    h for h in results['hotspots']
    if h['severity'] == 'Critical'
]

for hotspot in critical_hotspots:
    print(f"Critical: {hotspot['type']}")
    print(f"Impact: {hotspot['cpu_impact']}% CPU")
    print(f"Root Cause: {hotspot['root_cause']}")
```

### Use Case 2: Optimize Thread Pools
```python
agent = CPUSpecialistAgent()
results = agent.analyze(cpu_metrics)

# Get thread pool recommendations
tuning = results['optimizations'].get('thread_pool_tuning', {})
print(f"Current pool size: {tuning['current_size']}")
print(f"Recommended size: {tuning['recommended_size']}")
print(f"Reason: {tuning['justification']}")
```

### Use Case 3: Monitor CPU Health
```python
from apscheduler.schedulers.background import BackgroundScheduler

def monitor_cpu():
    agent = CPUSpecialistAgent()
    cpu_metrics = fetch_cpu_metrics(...)
    results = agent.analyze(cpu_metrics)
    
    if results['cpu_metrics']['overall_cpu_percent'] > 90:
        send_alert(results['hotspots'])

scheduler = BackgroundScheduler()
scheduler.add_job(monitor_cpu, 'interval', minutes=5)
scheduler.start()
```

## Troubleshooting

### Issue: High CPU not detected
**Solution**: Ensure CPU metrics include historical data to detect spikes

### Issue: No thread correlation
**Solution**: Provide thread dump data with CPU time information

### Issue: Generic recommendations
**Solution**: Include more context in CPU metrics (application load, request rates)

## Future Enhancements

- [ ] Real-time CPU profiling
- [ ] Flame graph generation
- [ ] Historical trend analysis
- [ ] Predictive CPU spike detection
- [ ] Automated optimization application
- [ ] Integration with profiling tools
- [ ] Multi-server CPU analysis

## Contributing

When contributing to the CPU Specialist Agent:
1. Maintain the LangGraph workflow structure
2. Add comprehensive error handling
3. Include docstrings for all functions
4. Test with various CPU scenarios
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