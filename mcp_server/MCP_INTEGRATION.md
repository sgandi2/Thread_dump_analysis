# MCP Server Integration - Thread Dump Analysis

## Overview

The Thread Dump Analysis system is now fully integrated with Model Context Protocol (MCP), exposing all three LangGraph agents as MCP tools.

## Integrated Agents

### ✅ 1. Collector Agent
- **Tool**: `collect_thread_dump`
- **Purpose**: Collect thread dumps from webMethods Integration Server
- **LangGraph Workflow**: 6 steps (Validate → Authenticate → Collect → Parse → Enrich → Store)

### ✅ 2. Analyzer Agent  
- **Tool**: `analyze_thread_dump`
- **Purpose**: Analyze thread dumps and identify patterns
- **LangGraph Workflow**: 7 steps (Metrics → Deadlocks → Patterns → Stack Traces → Severity → Recommendations → Summary)

### ✅ 3. Remediation Agent
- **Tool**: `remediate_issue`
- **Purpose**: Execute automated remediation actions
- **LangGraph Workflow**: 7 nodes (Analyze → Recommend → Select → Approve → Execute → Verify)

## MCP Tools Available

### 1. `collect_thread_dump`
Collects thread dump using the LangGraph Collector Agent.

**Parameters:**
- `server_url` (optional): Server URL to collect from

**Returns:**
```json
{
  "success": true,
  "timestamp": "2024-01-15T10:30:00",
  "server_url": "http://localhost:5555",
  "thread_count": 150,
  "hung_threads": 2,
  "blocked_threads": 5,
  "storage_path": "data/thread_dumps/dump_20240115_103000.json",
  "message": "Thread dump collected successfully"
}
```

### 2. `analyze_thread_dump`
Analyzes collected thread dump using the LangGraph Analyzer Agent.

**Parameters:**
- `use_latest` (default: true): Use latest collected dump
- `timestamp` (optional): Specific timestamp to analyze

**Returns:**
```json
{
  "success": true,
  "timestamp": "2024-01-15T10:30:05",
  "severity": "medium",
  "total_threads": 150,
  "hung_threads": 2,
  "blocked_threads": 5,
  "deadlocks": 0,
  "patterns": 3,
  "recommendations": [
    "Kill or cancel 2 hung threads",
    "Review locking strategy"
  ],
  "summary": "Thread Dump Analysis - Severity: MEDIUM | ...",
  "message": "Analysis completed successfully"
}
```

### 3. `remediate_issue`
Executes remediation using the LangGraph Remediation Agent.

**Parameters:**
- `thread_id` (optional): Specific thread to remediate
- `auto_approve` (default: false): Auto-approve actions
- `use_latest_analysis` (default: true): Use latest analysis

**Returns:**
```json
{
  "success": true,
  "timestamp": "2024-01-15T10:30:10",
  "action": "kill_thread",
  "status": "success",
  "approved": true,
  "severity": "critical",
  "message": "Remediation completed successfully"
}
```

### 4. `full_workflow`
Executes complete workflow: Collect → Analyze → Remediate.

**Parameters:**
- `server_url` (optional): Server URL
- `auto_remediate` (default: false): Auto-remediate if issues found

**Returns:**
```json
{
  "success": true,
  "timestamp": "2024-01-15T10:30:15",
  "steps": {
    "collection": { "success": true, ... },
    "analysis": { "success": true, ... },
    "remediation": { "success": true, ... }
  },
  "message": "Complete workflow executed successfully"
}
```

### 5. `get_status`
Gets current status of all agents and cached data.

**Returns:**
```json
{
  "success": true,
  "timestamp": "2024-01-15T10:30:20",
  "agents": {
    "collector": "ready",
    "analyzer": "ready",
    "remediation": "ready"
  },
  "cache": {
    "collections": 5,
    "analyses": 5,
    "remediations": 3
  },
  "config": {
    "server_url": "http://localhost:5555",
    "auto_approve": false
  }
}
```

## MCP Resources Available

### 1. `thread://latest`
Returns the latest collected thread dump.

### 2. `analysis://latest`
Returns the latest analysis result.

### 3. `remediation://latest`
Returns the latest remediation result.

## Usage Examples

### Example 1: Collect and Analyze

