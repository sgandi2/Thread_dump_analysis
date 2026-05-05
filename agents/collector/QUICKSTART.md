# Thread Dump Collector Agent - Quick Start Guide

**Team Member:** Ranadeep  
**Time to Complete:** 5-10 minutes

## Prerequisites

- Python 3.8 or higher
- webMethods Integration Server running (or access to one)
- Basic knowledge of Python

## Quick Setup (3 Steps)

### Step 1: Install Dependencies

```bash
# From project root
pip install -r agents/collector/requirements.txt

# Or install shared dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment

Create or update `.env` file in project root:

```env
# webMethods Integration Server Configuration
WEBMETHODS_URL=http://localhost:5555
WEBMETHODS_USER=Administrator
WEBMETHODS_PASSWORD=manage

# Data Storage
DATA_DIR=data
HUNG_THREAD_THRESHOLD=300
```

### Step 3: Run the Collector

```bash
# From project root
python -m agents.collector.collector_agent

# Or from collector directory
cd agents/collector
python collector_agent.py
```

## Expected Output

```
======================================================================
Thread Dump Collection Workflow - LangGraph Agent
======================================================================
[1/6] Validating connection to http://localhost:5555...
✓ Connection successful
[2/6] Authenticating with Integration Server...
✓ Authentication successful
[3/6] Collecting thread dump (attempt 1/3)...
✓ Thread dump collected (125000 bytes)
[4/6] Parsing thread dump...
✓ Parsed 150 threads (2 hung, 5 blocked)
[5/6] Enriching metadata...
✓ Metadata enriched with server statistics
[6/6] Storing thread dump data...
✓ Thread dump stored: data/thread_dumps/dump_20240115_103000.json

======================================================================
✅ Collection Successful
Threads collected: 150
Hung threads: 2
Blocked threads: 5
Stored at: data/thread_dumps/dump_20240115_103000.json
======================================================================
```

## Usage Examples

### Example 1: Basic Collection

```python
from agents.collector.collector_agent import ThreadDumpCollectorAgent

# Create and run collector
agent = ThreadDumpCollectorAgent()
result = agent.run()

# Check result
if not result.get("error"):
    print(f"Success! Collected {result['metadata']['thread_count']} threads")
```

### Example 2: Custom Server

```python
# Collect from production server
agent = ThreadDumpCollectorAgent(
    server_url="http://prod-server:5555"
)
result = agent.run()
```

### Example 3: Scheduled Collection

```python
import time
from agents.collector.collector_agent import ThreadDumpCollectorAgent

agent = ThreadDumpCollectorAgent()

# Collect every 60 seconds
while True:
    result = agent.run()
    if not result.get("error"):
        print(f"Collected at {result['timestamp']}")
    time.sleep(60)
```

## Testing

### Run Test Suite

```bash
# From project root
python agents/collector/test_collector.py

# Expected output:
# ✅ PASS - Thread Parsing
# ✅ PASS - Metrics Calculation
# ✅ PASS - Error Handling
# ✅ PASS - Basic Collection
# ✅ PASS - Custom Endpoint
# Total: 5/5 tests passed
```

### Quick Test

```python
# Test without server (parsing only)
from shared.utils import parse_thread_dump

sample_dump = '''
"HTTP Handler" #123 prio=5 tid=0x1000 nid=0x1234 runnable
   java.lang.Thread.State: RUNNABLE
'''

threads = parse_thread_dump(sample_dump)
print(f"Parsed {len(threads)} threads")
```

## Troubleshooting

### Issue: Connection Refused

```
Error: Connection failed: [Errno 111] Connection refused
```

**Solution:**
1. Verify webMethods server is running: `curl http://localhost:5555`
2. Check `WEBMETHODS_URL` in `.env`
3. Ensure firewall allows connection

### Issue: Authentication Failed

```
Error: Authentication failed: Invalid credentials
```

**Solution:**
1. Verify credentials in `.env`
2. Test login in browser: `http://localhost:5555`
3. Check user has admin privileges

