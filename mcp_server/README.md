# MCP Server for Thread Dump Analysis

## Overview

The MCP (Model Context Protocol) Server provides a standardized interface for all agents to interact with the webMethods Integration Server. It exposes tools and resources that enable agent collaboration and centralized server operations.

**Team Member:** Sai

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     MCP Server                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    Tools                              │  │
│  │  • get_thread_dump                                    │  │
│  │  • get_server_stats                                   │  │
│  │  • analyze_thread                                     │  │
│  │  • execute_remediation                                │  │
│  │  • get_gc_logs                                        │  │
│  │  • get_cpu_metrics                                    │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  Resources                            │  │
│  │  • thread://current                                   │  │
│  │  • analysis://latest                                  │  │
│  │  • alerts://active                                    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │  webMethods Integration │
              │        Server           │
              └─────────────────────────┘
```

## Available Tools

### 1. `get_thread_dump`
Collects thread dump from webMethods Integration Server.

**Parameters:**
- `server_url` (optional): Server URL (uses config if not provided)

**Returns:**
```json
{
  "success": true,
  "timestamp": "2024-01-01T12:00:00",
  "server_url": "http://localhost:5555",
  "thread_count": 45,
  "raw_dump": "..."
}
```

**Usage by Agents:**
- **Monitor Agent**: Trigger collection when issues detected
- **Collector Agent**: Primary tool for gathering dumps
- **Analyzer Agent**: Get dumps for analysis

---

### 2. `get_server_stats`
Retrieves current server statistics.

**Parameters:** None

**Returns:**
```json
{
  "success": true,
  "timestamp": "2024-01-01T12:00:00",
  "stats": {
    "total_threads": 45,
    "active_threads": 12,
    "cpu_usage": 75.5,
    "memory_usage": 82.3
  }
}
```

**Usage by Agents:**
- **Monitor Agent**: Continuous health monitoring
- **Dashboard**: Real-time metrics display

---

### 3. `analyze_thread`
Analyzes a specific thread.

**Parameters:**
- `thread_id` (required): Thread ID to analyze
- `thread_dump` (optional): Thread dump data (uses latest if not provided)

**Returns:**
```json
{
  "success": true,
  "analysis": {
    "thread_id": "123",
    "name": "HTTP-Worker-1",
    "state": "RUNNABLE",
    "cpu_time": 350.5,
    "is_hung": true,
    "is_blocked": false
  }
}
```

**Usage by Agents:**
- **Analyzer Agent**: Deep dive into specific threads
- **Remediation Agent**: Assess before taking action

---

### 4. `execute_remediation`
Executes remediation actions on the Integration Server.

**Parameters:**
- `action` (required): Action type (kill_thread, restart_service, clear_pool, trigger_gc)
- `thread_id` (required): Target thread ID
- `parameters` (optional): JSON string with additional parameters

**Returns:**
```json
{
  "success": true,
  "action": "kill_thread",
  "thread_id": "123",
  "result": {
    "success": true,
    "message": "Thread 123 killed"
  },
  "timestamp": "2024-01-01T12:00:00"
}
```

**Supported Actions:**
- `kill_thread`: Terminate a hung thread
- `restart_service`: Restart a specific service
- `clear_pool`: Clear connection pool
- `trigger_gc`: Force garbage collection

**Usage by Agents:**
- **Remediation Agent**: Execute automated fixes
- **Dashboard**: Manual remediation triggers

---

### 5. `get_gc_logs`
Retrieves garbage collection logs.

**Parameters:**
- `duration_minutes` (optional): Duration in minutes (default: 60)

**Returns:**
```json
{
  "success": true,
  "duration_minutes": 60,
  "logs": "...",
  "timestamp": "2024-01-01T12:00:00"
}
```

**Usage by Agents:**
- **GC Specialist Agent**: Analyze GC patterns
- **Analyzer Agent**: Correlate GC with thread issues

---

### 6. `get_cpu_metrics`
Retrieves CPU usage metrics.

**Parameters:** None

**Returns:**
```json
{
  "success": true,
  "metrics": {
    "overall_cpu": 75.5,
    "thread_cpu_usage": {
      "123": 45.2,
      "124": 30.1
    }
  },
  "timestamp": "2024-01-01T12:00:00"
}
```

**Usage by Agents:**
- **CPU Specialist Agent**: Analyze CPU patterns
- **Monitor Agent**: Detect CPU spikes

---

## Available Resources

### 1. `thread://current`
Get current thread state from the server.

