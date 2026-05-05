"""
Thread Dump Collector Agent using LangGraph
Collects thread dumps from webMethods Integration Server API
Team Member: Ranadeep
"""
import json
import requests
from typing import TypedDict, List, Optional, Dict, Any
from datetime import datetime
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.config import config
from shared.models import ThreadInfo, ThreadDumpData
from shared.utils import parse_thread_dump


class CollectorState(TypedDict):
    """State for collector workflow"""
    server_url: str
    api_endpoint: str
    auth_credentials: Dict[str, str]
    thread_dump_raw: str
    parsed_threads: List[ThreadInfo]
    metadata: Dict[str, Any]
    error: Optional[str]
    timestamp: datetime
    retry_count: int


class ThreadDumpCollectorAgent:
    """
    LangGraph-based agent for collecting thread dumps from Integration Server
    Uses OpenAPI specs to interact with webMethods API
    """
    
    def __init__(self, server_url: Optional[str] = None):
        """
        Initialize the collector agent
        
        Args:
            server_url: Optional server URL (uses config if not provided)
        """
        self.config = config
        self.server_url = server_url or self.config.WEBMETHODS_URL
        self.memory = MemorySaver()
        self.graph = self._create_graph()
        
        # OpenAPI endpoints for webMethods Integration Server
        self.api_endpoints = {
            "thread_dump": "/invoke/wm.server/getThreadDump",
            "thread_stats": "/invoke/wm.server/getThreadPoolStats",
            "server_stats": "/invoke/wm.server/getServerStats",
            "ping": "/invoke/wm.server/ping"
        }
    
    def _create_graph(self) -> StateGraph:
        """Create LangGraph workflow for thread dump collection"""
        workflow = StateGraph(CollectorState)
        
        # Add nodes for each step in the workflow
        workflow.add_node("validate_connection", self.validate_connection)
        workflow.add_node("authenticate", self.authenticate)
        workflow.add_node("collect_thread_dump", self.collect_thread_dump)
        workflow.add_node("parse_threads", self.parse_threads)
        workflow.add_node("enrich_metadata", self.enrich_metadata)
        workflow.add_node("store_data", self.store_data)
        workflow.add_node("handle_error", self.handle_error)
        
        # Define the workflow edges
        workflow.set_entry_point("validate_connection")
        
        # Connection validation -> Authentication
        workflow.add_conditional_edges(
            "validate_connection",
            self._check_connection_status,
            {
                "success": "authenticate",
                "error": "handle_error"
            }
        )
        
        # Authentication -> Collection
        workflow.add_conditional_edges(
            "authenticate",
            self._check_auth_status,
            {
                "success": "collect_thread_dump",
                "error": "handle_error"
            }
        )
        
        # Collection -> Parsing
        workflow.add_conditional_edges(
            "collect_thread_dump",
            self._check_collection_status,
            {
                "success": "parse_threads",
                "retry": "collect_thread_dump",
                "error": "handle_error"
            }
        )
        
        # Parsing -> Enrichment
        workflow.add_conditional_edges(
            "parse_threads",
            self._check_parsing_status,
            {
                "success": "enrich_metadata",
                "error": "handle_error"
            }
        )
        
        # Enrichment -> Storage
        workflow.add_edge("enrich_metadata", "store_data")
        
        # Storage -> End
        workflow.add_edge("store_data", END)
        
        # Error handling -> End
        workflow.add_edge("handle_error", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    def validate_connection(self, state: CollectorState) -> CollectorState:
        """
        Validate connection to Integration Server
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with connection status
        """
        print(f"[1/6] Validating connection to {state['server_url']}...")
        
        try:
            # Ping the server to check connectivity
            ping_url = f"{state['server_url']}{self.api_endpoints['ping']}"
            response = requests.get(
                ping_url,
                timeout=10,
                verify=False  # For development; use proper SSL in production
            )
            
            if response.status_code == 200:
                print("+ Connection successful")
                state["metadata"]["connection_status"] = "success"
            else:
                state["error"] = f"Server returned status {response.status_code}"
                state["metadata"]["connection_status"] = "failed"
        
        except requests.exceptions.ConnectionError as e:
            state["error"] = f"Connection failed: {str(e)}"
            state["metadata"]["connection_status"] = "failed"
        except Exception as e:
            state["error"] = f"Unexpected error: {str(e)}"
            state["metadata"]["connection_status"] = "failed"
        
        return state
    
    def authenticate(self, state: CollectorState) -> CollectorState:
        """
        Authenticate with Integration Server
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with authentication status
        """
        print("[2/6] Authenticating with Integration Server...")
        
        try:
            # Test authentication with a simple API call
            test_url = f"{state['server_url']}{self.api_endpoints['server_stats']}"
            response = requests.get(
                test_url,
                auth=(
                    state["auth_credentials"]["username"],
                    state["auth_credentials"]["password"]
                ),
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                print("+ Authentication successful")
                state["metadata"]["auth_status"] = "success"
            elif response.status_code == 401:
                state["error"] = "Authentication failed: Invalid credentials"
                state["metadata"]["auth_status"] = "failed"
            else:
                state["error"] = f"Authentication error: Status {response.status_code}"
                state["metadata"]["auth_status"] = "failed"
        
        except Exception as e:
            state["error"] = f"Authentication error: {str(e)}"
            state["metadata"]["auth_status"] = "failed"
        
        return state
    
    def collect_thread_dump(self, state: CollectorState) -> CollectorState:
        """
        Collect thread dump from Integration Server using OpenAPI
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with thread dump data
        """
        print(f"[3/6] Collecting thread dump (attempt {state['retry_count'] + 1}/3)...")
        
        try:
            # Call the thread dump API endpoint
            dump_url = f"{state['server_url']}{state['api_endpoint']}"
            
            response = requests.post(
                dump_url,
                auth=(
                    state["auth_credentials"]["username"],
                    state["auth_credentials"]["password"]
                ),
                json={
                    "format": "text",  # Request text format for easier parsing
                    "includeStackTrace": True,
                    "includeLockedMonitors": True,
                    "includeLockedSynchronizers": True
                },
                timeout=60,  # Thread dumps can take time
                verify=False
            )
            
            if response.status_code == 200:
                # Extract thread dump from response
                response_data = response.json() if response.content else {}
                state["thread_dump_raw"] = response_data.get("threadDump", response.text)
                state["metadata"]["dump_size"] = len(state["thread_dump_raw"])
                state["metadata"]["collection_status"] = "success"
                print(f"+ Thread dump collected ({state['metadata']['dump_size']} bytes)")
            else:
                state["retry_count"] += 1
                if state["retry_count"] >= 3:
                    state["error"] = f"Failed to collect thread dump after 3 attempts: Status {response.status_code}"
                    state["metadata"]["collection_status"] = "failed"
                else:
                    state["metadata"]["collection_status"] = "retry"
        
        except requests.exceptions.Timeout:
            state["retry_count"] += 1
            if state["retry_count"] >= 3:
                state["error"] = "Thread dump collection timed out after 3 attempts"
                state["metadata"]["collection_status"] = "failed"
            else:
                state["metadata"]["collection_status"] = "retry"
        
        except Exception as e:
            state["error"] = f"Collection error: {str(e)}"
            state["metadata"]["collection_status"] = "failed"
        
        return state
    
    def parse_threads(self, state: CollectorState) -> CollectorState:
        """
        Parse thread dump into structured ThreadInfo objects
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with parsed threads
        """
        print("[4/6] Parsing thread dump...")
        
        try:
            # Use shared utility to parse thread dump
            threads = parse_thread_dump(state["thread_dump_raw"])
            state["parsed_threads"] = threads
            state["metadata"]["thread_count"] = len(threads)
            state["metadata"]["parsing_status"] = "success"
            
            # Calculate basic statistics
            hung_count = sum(1 for t in threads if t.is_hung())
            blocked_count = sum(1 for t in threads if t.is_blocked())
            
            state["metadata"]["hung_threads"] = hung_count
            state["metadata"]["blocked_threads"] = blocked_count
            
            print(f"+ Parsed {len(threads)} threads ({hung_count} hung, {blocked_count} blocked)")
        
        except Exception as e:
            state["error"] = f"Parsing error: {str(e)}"
            state["metadata"]["parsing_status"] = "failed"
        
        return state
    
    def enrich_metadata(self, state: CollectorState) -> CollectorState:
        """
        Enrich thread data with additional metadata
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with enriched metadata
        """
        print("[5/6] Enriching metadata...")
        
        try:
            # Get additional server statistics
            stats_url = f"{state['server_url']}{self.api_endpoints['thread_stats']}"
            response = requests.get(
                stats_url,
                auth=(
                    state["auth_credentials"]["username"],
                    state["auth_credentials"]["password"]
                ),
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                stats = response.json() if response.content else {}
                state["metadata"]["server_stats"] = stats
                print("+ Metadata enriched with server statistics")
            else:
                print("! Could not fetch server statistics")
        
        except Exception as e:
            print(f"! Metadata enrichment warning: {str(e)}")
            # Don't fail the workflow for metadata enrichment errors
        
        return state
    
    def store_data(self, state: CollectorState) -> CollectorState:
        """
        Store thread dump data for analysis
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with storage status
        """
        print("[6/6] Storing thread dump data...")
        
        try:
            # Create ThreadDumpData object
            thread_dump_data = ThreadDumpData(
                server_url=state["server_url"],
                timestamp=state["timestamp"],
                threads=state["parsed_threads"],
                total_threads=state["metadata"]["thread_count"],
                hung_threads=state["metadata"]["hung_threads"],
                blocked_threads=state["metadata"]["blocked_threads"]
            )
            
            # Store to file
            filename = f"data/thread_dumps/dump_{state['timestamp'].strftime('%Y%m%d_%H%M%S')}.json"
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            with open(filename, 'w') as f:
                json.dump({
                    "server_url": thread_dump_data.server_url,
                    "timestamp": thread_dump_data.timestamp.isoformat(),
                    "total_threads": thread_dump_data.total_threads,
                    "hung_threads": thread_dump_data.hung_threads,
                    "blocked_threads": thread_dump_data.blocked_threads,
                    "threads": [
                        {
                            "thread_id": t.thread_id,
                            "name": t.name,
                            "state": t.state,
                            "cpu_time": t.cpu_time,
                            "blocked_time": t.blocked_time,
                            "stack_trace": t.stack_trace[:10]  # Limit stack trace size
                        }
                        for t in thread_dump_data.threads
                    ],
                    "metadata": state["metadata"]
                }, f, indent=2)
            
            state["metadata"]["storage_path"] = filename
            state["metadata"]["storage_status"] = "success"
            print(f"+ Thread dump stored: {filename}")
        
        except Exception as e:
            state["error"] = f"Storage error: {str(e)}"
            state["metadata"]["storage_status"] = "failed"
        
        return state
    
    def handle_error(self, state: CollectorState) -> CollectorState:
        """
        Handle errors in the workflow
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with error handling
        """
        print(f"\nX Error occurred: {state['error']}")
        state["metadata"]["final_status"] = "failed"
        return state
    
    # Conditional edge functions
    def _check_connection_status(self, state: CollectorState) -> str:
        """Check connection validation status"""
        return "success" if state["metadata"].get("connection_status") == "success" else "error"
    
    def _check_auth_status(self, state: CollectorState) -> str:
        """Check authentication status"""
        return "success" if state["metadata"].get("auth_status") == "success" else "error"
    
    def _check_collection_status(self, state: CollectorState) -> str:
        """Check collection status"""
        status = state["metadata"].get("collection_status", "error")
        return status if status in ["success", "retry"] else "error"
    
    def _check_parsing_status(self, state: CollectorState) -> str:
        """Check parsing status"""
        return "success" if state["metadata"].get("parsing_status") == "success" else "error"
    
    def run(self, api_endpoint: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute the collection workflow
        
        Args:
            api_endpoint: Optional API endpoint (uses default if not provided)
        
        Returns:
            Final workflow state as dictionary
        """
        print("=" * 70)
        print("Thread Dump Collection Workflow - LangGraph Agent")
        print("=" * 70)
        
        # Initialize state
        initial_state: CollectorState = {
            "server_url": self.server_url,
            "api_endpoint": api_endpoint or self.api_endpoints["thread_dump"],
            "auth_credentials": {
                "username": self.config.WEBMETHODS_USER,
                "password": self.config.WEBMETHODS_PASSWORD
            },
            "thread_dump_raw": "",
            "parsed_threads": [],
            "metadata": {
                "workflow_start": datetime.now().isoformat()
            },
            "error": None,
            "timestamp": datetime.now(),
            "retry_count": 0
        }
        
        # Execute workflow
        try:
            # Add thread_id for checkpointer
            config = {"configurable": {"thread_id": "collector_1"}}
            result = self.graph.invoke(initial_state, config)
            
            # Print summary
            print("\n" + "=" * 70)
            if result.get("error"):
                print("X Collection Failed")
                print(f"Error: {result['error']}")
            else:
                print("+ Collection Successful")
                print(f"Threads collected: {result['metadata'].get('thread_count', 0)}")
                print(f"Hung threads: {result['metadata'].get('hung_threads', 0)}")
                print(f"Blocked threads: {result['metadata'].get('blocked_threads', 0)}")
                if result['metadata'].get('storage_path'):
                    print(f"Stored at: {result['metadata']['storage_path']}")
            print("=" * 70)
            
            return result
        
        except Exception as e:
            print(f"\nX Workflow execution failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"error": str(e), "metadata": {"final_status": "failed"}}


def main():
    """Main entry point for collector agent"""
    print("Thread Dump Collector Agent - LangGraph Implementation")
    print("Team Member: Ranadeep\n")
    
    # Create and run collector agent
    agent = ThreadDumpCollectorAgent()
    result = agent.run()
    
    # Exit with appropriate code
    exit(0 if not result.get("error") else 1)


if __name__ == "__main__":
    main()

# Made with Bob
