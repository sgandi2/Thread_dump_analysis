"""
Integrated MCP Server for Thread Dump Analysis
Integrates Collector, Analyzer, and Remediation LangGraph agents
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
from agents.collector.collector_agent import ThreadDumpCollectorAgent
from agents.analyzer.analyzer_agent import ThreadDumpAnalyzerAgent
from agents.remediation.remediation_agent import RemediationAgent


class IntegratedThreadDumpMCPServer:
    """
    Integrated MCP Server for Thread Dump Analysis
    Exposes LangGraph agents as MCP tools
    """
    
    def __init__(self):
        if Server is None:
            raise ImportError("MCP package not installed")
        
        self.server = Server("thread-dump-analysis-integrated")
        self.config = config
        
        # Initialize agents
        self.collector_agent = ThreadDumpCollectorAgent()
        self.analyzer_agent = ThreadDumpAnalyzerAgent()
        self.remediation_agent = RemediationAgent(auto_approve=False)
        
        # Cache for storing results
        self.collection_cache: Dict[str, Any] = {}
        self.analysis_cache: Dict[str, Any] = {}
        self.remediation_cache: Dict[str, Any] = {}
        
        self._setup_tools()
        self._setup_resources()
    
    def _setup_tools(self):
        """Register all MCP tools"""
        
        @self.server.tool()
        async def collect_thread_dump(server_url: str = None) -> str:
            """
            Collect thread dump using LangGraph Collector Agent
            
            Args:
                server_url: Optional server URL (uses config if not provided)
            
            Returns:
                JSON string with collection result
            """
            try:
                # Run collector agent
                result = self.collector_agent.run()
                
                if result.get("error"):
                    return json.dumps({
                        "success": False,
                        "error": result["error"],
                        "timestamp": datetime.now().isoformat()
                    })
                
                # Store in cache
                timestamp = result["timestamp"].isoformat()
                self.collection_cache[timestamp] = result
                
                return json.dumps({
                    "success": True,
                    "timestamp": timestamp,
                    "server_url": result["server_url"],
                    "thread_count": result["metadata"].get("thread_count", 0),
                    "hung_threads": result["metadata"].get("hung_threads", 0),
                    "blocked_threads": result["metadata"].get("blocked_threads", 0),
                    "storage_path": result["metadata"].get("storage_path", ""),
                    "message": "Thread dump collected successfully"
                }, indent=2)
            
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        @self.server.tool()
        async def analyze_thread_dump(use_latest: bool = True, timestamp: str = None) -> str:
            """
            Analyze thread dump using LangGraph Analyzer Agent
            
            Args:
                use_latest: Use latest collected thread dump
                timestamp: Specific timestamp to analyze (if not using latest)
            
            Returns:
                JSON string with analysis result
            """
            try:
                # Get threads from cache
                if use_latest and self.collection_cache:
                    latest_timestamp = max(self.collection_cache.keys())
                    collection_result = self.collection_cache[latest_timestamp]
                elif timestamp and timestamp in self.collection_cache:
                    collection_result = self.collection_cache[timestamp]
                else:
                    return json.dumps({
                        "success": False,
                        "error": "No thread dump available. Run collect_thread_dump first."
                    })
                
                threads = collection_result["parsed_threads"]
                
                # Run analyzer agent
                analysis_result = self.analyzer_agent.analyze(threads)
                
                # Store in cache
                analysis_timestamp = datetime.now().isoformat()
                self.analysis_cache[analysis_timestamp] = analysis_result
                
                return json.dumps({
                    "success": True,
                    "timestamp": analysis_timestamp,
                    "severity": analysis_result.severity.value,
                    "total_threads": analysis_result.total_threads,
                    "hung_threads": analysis_result.hung_threads,
                    "blocked_threads": analysis_result.blocked_threads,
                    "deadlocks": len(analysis_result.deadlocks),
                    "patterns": len(analysis_result.details.get("patterns", [])),
                    "recommendations": analysis_result.recommendations,
                    "summary": analysis_result.summary,
                    "message": "Analysis completed successfully"
                }, indent=2)
            
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        @self.server.tool()
        async def remediate_issue(
            thread_id: str = None,
            auto_approve: bool = False,
            use_latest_analysis: bool = True
        ) -> str:
            """
            Execute remediation using LangGraph Remediation Agent
            
            Args:
                thread_id: Specific thread ID to remediate (optional)
                auto_approve: Auto-approve remediation actions
                use_latest_analysis: Use latest analysis result
            
            Returns:
                JSON string with remediation result
            """
            try:
                # Get analysis result
                if use_latest_analysis and self.analysis_cache:
                    latest_timestamp = max(self.analysis_cache.keys())
                    analysis_result = self.analysis_cache[latest_timestamp]
                else:
                    return json.dumps({
                        "success": False,
                        "error": "No analysis available. Run analyze_thread_dump first."
                    })
                
                # Get thread info if thread_id provided
                thread_info = None
                if thread_id and self.collection_cache:
                    latest_collection = max(self.collection_cache.keys())
                    threads = self.collection_cache[latest_collection]["parsed_threads"]
                    thread_info = next((t for t in threads if t.thread_id == thread_id), None)
                
                # Update agent auto-approve setting
                self.remediation_agent.auto_approve = auto_approve
                
                # Run remediation agent
                remediation_result = self.remediation_agent.run(
                    thread_info=thread_info,
                    analysis_result=analysis_result.to_dict() if hasattr(analysis_result, 'to_dict') else {}
                )
                
                if remediation_result.get("error"):
                    return json.dumps({
                        "success": False,
                        "error": remediation_result["error"],
                        "timestamp": datetime.now().isoformat()
                    })
                
                # Store in cache
                remediation_timestamp = datetime.now().isoformat()
                self.remediation_cache[remediation_timestamp] = remediation_result
                
                exec_result = remediation_result.get("execution_result", {})
                
                return json.dumps({
                    "success": True,
                    "timestamp": remediation_timestamp,
                    "action": exec_result.get("action", "N/A"),
                    "status": exec_result.get("status", "N/A"),
                    "approved": remediation_result.get("approved", False),
                    "severity": remediation_result["metadata"].get("severity", "N/A"),
                    "message": "Remediation completed successfully"
                }, indent=2)
            
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        @self.server.tool()
        async def full_workflow(server_url: str = None, auto_remediate: bool = False) -> str:
            """
            Execute complete workflow: Collect → Analyze → Remediate
            
            Args:
                server_url: Optional server URL
                auto_remediate: Automatically remediate if issues found
            
            Returns:
                JSON string with complete workflow result
            """
            try:
                workflow_result = {
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                    "steps": {}
                }
                
                # Step 1: Collect
                collect_result = await collect_thread_dump(server_url)
                collect_data = json.loads(collect_result)
                workflow_result["steps"]["collection"] = collect_data
                
                if not collect_data.get("success"):
                    workflow_result["success"] = False
                    workflow_result["error"] = "Collection failed"
                    return json.dumps(workflow_result, indent=2)
                
                # Step 2: Analyze
                analyze_result = await analyze_thread_dump(use_latest=True)
                analyze_data = json.loads(analyze_result)
                workflow_result["steps"]["analysis"] = analyze_data
                
                if not analyze_data.get("success"):
                    workflow_result["success"] = False
                    workflow_result["error"] = "Analysis failed"
                    return json.dumps(workflow_result, indent=2)
                
                # Step 3: Remediate (if needed and auto_remediate is True)
                if auto_remediate and analyze_data.get("severity") in ["critical", "high", "medium"]:
                    remediate_result = await remediate_issue(
                        auto_approve=True,
                        use_latest_analysis=True
                    )
                    remediate_data = json.loads(remediate_result)
                    workflow_result["steps"]["remediation"] = remediate_data
                else:
                    workflow_result["steps"]["remediation"] = {
                        "skipped": True,
                        "reason": "Auto-remediation disabled or severity too low"
                    }
                
                workflow_result["message"] = "Complete workflow executed successfully"
                return json.dumps(workflow_result, indent=2)
            
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        @self.server.tool()
        async def get_status() -> str:
            """
            Get current status of all agents and cached data
            
            Returns:
                JSON string with status information
            """
            try:
                return json.dumps({
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                    "agents": {
                        "collector": "ready",
                        "analyzer": "ready",
                        "remediation": "ready"
                    },
                    "cache": {
                        "collections": len(self.collection_cache),
                        "analyses": len(self.analysis_cache),
                        "remediations": len(self.remediation_cache)
                    },
                    "config": {
                        "server_url": self.config.WEBMETHODS_URL,
                        "auto_approve": self.remediation_agent.auto_approve
                    }
                }, indent=2)
            
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": str(e)
                })
    
    def _setup_resources(self):
        """Register MCP resources"""
        
        @self.server.resource("thread://latest")
        async def get_latest_thread_dump() -> str:
            """Get latest collected thread dump"""
            if not self.collection_cache:
                return json.dumps({"error": "No thread dumps available"})
            
            latest_timestamp = max(self.collection_cache.keys())
            return json.dumps(self.collection_cache[latest_timestamp], indent=2, default=str)
        
        @self.server.resource("analysis://latest")
        async def get_latest_analysis() -> str:
            """Get latest analysis result"""
            if not self.analysis_cache:
                return json.dumps({"error": "No analyses available"})
            
            latest_timestamp = max(self.analysis_cache.keys())
            analysis = self.analysis_cache[latest_timestamp]
            return json.dumps(analysis.to_dict() if hasattr(analysis, 'to_dict') else analysis, indent=2)
        
        @self.server.resource("remediation://latest")
        async def get_latest_remediation() -> str:
            """Get latest remediation result"""
            if not self.remediation_cache:
                return json.dumps({"error": "No remediations available"})
            
            latest_timestamp = max(self.remediation_cache.keys())
            return json.dumps(self.remediation_cache[latest_timestamp], indent=2, default=str)
    
    async def run(self):
        """Run the MCP server"""
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point"""
    server = IntegratedThreadDumpMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())

# Made with Bob