### Issue: Module Not Found

```
ModuleNotFoundError: No module named 'langgraph'
```

**Solution:**
```bash
pip install -r agents/collector/requirements.txt
```

### Issue: Permission Denied

```
Error: Storage error: Permission denied
```

**Solution:**
```bash
# Create data directory with proper permissions
mkdir -p data/thread_dumps
chmod 755 data/thread_dumps
```

## Integration with Other Components

### With Monitor Agent

The monitor agent automatically uses the collector:

```python
from agents.monitor.monitor_agent import MonitorAgent

monitor = MonitorAgent()
monitor.start()  # Uses collector internally
```

### With Analyzer Agent

Pass collected threads to analyzer:

```python
from agents.collector.collector_agent import ThreadDumpCollectorAgent
from agents.analyzer.analyzer_agent import ThreadDumpAnalyzerAgent

# Collect
collector = ThreadDumpCollectorAgent()
result = collector.run()

# Analyze
if not result.get("error"):
    analyzer = ThreadDumpAnalyzerAgent()
    analysis = analyzer.analyze(result["parsed_threads"])
```

### With Dashboard

View collected data in dashboard:

```bash
# Start dashboard
streamlit run dashboard/app.py

# Navigate to "Thread Analysis" tab
# Select thread dump file from dropdown
```

## Next Steps

1. ✅ **Collector Working** - You've successfully collected thread dumps
2. 📊 **View Data** - Check `data/thread_dumps/` for collected files
3. 🔍 **Analyze** - Use analyzer agent to identify issues
4. 📈 **Monitor** - Set up continuous monitoring
5. 🚨 **Alerts** - Configure Slack notifications

## Advanced Configuration

### Custom Thresholds

```python
from shared.config import config

# Adjust hung thread threshold
config.HUNG_THREAD_THRESHOLD = 600  # 10 minutes

# Run collector with new threshold
agent = ThreadDumpCollectorAgent()
result = agent.run()
```

### Custom Storage Location

```python
from shared.config import config

# Change storage directory
config.THREAD_DUMPS_DIR = "/var/log/thread_dumps"

# Collector will use new location
agent = ThreadDumpCollectorAgent()
result = agent.run()
```

### Retry Configuration

Edit `collector_agent.py` to adjust retry behavior:

```python
# In collect_thread_dump method
if state["retry_count"] >= 5:  # Change from 3 to 5
    state["error"] = "Failed after 5 attempts"
```

## Performance Tips

1. **Batch Collection**: Collect from multiple servers in parallel
2. **Compression**: Enable compression for large dumps
3. **Cleanup**: Implement log rotation for old dumps
4. **Caching**: Cache server statistics between collections
5. **Async**: Use async collection for better performance

## API Reference

### ThreadDumpCollectorAgent

```python
class ThreadDumpCollectorAgent:
    def __init__(self, server_url: Optional[str] = None)
    def run(self, api_endpoint: Optional[str] = None) -> Dict[str, Any]
```

### Result Structure

```python
{
    "server_url": str,
    "api_endpoint": str,
    "thread_dump_raw": str,
    "parsed_threads": List[ThreadInfo],
    "metadata": {
        "connection_status": str,
        "auth_status": str,
        "collection_status": str,
        "parsing_status": str,
        "storage_status": str,
        "thread_count": int,
        "hung_threads": int,
        "blocked_threads": int,
        "storage_path": str
    },
    "error": Optional[str],
    "timestamp": datetime
}
```

## Support

- **Documentation**: See `agents/collector/README.md`
- **Tests**: Run `python agents/collector/test_collector.py`
- **Issues**: Check error messages in result state
- **Contact**: Ranadeep (Team Member)

## Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [webMethods API Reference](https://documentation.softwareag.com/)
- [Project README](../../README.md)

---

**Ready to collect thread dumps!** 🚀

If you encounter any issues, check the troubleshooting section or run the test suite.