```python
# Using MCP client
import mcp

client = mcp.Client("thread-dump-analysis-integrated")

# Collect thread dump
result = await client.call_tool("collect_thread_dump")
print(f"Collected {result['thread_count']} threads")

# Analyze
analysis = await client.call_tool("analyze_thread_dump", use_latest=True)
print(f"Severity: {analysis['severity']}")
print(f"Recommendations: {analysis['recommendations']}")
```

### Example 2: Full Workflow with Auto-Remediation

```python
# Execute complete workflow
result = await client.call_tool(
    "full_workflow",
    server_url="http://localhost:5555",
    auto_remediate=True
)

print(f"Collection: {result['steps']['collection']['success']}")
print(f"Analysis: {result['steps']['analysis']['severity']}")
print(f"Remediation: {result['steps']['remediation']['action']}")
```

### Example 3: Manual Remediation

```python
# Collect and analyze first
await client.call_tool("collect_thread_dump")
analysis = await client.call_tool("analyze_thread_dump")

# Remediate specific thread if needed
if analysis['hung_threads'] > 0:
    result = await client.call_tool(
        "remediate_issue",
        thread_id="0x1000",
        auto_approve=True
    )
    print(f"Remediation: {result['action']} - {result['status']}")
```

### Example 4: Access Resources

```python
# Get latest thread dump
latest_dump = await client.get_resource("thread://latest")

# Get latest analysis
latest_analysis = await client.get_resource("analysis://latest")

# Get latest remediation
latest_remediation = await client.get_resource("remediation://latest")
```

## Configuration

### Environment Variables

```env
# webMethods Integration Server
WEBMETHODS_URL=http://localhost:5555
WEBMETHODS_USER=Administrator
WEBMETHODS_PASSWORD=manage

# Thresholds
HUNG_THREAD_THRESHOLD=300
CPU_THRESHOLD=80.0
MEMORY_THRESHOLD=85.0

# MCP Settings
MCP_AUTO_APPROVE=false
```

### Starting the MCP Server

```bash
# Install MCP package
pip install mcp

# Run integrated MCP server
python mcp_server/server_integrated.py
```

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server (Integrated)                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Collector   │  │   Analyzer   │  │ Remediation  │      │
│  │    Agent     │→ │    Agent     │→ │    Agent     │      │
│  │  (LangGraph) │  │  (LangGraph) │  │  (LangGraph) │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         ↓                 ↓                  ↓               │
│  ┌──────────────────────────────────────────────────┐       │
│  │              Shared Infrastructure                │       │
│  │  (Models, Config, Utils, API Integration)        │       │
│  └──────────────────────────────────────────────────┘       │
│                          ↓                                    │
│  ┌──────────────────────────────────────────────────┐       │
│  │        webMethods Integration Server             │       │
│  └──────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## Benefits of MCP Integration

1. **Standardized Interface**: All agents accessible through MCP protocol
2. **Tool Composition**: Combine tools in workflows
3. **Resource Access**: Direct access to cached results
4. **Agent Collaboration**: Agents can call each other via MCP
5. **External Integration**: Easy integration with other MCP-compatible systems

## Testing MCP Integration

```bash
# Test MCP server
python -c "
from mcp_server.server_integrated import IntegratedThreadDumpMCPServer
import asyncio

async def test():
    server = IntegratedThreadDumpMCPServer()
    status = await server._setup_tools()
    print('MCP Server initialized successfully')

asyncio.run(test())
"
```

## Comparison: Original vs Integrated

### Original MCP Server (`server.py`)
- ❌ Basic API wrappers
- ❌ No LangGraph integration
- ❌ Limited workflow support
- ❌ Manual implementation

### Integrated MCP Server (`server_integrated.py`)
- ✅ Full LangGraph agent integration
- ✅ Complete workflow automation
- ✅ Intelligent analysis and remediation
- ✅ Production-ready agents

## Next Steps

1. ✅ All three agents integrated into MCP
2. ✅ Complete workflow tool available
3. ✅ Resources for accessing cached data
4. ⏳ Deploy MCP server to production
5. ⏳ Integrate with monitoring dashboard
6. ⏳ Add GC/CPU specialist agents (optional)

## Support

For issues or questions:
- Check MCP server logs
- Verify agent configuration
- Test individual agents first
- Contact: Sai (Team Member)

---

**Status**: ✅ All agents fully integrated into MCP Server  
**Ready for**: Production deployment and external integration