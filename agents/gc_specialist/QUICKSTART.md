# GC Specialist Agent - Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Step 1: Install Dependencies
```bash
cd agents/gc_specialist
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
from gc_agent import GCSpecialistAgent

# Initialize agent
agent = GCSpecialistAgent()

# Read sample GC log
with open('sample_gc.log', 'r') as f:
    gc_logs = f.read()

# Analyze
results = agent.analyze(gc_logs)

# Print results
print(results['summary'])
print("\nIssues Found:")
for issue in results['issues']:
    print(f"- [{issue['severity']}] {issue['type']}")

print("\nRecommendations:")
print(results['recommendations'])
```

### Step 4: Run Tests
```bash
python test_gc_agent.py
```

## 📊 Example Output

```
Starting GC analysis workflow...
✓ Collected GC logs: 2847 characters
✓ Parsed metrics: 18 entries
✓ Analyzed GC patterns
✓ Detected 5 memory issues
✓ Generated tuning recommendations
✓ Analysis complete

=== GC Analysis Summary ===
Generated: 2023-01-15 10:30:45

Issues Detected: 5

1. [Critical] Memory Leak
2. [High] Excessive Full GCs
3. [High] Long GC Pauses
4. [Medium] Heap Too Small
5. [Low] Explicit System.gc() Calls

Recommendations: 5 categories
```

## 🔧 Integration with webMethods

```python
import requests
from gc_agent import GCSpecialistAgent

def fetch_gc_logs_from_webmethods(server_url, username, password):
    """Fetch GC logs from webMethods Integration Server"""
    response = requests.get(
        f"{server_url}/admin/gc/logs",
        auth=(username, password)
    )
    return response.text

# Fetch and analyze
agent = GCSpecialistAgent()
gc_logs = fetch_gc_logs_from_webmethods(
    "http://localhost:5555",
    "Administrator",
    "manage"
)
results = agent.analyze(gc_logs)
```

## 🎯 Common Use Cases

### Use Case 1: Detect Memory Leaks
```python
agent = GCSpecialistAgent()
results = agent.analyze(gc_logs)

# Check for memory leaks
memory_leaks = [
    issue for issue in results['issues']
    if issue['type'] == 'Memory Leak'
]

if memory_leaks:
    print("⚠️ Memory leak detected!")
    for leak in memory_leaks:
        print(f"Evidence: {leak['evidence']}")
```

### Use Case 2: Optimize GC Performance
```python
agent = GCSpecialistAgent()
results = agent.analyze(gc_logs)

# Get JVM tuning recommendations
jvm_params = results['recommendations'].get('jvm_parameters', [])

print("Recommended JVM Parameters:")
for param in jvm_params:
    print(f"{param['parameter']}: {param['recommended']}")
    print(f"  Reason: {param['justification']}")
    print(f"  Priority: {param['priority']}")
```

### Use Case 3: Monitor GC Health
```python
from apscheduler.schedulers.background import BackgroundScheduler

def monitor_gc_health():
    agent = GCSpecialistAgent()
    gc_logs = fetch_gc_logs_from_webmethods(...)
    results = agent.analyze(gc_logs)
    
    # Check for critical issues
    critical_issues = [
        issue for issue in results['issues']
        if issue['severity'] == 'Critical'
    ]
    
    if critical_issues:
        send_alert_to_slack(critical_issues)

# Schedule monitoring every 5 minutes
scheduler = BackgroundScheduler()
scheduler.add_job(monitor_gc_health, 'interval', minutes=5)
scheduler.start()
```

## 🔍 Understanding the Output

### GC Patterns
```json
{
  "pause_time_analysis": "Average pause time is 0.5s, max is 3.6s",
  "heap_usage_analysis": "Heap utilization increasing from 50% to 99%",
  "old_gen_analysis": "Old generation growing at 15% per hour",
  "full_gc_analysis": "5 Full GCs in last minute - excessive",
  "allocation_rate": "High allocation rate detected"
}
```

### Memory Issues
```json
[
  {
    "type": "Memory Leak",
    "severity": "Critical",
    "evidence": "Old generation continuously growing",
    "impact": "Application will eventually run out of memory"
  }
]
```

### Tuning Recommendations
```json
{
  "jvm_parameters": [
    {
      "parameter": "-Xmx",
      "current": "1024m",
      "recommended": "4096m",
      "justification": "Heap too small for workload",
      "impact": "Reduce Full GC frequency by 80%",
      "risk": "Low",
      "priority": "High"
    }
  ],
  "gc_algorithm": "G1GC",
  "heap_sizing": "Increase heap to 4GB minimum"
}
```

## 🐛 Troubleshooting

### Issue: Import errors
```bash
# Solution: Install dependencies
pip install langgraph langchain-openai langchain-core
```

### Issue: OpenAI API errors
```bash
# Solution: Check API key
export OPENAI_API_KEY="your-key"
# Or set in config.py
```

### Issue: No GC logs found
```python
# Solution: Verify log format
# The agent expects standard JVM GC log format
# Example: [GC (Allocation Failure) 1024K->512K(2048K), 0.023 secs]
```

## 📈 Performance Tips

1. **Batch Analysis**: Analyze multiple log files together for better insights
2. **Cache Results**: Store analysis results to avoid re-analyzing same logs
3. **Adjust Temperature**: Lower temperature (0.0-0.2) for more consistent results
4. **Use GPT-4**: Better analysis quality than GPT-3.5

## 🔗 Integration Points

### With Remediation Agent
```python
# Send recommendations to remediation agent
if results['issues']:
    remediation_agent.execute(results['recommendations'])
```

### With Dashboard
```python
# Send results to dashboard
dashboard.update_gc_metrics(results)
```

### With Slack
```python
# Send alerts to Slack
if critical_issues:
    slack_client.send_message(
        channel="#alerts",
        text=f"Critical GC issues detected: {len(critical_issues)}"
    )
```

## 📚 Next Steps

1. Review the full [README.md](README.md) for detailed documentation
2. Check [gc_agent.py](gc_agent.py) for implementation details
3. Run [test_gc_agent.py](test_gc_agent.py) to verify setup
4. Integrate with your monitoring pipeline
5. Customize thresholds in config.py

## 💡 Tips for Best Results

- **Collect sufficient data**: Analyze at least 5-10 minutes of GC logs
- **Include context**: Provide application load information if available
- **Regular monitoring**: Run analysis every 5-15 minutes
- **Act on recommendations**: Implement high-priority recommendations first
- **Validate changes**: Monitor impact after applying tuning changes

## 🆘 Need Help?

- Check the [README.md](README.md) for detailed documentation
- Review sample logs in [sample_gc.log](sample_gc.log)
- Run tests to verify your setup
- Contact the development team

---

**Happy GC Tuning! 🚀**