**Usage:**
```python
# Access via MCP client
current_threads = await mcp_client.read_resource("thread://current")
```

---

### 2. `analysis://latest`
Get latest analysis results from cache.

**Usage:**
```python
latest_analysis = await mcp_client.read_resource("analysis://latest")
```

---

### 3. `alerts://active`
Get currently active alerts.

**Usage:**
```python
active_alerts = await mcp_client.read_resource("alerts://active")
```

---

## Running the MCP Server

### Start the Server

```bash
# From project root
python -m mcp_server.server

# Or directly
cd mcp_server
python server.py
```

### Configuration

The server uses environment variables from `.env`:

```bash
WEBMETHODS_URL=http://localhost:5555
WEBMETHODS_USER=Administrator
WEBMETHODS_PASSWORD=manage
MCP_SERVER_PORT=8080
```

---

## Agent Integration Examples

### Example 1: Monitor Agent Using MCP

```python
from mcp.client import Client

# Connect to MCP server
async with Client() as mcp:
    # Get server stats
    stats = await mcp.call_tool("get_server_stats")
    
    # If issues detected, collect thread dump
    if stats["stats"]["cpu_usage"] > 80:
        dump = await mcp.call_tool("get_thread_dump")
        # Trigger analysis...
```

### Example 2: Remediation Agent Using MCP

```python
from mcp.client import Client

async with Client() as mcp:
    # Analyze thread
    analysis = await mcp.call_tool(
        "analyze_thread",
        thread_id="123"
    )
    
    # If hung, execute remediation
    if analysis["analysis"]["is_hung"]:
        result = await mcp.call_tool(
            "execute_remediation",
            action="kill_thread",
            thread_id="123"
        )
```

### Example 3: GC Specialist Using MCP

```python
from mcp.client import Client

async with Client() as mcp:
    # Get GC logs
    gc_logs = await mcp.call_tool(
        "get_gc_logs",
        duration_minutes=30
    )
    
    # Analyze GC patterns
    # ... AI analysis logic ...
```

---

## Error Handling

All tools return a consistent error format:

```json
{
  "success": false,
  "error": "Error message here",
  "timestamp": "2024-01-01T12:00:00"
}
```

Always check the `success` field before processing results.

---

## Security Considerations

1. **Authentication**: Uses webMethods credentials from config
2. **Authorization**: All actions are logged
3. **Rollback**: Remediation actions support rollback where possible
4. **Audit Trail**: All operations are timestamped and cached

---

## Testing the MCP Server

### Test Tool Calls

```bash
# Test get_server_stats
echo '{"method": "tools/call", "params": {"name": "get_server_stats"}}' | python server.py

# Test get_thread_dump
echo '{"method": "tools/call", "params": {"name": "get_thread_dump"}}' | python server.py
```

### Test Resources

```bash
# Test thread://current resource
echo '{"method": "resources/read", "params": {"uri": "thread://current"}}' | python server.py
```

---

## Troubleshooting

### Server Won't Start

1. Check MCP package is installed: `pip install mcp`
2. Verify environment variables in `.env`
3. Check webMethods server is accessible

### Tool Calls Failing

1. Verify webMethods credentials
2. Check server URL is correct
3. Ensure webMethods API endpoints exist
4. Review error messages in server logs

### Connection Issues

1. Check firewall settings
2. Verify MCP_SERVER_PORT is not in use
3. Test webMethods connectivity: `curl http://localhost:5555/invoke/wm.server/ping`

---

## Development

### Adding New Tools

1. Add tool decorator in `_setup_tools()`:
```python
@self.server.tool()
async def my_new_tool(param1: str) -> str:
    """Tool description"""
    # Implementation
    return json.dumps(result)
```

2. Document the tool in this README
3. Test the tool
4. Update agent integration examples

### Adding New Resources

1. Add resource decorator in `_setup_resources()`:
```python
@self.server.resource("myresource://data")
async def my_resource() -> str:
    """Resource description"""
    return json.dumps(data)
```

---

## Support

For issues or questions:
- Check the main project README
- Review IMPLEMENTATION_PLAN.md
- Contact: Sai (MCP Server owner)

---

**Status:** ✅ Ready for agent integration
**Version:** 1.0.0
**Last Updated:** 2024-01-01