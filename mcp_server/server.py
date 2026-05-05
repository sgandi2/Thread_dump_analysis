"""
MCP Server for Thread Dump Analysis
Provides tools and resources for agent collaboration
Team Member: Sai
"""
import asyncio
import json
from typing import Any, Dict, List
from datetime import datetime

try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent, Resource
except ImportError:
    print("Warning: MCP not installed. Run: pip install mcp")
    Server = None

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.config import config
from shared.models import ThreadInfo, AnalysisResult, RemediationAction
from shared.utils import call_webmethods_api, parse_thread_dump


class ThreadDumpMCPServer:
    """
    MCP Server for Thread Dump Analysis
    Exposes tools and resources for agent collaboration
    """
    
    def __init__(self):
        if Server is None:
            raise ImportError("MCP package not installed")
        
        self.server = Server("thread-dump-analysis")
        self.config = config
        self._setup_tools()
        self._setup_resources()
        
        # Cache for storing analysis results
        self.analysis_cache: Dict[str, Any] = {}
        self.thread_dump_cache: Dict[str, str] = {}
    
    def _setup_tools(self):
        """Register all MCP tools"""
        
        @self.server.tool()
        async def get_thread_dump(server_url: str = None) -> str:
            """
            Collect thread dump from webMethods Integration Server
            
            Args:
                server_url: Optional server URL (uses config if not provided)
            
            Returns:
                JSON string with thread dump data
            """
            try:
                url = server_url or self.config.WEBMETHODS_URL
                
                # Call webMethods API to get thread dump
                response = call_webmethods_api("/invoke/wm.server/getThreadDump")
                
                # Store in cache
                timestamp = datetime.now().isoformat()
                self.thread_dump_cache[timestamp] = response.get("threadDump", "")
                
                result = {
                    "success": True,
                    "timestamp": timestamp,
                    "server_url": url,
                    "thread_count": len(parse_thread_dump(response.get("threadDump", ""))),
                    "raw_dump": response.get("threadDump", "")
                }
                
                return json.dumps(result, indent=2)
            
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        @self.server.tool()
        async def get_server_stats() -> str:
            """
            Get current server statistics from webMethods
            
            Returns:
                JSON string with server statistics
            """
            try:
                # Get thread pool stats
                stats = call_webmethods_api("/invoke/wm.server/getThreadPoolStats")
                
                result = {
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                    "stats": stats
                }
                
                return json.dumps(result, indent=2)
            
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        @self.server.tool()
        async def analyze_thread(thread_id: str, thread_dump: str = None) -> str:
            """
            Analyze a specific thread using AI
            
            Args:
                thread_id: Thread ID to analyze
                thread_dump: Optional thread dump data (uses latest if not provided)
            
            Returns:
                JSON string with analysis results
            """
            try:
                # Get thread dump from cache if not provided
                if not thread_dump and self.thread_dump_cache:
                    latest_timestamp = max(self.thread_dump_cache.keys())
                    thread_dump = self.thread_dump_cache[latest_timestamp]
                
                if not thread_dump:
                    return json.dumps({
                        "success": False,
                        "error": "No thread dump available"
                    })
                
                # Parse threads
                threads = parse_thread_dump(thread_dump)
                target_thread = next((t for t in threads if t.thread_id == thread_id), None)
                
                if not target_thread:
                    return json.dumps({
                        "success": False,
                        "error": f"Thread {thread_id} not found"
                    })
                
                # Basic analysis (AI analysis would be done by analyzer agent)
                analysis = {
                    "thread_id": thread_id,
                    "name": target_thread.name,
                    "state": target_thread.state,
                    "cpu_time": target_thread.cpu_time,
                    "is_hung": target_thread.is_hung(),
                    "is_blocked": target_thread.is_blocked(),
                    "stack_trace_length": len(target_thread.stack_trace),
                    "timestamp": datetime.now().isoformat()
                }
                
                # Store in cache
                self.analysis_cache[thread_id] = analysis
                
                return json.dumps({
                    "success": True,
                    "analysis": analysis
                }, indent=2)
            
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": str(e)
                })
        
        @self.server.tool()
        async def execute_remediation(action: str, thread_id: str, parameters: str = "{}") -> str:
            """
            Execute a remediation action on the Integration Server
            
            Args:
                action: Action type (kill_thread, restart_service, clear_pool, etc.)
                thread_id: Target thread ID
                parameters: JSON string with additional parameters
            
            Returns:
                JSON string with execution result
            """
            try:
                params = json.loads(parameters)
                
                # Create remediation action
                remediation = RemediationAction(
                    action_type=action,
                    target=thread_id,
                    parameters=params
                )
                
                # Execute based on action type
                if action == "kill_thread":
                    result = await self._kill_thread(thread_id)
                elif action == "restart_service":
                    result = await self._restart_service(params.get("service_name"))
                elif action == "clear_pool":
                    result = await self._clear_connection_pool(params.get("pool_name"))
                elif action == "trigger_gc":
                    result = await self._trigger_gc()
                else:
                    result = {"success": False, "error": f"Unknown action: {action}"}
                
                remediation.executed = True
                remediation.success = result.get("success", False)
                
                return json.dumps({
                    "success": result.get("success", False),
                    "action": action,
                    "thread_id": thread_id,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                }, indent=2)
            
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": str(e)
                })
        
        @self.server.tool()
        async def get_gc_logs(duration_minutes: int = 60) -> str:
            """
            Get GC logs from Integration Server
            
            Args:
                duration_minutes: Duration in minutes to fetch logs
            
            Returns:
                JSON string with GC log data
            """
            try:
                # Call webMethods API to get GC logs
                response = call_webmethods_api(
                    "/invoke/wm.server/getGCLogs",
                    data={"duration": duration_minutes}
                )
                
                return json.dumps({
                    "success": True,
                    "duration_minutes": duration_minutes,
                    "logs": response.get("gcLogs", ""),
                    "timestamp": datetime.now().isoformat()
                }, indent=2)
            
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": str(e)
                })
        
        @self.server.tool()
        async def get_cpu_metrics() -> str:
            """
            Get CPU metrics from Integration Server
            
            Returns:
                JSON string with CPU metrics
            """
            try:
                # Call webMethods API to get CPU metrics
                response = call_webmethods_api("/invoke/wm.server/getCPUMetrics")
                
                return json.dumps({
                    "success": True,
                    "metrics": response,
                    "timestamp": datetime.now().isoformat()
                }, indent=2)
            
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": str(e)
                })
    
    def _setup_resources(self):
        """Register MCP resources"""
        
        @self.server.resource("thread://current")
        async def current_threads() -> str:
            """Get current thread state"""
            try:
                response = call_webmethods_api("/invoke/wm.server/getThreadPoolStats")
                return json.dumps(response, indent=2)
            except Exception as e:
                return json.dumps({"error": str(e)})
        
        @self.server.resource("analysis://latest")
        async def latest_analysis() -> str:
            """Get latest analysis results"""
            if not self.analysis_cache:
                return json.dumps({"message": "No analysis results available"})
            
            return json.dumps(self.analysis_cache, indent=2)
        
        @self.server.resource("alerts://active")
        async def active_alerts() -> str:
            """Get active alerts"""
            # This would integrate with the monitor agent
            return json.dumps({
                "message": "Active alerts endpoint",
                "timestamp": datetime.now().isoformat()
            })
    
    async def _kill_thread(self, thread_id: str) -> Dict[str, Any]:
        """Kill a specific thread"""
        try:
            response = call_webmethods_api(
                "/invoke/wm.server/killThread",
                method="POST",
                data={"threadId": thread_id}
            )
            return {"success": True, "message": f"Thread {thread_id} killed"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _restart_service(self, service_name: str) -> Dict[str, Any]:
        """Restart a service"""
        try:
            response = call_webmethods_api(
                "/invoke/wm.server/restartService",
                method="POST",
                data={"serviceName": service_name}
            )
            return {"success": True, "message": f"Service {service_name} restarted"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _clear_connection_pool(self, pool_name: str) -> Dict[str, Any]:
        """Clear connection pool"""
        try:
            response = call_webmethods_api(
                "/invoke/wm.server/clearConnectionPool",
                method="POST",
                data={"poolName": pool_name}
            )
            return {"success": True, "message": f"Pool {pool_name} cleared"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _trigger_gc(self) -> Dict[str, Any]:
        """Trigger garbage collection"""
        try:
            response = call_webmethods_api(
                "/invoke/wm.server/triggerGC",
                method="POST"
            )
            return {"success": True, "message": "GC triggered"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def run(self):
        """Run the MCP server"""
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream)


async def main():
    """Main entry point"""
    print("=" * 60)
    print("Thread Dump Analysis - MCP Server")
    print("Team Member: Sai")
    print("=" * 60)
    print("\nStarting MCP server...")
    print("Available tools:")
    print("  - get_thread_dump: Collect thread dump from Integration Server")
    print("  - get_server_stats: Get server statistics")
    print("  - analyze_thread: Analyze specific thread")
    print("  - execute_remediation: Execute remediation actions")
    print("  - get_gc_logs: Get GC logs")
    print("  - get_cpu_metrics: Get CPU metrics")
    print("\nAvailable resources:")
    print("  - thread://current: Current thread state")
    print("  - analysis://latest: Latest analysis results")
    print("  - alerts://active: Active alerts")
    print("\n" + "=" * 60)
    
    try:
        server = ThreadDumpMCPServer()
        await server.run()
    except ImportError as e:
        print(f"\nError: {e}")
        print("Please install MCP: pip install mcp")
    except Exception as e:
        print(f"\nError starting server: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

# Made with Bob
