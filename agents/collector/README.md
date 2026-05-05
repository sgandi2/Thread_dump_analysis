# Thread Dump Collector Agent

**Team Member:** Ranadeep  
**Technology:** LangGraph  
**Purpose:** Collect thread dumps from webMethods Integration Server using OpenAPI specs

## Overview

The Thread Dump Collector Agent is a LangGraph-based intelligent agent that collects thread dumps from webMethods Integration Server. It uses a state machine workflow to ensure reliable collection with proper error handling and retry logic.

## Features

- ✅ **LangGraph Workflow**: State-based workflow with conditional edges
- ✅ **OpenAPI Integration**: Uses webMethods Integration Server REST API
- ✅ **Automatic Retry**: Retries failed collections up to 3 times
- ✅ **Thread Parsing**: Parses raw thread dumps into structured data
- ✅ **Metadata Enrichment**: Adds server statistics and metrics
- ✅ **Persistent Storage**: Saves thread dumps to JSON files
- ✅ **Error Handling**: Comprehensive error handling at each step
- ✅ **Progress Tracking**: Visual progress indicators for each step

## Architecture

### Workflow Steps

```
1. Validate Connection → 2. Authenticate → 3. Collect Thread Dump
                                              ↓
6. Store Data ← 5. Enrich Metadata ← 4. Parse Threads
```

### State Machine

The agent uses a `CollectorState` TypedDict to track:
- Server URL and API endpoint
- Authentication credentials
- Raw thread dump data
- Parsed thread objects
- Metadata and metrics
- Error information
- Retry count

### Conditional Edges

The workflow includes intelligent routing:
- **Connection Check**: Success → Authenticate, Error → Handle Error
- **Auth Check**: Success → Collect, Error → Handle Error
- **Collection Check**: Success → Parse, Retry → Collect Again, Error → Handle Error
- **Parsing Check**: Success → Enrich, Error → Handle Error

## Installation

### 1. Install Dependencies

```bash
cd agents/collector
pip install -r requirements.txt
```

### 2. Configure Environment

Create or update `.env` file in project root:

```env
# webMethods Integration Server
WEBMETHODS_URL=http://localhost:5555
WEBMETHODS_USER=Administrator
WEBMETHODS_PASSWORD=manage

# Data storage
DATA_DIR=data
```

## Usage

### Basic Usage

```python
from agents.collector.collector_agent import ThreadDumpCollectorAgent

# Create agent
agent = ThreadDumpCollectorAgent()

# Run collection workflow
result = agent.run()

# Check result
if result.get("error"):
    print(f"Collection failed: {result['error']}")
else:
    print(f"Collected {result['metadata']['thread_count']} threads")
    print(f"Stored at: {result['metadata']['storage_path']}")
```

### Custom Server URL

```python
# Use custom server URL
agent = ThreadDumpCollectorAgent(server_url="http://prod-server:5555")
result = agent.run()
```

### Custom API Endpoint

```python
# Use custom API endpoint
agent = ThreadDumpCollectorAgent()
result = agent.run(api_endpoint="/invoke/custom/getThreadDump")
```

### Command Line

```bash
# Run from project root
python -m agents.collector.collector_agent

# Or from collector directory
cd agents/collector
python collector_agent.py
```

## API Endpoints

The collector uses these webMethods Integration Server endpoints:

| Endpoint | Purpose | Method |
|----------|---------|--------|
| `/invoke/wm.server/ping` | Connection validation | GET |
| `/invoke/wm.server/getServerStats` | Authentication test | GET |
| `/invoke/wm.server/getThreadDump` | Thread dump collection | POST |
| `/invoke/wm.server/getThreadPoolStats` | Metadata enrichment | GET |

## Output Format

### Thread Dump File Structure

```json
{
  "server_url": "http://localhost:5555",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "total_threads": 150,
  "hung_threads": 2,
  "blocked_threads": 5,
  "threads": [
    {
      "thread_id": "0x00007f8a1c001000",
      "name": "HTTP Handler",
      "state": "RUNNABLE",
      "cpu_time": 45.2,
      "blocked_time": 0.0,
      "stack_trace": [
        "at java.net.SocketInputStream.read(...)",
        "at com.wm.app.b2b.server.HTTPHandler.run(...)"
      ]
    }
  ],
  "metadata": {
    "connection_status": "success",
    "auth_status": "success",
    "collection_status": "success",
    "parsing_status": "success",
    "storage_status": "success",
    "dump_size": 125000,
    "thread_count": 150,
    "hung_threads": 2,
    "blocked_threads": 5,
    "storage_path": "data/thread_dumps/dump_20240115_103000.json"
  }
}
```

## Workflow Details

### 1. Validate Connection (Step 1/6)

- Pings the Integration Server
- Verifies network connectivity
- Sets `connection_status` in metadata

