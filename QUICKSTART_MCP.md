# Quick Start Guide - MCP Integration

## Prerequisites

- Python 3.8+
- webMethods Integration Server (running)
- MCP package installed

## Installation

### 1. Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Install MCP package
pip install mcp
```

### 2. Configure Environment

Create a `.env` file in the project root:

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

### 3. Start MCP Server

```bash
# Run the integrated MCP server
python mcp_server/server_integrated.py
```

## Quick Test

### Test 1: Check Server Status

```python
import asyncio
from mcp_server.server_integrated import IntegratedThreadDumpMCPServer

async def test_status():
    server = IntegratedThreadDumpMCPServer()
    await server._setup_tools()
    
    # Get status
    status = await server.get_status()
    print(f"Server Status: {status}")

asyncio.run(test_status())
```

### Test 2: Collect Thread Dump

```python
import asyncio
from mcp_server.server_integrated import IntegratedThreadDumpMCPServer

async def test_collect():
    server = IntegratedThreadDumpMCPServer()
    await server._setup_tools()
    
    # Collect thread dump
    result = await server.collect_thread_dump()
    print(f"Collection Result: {result}")

asyncio.run(test_collect())
```

### Test 3: Full Workflow

```python
import asyncio
from mcp_server.server_integrated import IntegratedThreadDumpMCPServer

async def test_workflow():
    server = IntegratedThreadDumpMCPServer()
    await server._setup_tools()
    
    # Run complete workflow
    result = await server.full_workflow(auto_remediate=False)
    print(f"Workflow Result: {result}")

asyncio.run(test_workflow())
```

## Using with MCP Client

### Example: Claude Desktop Integration

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "thread-dump-analysis": {
      "command": "python",
      "args": ["c:/Bobathon/Thread_dump_analysis/mcp_server/server_integrated.py"],
      "env": {
        "WEBMETHODS_URL": "http://localhost:5555",
        "WEBMETHODS_USER": "Administrator",
        "WEBMETHODS_PASSWORD": "manage"
      }
    }
  }
}
```

### Example: Python MCP Client

```python
import mcp
import asyncio

async def main():
    # Connect to MCP server
    client = mcp.Client("thread-dump-analysis")
    
    # Use tools
    result = await client.call_tool("collect_thread_dump")
    print(f"Collected: {result['thread_count']} threads")
    
    analysis = await client.call_tool("analyze_thread_dump")
    print(f"Severity: {analysis['severity']}")
    
    # Access resources
    latest = await client.get_resource("thread://latest")
    print(f"Latest dump: {latest}")

asyncio.run(main())
```

## Available MCP Tools

1. **collect_thread_dump** - Collect thread dumps
2. **analyze_thread_dump** - Analyze collected dumps
3. **remediate_issue** - Execute remediation actions
4. **full_workflow** - Complete Collect→Analyze→Remediate
5. **get_status** - Get server and agent status

## Available MCP Resources

1. **thread://latest** - Latest thread dump
2. **analysis://latest** - Latest analysis result
3. **remediation://latest** - Latest remediation result

## Common Use Cases

### Use Case 1: Monitor and Alert

```python
async def monitor():
    server = IntegratedThreadDumpMCPServer()
    await server._setup_tools()
    
    while True:
        # Collect and analyze
        await server.collect_thread_dump()
        analysis = await server.analyze_thread_dump()
        
        # Alert if critical
        if analysis['severity'] == 'critical':
            print(f"ALERT: Critical issues detected!")
            print(f"Recommendations: {analysis['recommendations']}")
        
        # Wait 5 minutes
        await asyncio.sleep(300)
```

### Use Case 2: Automated Remediation

```python
async def auto_remediate():
    server = IntegratedThreadDumpMCPServer()
    await server._setup_tools()
    
    # Run workflow with auto-remediation
    result = await server.full_workflow(auto_remediate=True)
    
    if result['steps']['remediation']['success']:
        print(f"Remediation successful: {result['steps']['remediation']['action']}")
    else:
        print(f"Remediation failed: {result['steps']['remediation']['message']}")
```

### Use Case 3: Manual Review

```python
async def manual_review():
    server = IntegratedThreadDumpMCPServer()
    await server._setup_tools()
    
    # Collect and analyze
    await server.collect_thread_dump()
    analysis = await server.analyze_thread_dump()
    
    # Review recommendations
    print(f"Severity: {analysis['severity']}")
    print(f"Patterns: {analysis['patterns']}")
    print(f"Recommendations:")
    for rec in analysis['recommendations']:
        print(f"  - {rec}")
    
    # Manual approval for remediation
    if input("Proceed with remediation? (y/n): ").lower() == 'y':
        result = await server.remediate_issue(auto_approve=True)
        print(f"Remediation: {result['action']} - {result['status']}")
```

## Troubleshooting

### Issue: MCP package not found

```bash
pip install mcp
```

### Issue: Connection to webMethods failed

Check:
1. Server is running: `http://localhost:5555`
2. Credentials are correct in `.env`
3. Network connectivity

### Issue: Agent initialization failed

Check:
1. All dependencies installed: `pip install -r requirements.txt`
2. Shared modules accessible
3. Python version 3.8+

### Issue: Type errors in server_integrated.py

These are type hints warnings and don't affect functionality. To fix:

```bash
pip install --upgrade mcp
```

## Next Steps

1. ✅ MCP server running
2. ✅ Test basic functionality
3. ⏳ Integrate with monitoring dashboard
4. ⏳ Setup automated alerts
5. ⏳ Deploy to production

## Support

- Check logs in `logs/` directory
- Review agent documentation in `agents/*/README.md`
- Test individual agents first before full workflow
- Contact: Sai (MCP Integration Lead)

---

**Status**: ✅ MCP Integration Complete  
**Ready for**: Production deployment