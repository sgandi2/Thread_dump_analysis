# CPU Specialist Agent - Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Step 1: Install Dependencies
```bash
cd agents/cpu_specialist
pip install -r requirements.txt
```

### Step 2: Set Up Environment
```bash
# Copy the example config
cp config.example.py config.py

# Edit config.py and add your OpenAI API key
# Or set environment variable
export OPENAI_API_KEY="your-api-key-here"
```

### Step 3: Run a Test Analysis
```python
from cpu_agent import CPUSpecialistAgent
import json

# Initialize agent
agent = CPUSpecialistAgent()

# Load sample CPU data
with open('sample_cpu_data.json', 'r') as f:
    data = json.load(f)

# Analyze
results = agent.analyze(
    data['cpu_metrics'],
    data['thread_dump']
)

# Print results
print(results['summary'])
print("\nHotspots Found:")
for hotspot in results['hotspots']:
    print(f"- [{hotspot['severity']}] {hotspot['type']}")
    print(f"  CPU Impact: {hotspot.get('cpu_impact', 0)}%")

print("\nOptimizations:")
optimizations = results['optimizations'].get('optimizations', [])
for opt in optimizations[:3]:  # Top 3
    print(f"- {opt['type']}: {opt.get('target', 'N/A')}")
```

### Step 4: Run Tests
```bash
python test_cpu_agent.py
```

## 📊 Example Output

```
Starting CPU analysis workflow...
✓ Collected CPU metrics
  - Overall CPU: 92.5%
  - Process CPU: 88.3%
  - Thread count: 180
  - Runnable Threads: 95
✓ Correlated CPU usage with thread activity
✓ Identified 4 CPU hotspots
✓ Generated optimization suggestions
✓ CPU analysis complete

=== CPU Analysis Summary ===
Generated: 2023-01-15 10:30:45

CPU Metrics:
- Overall CPU: 92.5%
- Process CPU: 88.3%
- Thread Count: 180
- Runnable Threads: 95

Hotspots Identified: 4

1. [High] Inefficient Algorithm
2. [High] Lock Contention
3. [Medium] Regex Compilation
4. [Medium] String Concatenation

Optimization Recommendations: 5
```

## 🔧 Integration with webMethods

```python
import requests
from cpu_agent import CPUSpecialistAgent

def fetch_cpu_metrics(server_url: str, username: str, password: str) -> dict:
    """Fetch CPU metrics from webMethods Integration Server"""
    response = requests.get(
        f"{server_url}/admin/stats/cpu",
        auth=(username, password)
    )
    return response.json()

def fetch_thread_dump(server_url: str, username: str, password: str) -> dict:
    """Fetch thread dump from webMethods"""
    response = requests.get(
        f"{server_url}/admin/threads/dump",
        auth=(username, password)
    )
    return response.json()

# Fetch and analyze
agent = CPUSpecialistAgent()
cpu_metrics = fetch_cpu_metrics(
    "http://localhost:5555",
    "Administrator",
    "manage"
)
thread_dump = fetch_thread_dump(
    "http://localhost:5555",
    "Administrator",
    "manage"
)
results = agent.analyze(cpu_metrics, thread_dump)
```

## 🎯 Common Use Cases

### Use Case 1: Identify CPU Bottlenecks
```python
agent = CPUSpecialistAgent()
results = agent.analyze(cpu_metrics, thread_dump)

# Find critical hotspots
critical = [
    h for h in results['hotspots']
    if h['severity'] in ['Critical', 'High']
]

for hotspot in critical:
    print(f"⚠️ {hotspot['type']}")
    print(f"   Threads: {', '.join(hotspot.get('threads', []))}")
    print(f"   CPU Impact: {hotspot.get('cpu_impact', 0)}%")
    print(f"   Root Cause: {hotspot.get('root_cause', 'Unknown')}")
```

### Use Case 2: Get Optimization Recommendations
```python
agent = CPUSpecialistAgent()
results = agent.analyze(cpu_metrics, thread_dump)

# Get high-priority optimizations
optimizations = results['optimizations'].get('optimizations', [])
high_priority = [
    opt for opt in optimizations
    if opt.get('priority') == 'High'
]

for opt in high_priority:
    print(f"🔧 {opt['type']}")
    print(f"   Target: {opt.get('target', 'N/A')}")
    print(f"   Solution: {opt.get('recommended_solution', 'N/A')}")
    print(f"   Expected CPU Reduction: {opt.get('expected_cpu_reduction', 0)}%")
```

### Use Case 3: Monitor CPU Health
```python
from apscheduler.schedulers.background import BackgroundScheduler

def monitor_cpu_health():
    agent = CPUSpecialistAgent()
    cpu_metrics = fetch_cpu_metrics(...)
    thread_dump = fetch_thread_dump(...)
    results = agent.analyze(cpu_metrics, thread_dump)
    
    # Check for high CPU
    if results['cpu_metrics']['overall_cpu_percent'] > 90:
        send_alert_to_slack({
            'message': 'High CPU detected',
            'cpu': results['cpu_metrics']['overall_cpu_percent'],
            'hotspots': len(results['hotspots'])
        })

# Schedule monitoring every 5 minutes
scheduler = BackgroundScheduler()
scheduler.add_job(monitor_cpu_health, 'interval', minutes=5)
scheduler.start()
```