### 2. Authenticate (Step 2/6)

- Tests credentials with server stats API
- Validates authentication
- Sets `auth_status` in metadata

### 3. Collect Thread Dump (Step 3/6)

- Calls thread dump API endpoint
- Includes stack traces and lock information
- Implements retry logic (up to 3 attempts)
- Sets `collection_status` in metadata

### 4. Parse Threads (Step 4/6)

- Parses raw thread dump text
- Extracts thread information
- Identifies hung and blocked threads
- Sets `parsing_status` in metadata

### 5. Enrich Metadata (Step 5/6)

- Fetches additional server statistics
- Adds thread pool metrics
- Non-blocking (continues on error)

### 6. Store Data (Step 6/6)

- Saves to JSON file
- Creates timestamped filename
- Stores in `data/thread_dumps/` directory
- Sets `storage_path` in metadata

## Error Handling

The agent handles errors at each step:

- **Connection Errors**: Network issues, server unavailable
- **Authentication Errors**: Invalid credentials, permission denied
- **Collection Errors**: Timeout, server error, invalid response
- **Parsing Errors**: Malformed thread dump, unexpected format
- **Storage Errors**: Disk full, permission denied

All errors are captured in the `error` field of the result state.

## Integration with Other Agents

### With Analyzer Agent

```python
from agents.collector.collector_agent import ThreadDumpCollectorAgent
from agents.analyzer.analyzer_agent import ThreadDumpAnalyzerAgent

# Collect thread dump
collector = ThreadDumpCollectorAgent()
result = collector.run()

if not result.get("error"):
    # Analyze collected threads
    analyzer = ThreadDumpAnalyzerAgent()
    analysis = analyzer.analyze(result["parsed_threads"])
```

### With Monitor Agent

```python
from agents.collector.collector_agent import ThreadDumpCollectorAgent
from agents.monitor.monitor_agent import MonitorAgent

# Monitor will automatically use collector
monitor = MonitorAgent()
monitor.start()  # Periodically collects thread dumps
```

## Testing

### Unit Tests

```bash
cd agents/collector
pytest test_collector_agent.py -v
```

### Integration Tests

```bash
# Requires running webMethods server
pytest test_collector_agent.py -v --integration
```

### Manual Testing

```python
# Test with mock server
from agents.collector.collector_agent import ThreadDumpCollectorAgent

agent = ThreadDumpCollectorAgent(server_url="http://localhost:5555")
result = agent.run()

print(f"Status: {'Success' if not result.get('error') else 'Failed'}")
print(f"Threads: {result['metadata'].get('thread_count', 0)}")
```

## Performance

- **Collection Time**: 2-5 seconds (typical)
- **Parsing Time**: < 1 second for 200 threads
- **Storage Time**: < 1 second
- **Total Time**: 3-7 seconds end-to-end

## Troubleshooting

### Connection Failed

```
Error: Connection failed: [Errno 111] Connection refused
```

**Solution**: Verify webMethods server is running and URL is correct.

### Authentication Failed

```
Error: Authentication failed: Invalid credentials
```

**Solution**: Check `WEBMETHODS_USER` and `WEBMETHODS_PASSWORD` in `.env`.

### Collection Timeout

```
Error: Thread dump collection timed out after 3 attempts
```

**Solution**: Increase timeout or check server load.

### Parsing Error

```
Error: Parsing error: Unexpected thread dump format
```

**Solution**: Verify thread dump format matches expected pattern.

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WEBMETHODS_URL` | `http://localhost:5555` | Integration Server URL |
| `WEBMETHODS_USER` | `Administrator` | Admin username |
| `WEBMETHODS_PASSWORD` | `manage` | Admin password |
| `DATA_DIR` | `data` | Data storage directory |
| `HUNG_THREAD_THRESHOLD` | `300` | Hung thread threshold (seconds) |

### Customization

```python
# Custom thresholds
from shared.config import config

config.HUNG_THREAD_THRESHOLD = 600  # 10 minutes

# Custom data directory
config.DATA_DIR = "/var/log/thread_dumps"
```

## Best Practices

1. **Regular Collection**: Run every 60 seconds for monitoring
2. **Error Handling**: Always check for errors in result
3. **Storage Management**: Implement log rotation for old dumps
4. **Performance**: Use async collection for multiple servers
5. **Security**: Use environment variables for credentials

## Future Enhancements

- [ ] Async collection for multiple servers
- [ ] Real-time streaming of thread dumps
- [ ] Compression for large thread dumps
- [ ] Incremental collection (only changed threads)
- [ ] WebSocket support for live updates
- [ ] Custom parsing rules via configuration

## Support

For issues or questions:
- Check logs in `logs/` directory
- Review error messages in result state
- Verify server connectivity and credentials
- Contact: Ranadeep (Team Member)

## License

Internal use only - webMethods Thread Dump Analysis System