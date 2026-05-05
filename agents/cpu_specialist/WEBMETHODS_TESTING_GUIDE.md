# Testing CPU Specialist Agent with Local webMethods Integration Server

## 📋 Prerequisites

1. **webMethods Integration Server** running locally (default: http://localhost:5555)
2. **Admin credentials** (default: Administrator/manage)
3. **Python 3.8+** installed
4. **OpenAI API Key** for LLM analysis

## 🚀 Quick Start (5 Steps)

### Step 1: Install Dependencies
```bash
cd C:\Users\VinayMoola\Documents\GitHub\Thread_dump_analysis\agents\cpu_specialist
pip install -r requirements.txt
```

### Step 2: Set OpenAI API Key
```bash
# Windows PowerShell
$env:OPENAI_API_KEY="your-openai-api-key-here"

# Windows CMD
set OPENAI_API_KEY=your-openai-api-key-here

# Or add to config.py
```

### Step 3: Verify webMethods is Running
```bash
# Check if webMethods is accessible
curl http://localhost:5555
# Or open in browser: http://localhost:5555
```

### Step 4: Run the Test Script
```bash
python test_with_webmethods.py
```

### Step 5: Review Results
The script will:
- Connect to your webMethods server
- Collect CPU metrics and thread dumps
- Run AI analysis
- Display results and save to JSON file

## 📊 What the Test Does

### 1. Connection Test
```
Connecting to webMethods at http://localhost:5555...
✓ Connected successfully!
```

### 2. CPU Metrics Collection
```
Collecting CPU metrics...
✓ Overall CPU: 45.2%
✓ Process CPU: 38.5%
✓ Thread Count: 150
```

### 3. CPU History Collection (30 seconds)
```
Collecting CPU history (30 seconds)...
Collection 1/6...
Collection 2/6...
...
✓ Collected 6 data points
```

### 4. Thread Dump Collection
```
Fetching thread dump...
✓ Found 150 threads
```

### 5. AI Analysis
```
Running CPU analysis...
(This may take 10-30 seconds...)
✓ Analysis complete!
```

### 6. Results Display
```
=== CPU Analysis Summary ===
Generated: 2023-01-15 10:30:45

CPU Metrics:
- Overall CPU: 45.2%
- Process CPU: 38.5%
- Thread Count: 150
- Runnable Threads: 45

Hotspots Identified: 3
...
```

## 🔧 Configuration Options

### Modify Server Settings
Edit `test_with_webmethods.py`:

```python
# Configuration
WEBMETHODS_URL = "http://localhost:5555"  # Change if different port
USERNAME = "Administrator"                 # Your admin username
PASSWORD = "manage"                        # Your admin password
```

### Adjust Collection Duration
```python
# Collect for 60 seconds instead of 30
cpu_history = collect_cpu_history(
    connector, 
    duration_seconds=60,    # Change this
    interval_seconds=10     # And this
)
```

### Skip History Collection (Faster Test)
Comment out the history collection section:
```python
# print("\n3. Collecting CPU history (30 seconds)...")
# cpu_history = collect_cpu_history(connector, duration_seconds=30, interval_seconds=5)
# cpu_metrics['cpu_history'] = cpu_history
# print(f"   ✓ Collected {len(cpu_history)} data points")
```

## 📁 Output Files

The test creates a JSON file with complete results:
```
cpu_analysis_20230115_103045.json
```

Contains:
- CPU metrics
- Thread correlation data
- Identified hotspots
- Optimization recommendations
- JVM tuning suggestions

## 🐛 Troubleshooting

### Issue 1: Cannot Connect to webMethods
```
⚠ Could not connect to webMethods
→ Will use system-level metrics instead
```

**Solutions:**
1. Verify webMethods is running: `http://localhost:5555`
2. Check if port is correct (might be 5555, 5556, etc.)
3. Verify credentials (Administrator/manage)
4. Check firewall settings

**Fallback:** The script will use system-level CPU metrics from `psutil` if webMethods API is not accessible.

### Issue 2: OpenAI API Error
```
✗ Failed to initialize agent: AuthenticationError
→ Make sure OPENAI_API_KEY is set in environment
```

**Solutions:**
1. Set environment variable:
   ```bash
   $env:OPENAI_API_KEY="sk-..."
   ```
2. Or add to `config.py`:
   ```python
   OPENAI_API_KEY = "sk-..."
   ```
3. Verify API key is valid at https://platform.openai.com/api-keys

### Issue 3: Import Error
```
ModuleNotFoundError: No module named 'langgraph'
```

**Solution:**
```bash
pip install -r requirements.txt
```

### Issue 4: Permission Denied (psutil)
```
AccessDenied: psutil.Process.cpu_percent()
```

**Solution:** Run PowerShell/CMD as Administrator

### Issue 5: Slow Analysis
```
Running CPU analysis...
(This may take 10-30 seconds...)
```

**This is normal!** The LLM analysis takes time. If it's too slow:
- Use GPT-3.5 instead of GPT-4 (faster but less accurate)
- Reduce the amount of data being analyzed

## 🎯 Understanding the Results

### CPU Metrics
```json
{
  "overall_cpu_percent": 85.5,      // Total system CPU
  "process_cpu_percent": 78.2,      // webMethods process CPU
  "cpu_per_core": 10.7,             // Average per core
  "runnable_ratio": 0.3,            // 30% threads are runnable
  "blocked_ratio": 0.1              // 10% threads are blocked
}
```

**What to look for:**
- Overall CPU > 80% → High CPU usage
- Runnable ratio > 0.5 → Thread pool saturation
- Blocked ratio > 0.1 → Lock contention

### CPU Hotspots
```
1. [High] Inefficient Algorithm
   Threads: http-exec-1, http-exec-2
   CPU Impact: 45.2%
   Root Cause: O(n²) complexity in data processing
```

**Severity Levels:**
- **Critical**: Immediate action required
- **High**: Should be addressed soon
- **Medium**: Optimize when possible
- **Low**: Minor improvement opportunity

### Optimization Recommendations
```
1. [High] Algorithm Optimization
   Target: DataProcessor.process()
   Solution: Use HashMap for O(n) lookup
   Expected CPU Reduction: 40%
```

**Priority Levels:**
- **Critical**: Fix immediately
- **High**: Plan for next sprint
- **Medium**: Backlog item
- **Low**: Nice to have

## 📈 Advanced Usage

### 1. Continuous Monitoring
```python
import schedule
import time

def monitor_cpu():
    connector = WebMethodsConnector(...)
    agent = CPUSpecialistAgent()
    
    cpu_metrics = connector.get_server_stats()
    thread_dump = connector.get_thread_dump()
    results = agent.analyze(cpu_metrics, thread_dump)
    
    # Alert if high CPU
    if results['cpu_metrics']['overall_cpu_percent'] > 80:
        send_alert(results)

# Run every 5 minutes
schedule.every(5).minutes.do(monitor_cpu)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### 2. Compare Before/After Optimization
```python
# Before optimization
results_before = agent.analyze(cpu_metrics_before, thread_dump_before)

# Apply optimization
# ... make changes ...

# After optimization
results_after = agent.analyze(cpu_metrics_after, thread_dump_after)

# Compare
cpu_reduction = (
    results_before['cpu_metrics']['overall_cpu_percent'] -
    results_after['cpu_metrics']['overall_cpu_percent']
)
print(f"CPU reduced by {cpu_reduction:.1f}%")
```

### 3. Integration with Slack
```python
import requests

def send_to_slack(results):
    webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    
    message = {
        "text": f"CPU Analysis Complete",
        "attachments": [{
            "color": "danger" if results['cpu_metrics']['overall_cpu_percent'] > 80 else "good",
            "fields": [
                {"title": "Overall CPU", "value": f"{results['cpu_metrics']['overall_cpu_percent']:.1f}%"},
                {"title": "Hotspots", "value": str(len(results['hotspots']))},
                {"title": "Recommendations", "value": str(len(results['optimizations'].get('optimizations', [])))}
            ]
        }]
    }
    
    requests.post(webhook_url, json=message)
```

## 🔍 Interpreting webMethods-Specific Issues

### Common webMethods CPU Issues

1. **High HTTP Thread Pool Usage**
   - Symptom: Many `http-nio-*-exec-*` threads in RUNNABLE state
   - Solution: Increase thread pool size in `server.cnf`

2. **Database Connection Pool Exhaustion**
   - Symptom: Threads blocked on database connections
   - Solution: Increase connection pool size

3. **Document Processing Bottleneck**
   - Symptom: High CPU in document transformation services
   - Solution: Optimize document mappings, use streaming

4. **Integration Service Loops**
   - Symptom: Same service threads consuming high CPU
   - Solution: Review service logic for inefficient loops

## 📝 Next Steps

After running the test:

1. **Review the JSON output file** for detailed analysis
2. **Identify high-priority optimizations** from recommendations
3. **Implement fixes** in your webMethods services
4. **Re-run the test** to verify improvements
5. **Set up continuous monitoring** for production

## 🆘 Getting Help

If you encounter issues:

1. Check the error messages in the console output
2. Review the saved JSON file for detailed error information
3. Verify all prerequisites are met
4. Check the main README.md for additional documentation
5. Contact the development team

---

**Ready to test? Run:** `python test_with_webmethods.py`