### Use Case 4: Correlate CPU with Threads
```python
agent = CPUSpecialistAgent()
results = agent.analyze(cpu_metrics, thread_dump)

# Get CPU-intensive threads
correlation = results['correlation']
cpu_threads = correlation.get('cpu_intensive_threads', [])

print("Top CPU-consuming threads:")
for thread in cpu_threads[:5]:
    print(f"- {thread['name']}: {thread.get('cpu_percentage', 0):.1f}%")
```

## 🔍 Understanding the Output

### CPU Metrics
```json
{
  "overall_cpu_percent": 92.5,
  "process_cpu_percent": 88.3,
  "cpu_per_core": 11.6,
  "runnable_ratio": 0.53,
  "blocked_ratio": 0.14
}
```

### Correlation Analysis
```json
{
  "cpu_intensive_threads": [
    {"name": "http-exec-1", "cpu_percentage": 25.5}
  ],
  "spike_patterns": "CPU spikes during HTTP request processing",
  "contention_indicators": "25 blocked threads indicate lock contention"
}
```

### CPU Hotspots
```json
[
  {
    "type": "Inefficient Algorithm",
    "severity": "High",
    "threads": ["http-exec-1", "http-exec-2"],
    "cpu_impact": 45.2,
    "root_cause": "O(n²) complexity in data processing",
    "performance_impact": "Response time degradation under load"
  }
]
```

### Optimization Suggestions
```json
{
  "optimizations": [
    {
      "type": "Algorithm Optimization",
      "target": "DataProcessor.process()",
      "current_issue": "Nested loops causing O(n²) complexity",
      "recommended_solution": "Use HashMap for O(n) lookup",
      "expected_cpu_reduction": 40,
      "complexity": "Medium",
      "priority": "High",
      "risks": "Increased memory usage"
    }
  ],
  "thread_pool_tuning": {
    "current_size": 50,
    "recommended_size": 100
  },
  "jvm_flags": ["-XX:+UseParallelGC"]
}
```

## 🐛 Troubleshooting

### Issue: Import errors
```bash
# Solution: Install dependencies
pip install langgraph langchain-openai langchain-core psutil
```

### Issue: OpenAI API errors
```bash
# Solution: Check API key
export OPENAI_API_KEY="your-key"
# Or set in config.py
```

### Issue: No thread correlation
```python
# Solution: Ensure thread dump includes CPU time
# Thread dump should have 'cpu_time' field for each thread
thread = {
    "id": 1,
    "name": "thread-name",
    "state": "RUNNABLE",
    "cpu_time": 5000  # Required for correlation
}
```

## 📈 Performance Tips

1. **Include Thread Dumps**: Always provide thread dump for better correlation
2. **Historical Data**: Include CPU history for trend analysis
3. **Adjust Temperature**: Lower temperature (0.0-0.2) for consistent results
4. **Use GPT-4**: Better analysis quality than GPT-3.5
5. **Batch Analysis**: Analyze multiple snapshots together

## 🔗 Integration Points

### With GC Specialist Agent
```python
from agents.gc_specialist import GCSpecialistAgent
from agents.cpu_specialist import CPUSpecialistAgent

# Analyze both CPU and GC
cpu_agent = CPUSpecialistAgent()
gc_agent = GCSpecialistAgent()

cpu_results = cpu_agent.analyze(cpu_metrics, thread_dump)
gc_results = gc_agent.analyze(gc_logs)

# Combine insights
if cpu_results['cpu_metrics']['overall_cpu_percent'] > 90:
    if gc_results['issues']:
        print("High CPU may be caused by GC issues")
```

### With Remediation Agent
```python
# Send recommendations to remediation agent
if results['hotspots']:
    remediation_agent.execute(results['optimizations'])
```

### With Dashboard
```python
# Send results to dashboard
dashboard.update_cpu_metrics(results)
```

## 📚 Next Steps

1. Review the full [README.md](README.md) for detailed documentation
2. Check [cpu_agent.py](cpu_agent.py) for implementation details
3. Run [test_cpu_agent.py](test_cpu_agent.py) to verify setup
4. Integrate with your monitoring pipeline
5. Customize thresholds in config.py

## 💡 Tips for Best Results

- **Collect sufficient data**: Analyze at least 5-10 minutes of metrics
- **Include thread dumps**: Essential for accurate correlation
- **Regular monitoring**: Run analysis every 5-15 minutes
- **Act on recommendations**: Implement high-priority optimizations first
- **Validate changes**: Monitor CPU after applying optimizations
- **Combine with GC analysis**: CPU and memory issues often related

## 🆘 Need Help?

- Check the [README.md](README.md) for detailed documentation
- Review sample data in [sample_cpu_data.json](sample_cpu_data.json)
- Run tests to verify your setup
- Contact the development team

---

**Happy CPU Optimization! 🚀**