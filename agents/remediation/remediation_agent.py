"""
Thread Dump Remediation Agent using LangGraph
Provides automated remediation for thread issues
Team Member: Sai
"""
import json
import requests
from typing import TypedDict, List, Optional, Dict, Any
from datetime import datetime
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from enum import Enum

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.config import config
from shared.models import ThreadInfo, RemediationAction, AlertSeverity


class RemediationType(Enum):
    """Types of remediation actions"""
    KILL_THREAD = "kill_thread"
    CANCEL_OPERATION = "cancel_operation"
    RESTART_SERVER = "restart_server"
    INCREASE_THREAD_POOL = "increase_thread_pool"
    CLEAR_CACHE = "clear_cache"
    FORCE_GC = "force_gc"
    NO_ACTION = "no_action"


class RemediationState(TypedDict):
    """State for remediation workflow"""
    server_url: str
    auth_credentials: Dict[str, str]
    thread_info: Optional[ThreadInfo]
    analysis_result: Dict[str, Any]
    recommended_actions: List[RemediationAction]
    selected_action: Optional[RemediationType]
    execution_result: Dict[str, Any]
    approval_required: bool
    approved: bool
    error: Optional[str]
    timestamp: datetime
    metadata: Dict[str, Any]


class RemediationAgent:
    """
    LangGraph-based agent for automated remediation of thread issues
    Can kill threads, cancel operations, or restart Integration Server
    """
    
    def __init__(self, server_url: Optional[str] = None, auto_approve: bool = False):
        """
        Initialize the remediation agent
        
        Args:
            server_url: Optional server URL (uses config if not provided)
            auto_approve: If True, automatically approve safe actions
        """
        self.config = config
        self.server_url = server_url or self.config.WEBMETHODS_URL
        self.auto_approve = auto_approve
        self.memory = MemorySaver()
        self.graph = self._create_graph()
        
        # API endpoints for remediation
        self.api_endpoints = {
            "kill_thread": "/invoke/wm.server/killThread",
            "cancel_service": "/invoke/wm.server/cancelService",
            "restart_server": "/invoke/wm.server/shutdown",
            "thread_pool": "/invoke/wm.server/setThreadPoolSettings",
            "clear_cache": "/invoke/wm.server/clearCache",
            "force_gc": "/invoke/wm.server/forceGC",
            "server_stats": "/invoke/wm.server/getServerStats"
        }
        
        # Safe actions that can be auto-approved
        self.safe_actions = {
            RemediationType.FORCE_GC,
            RemediationType.CLEAR_CACHE,
            RemediationType.NO_ACTION
        }
    
    def _create_graph(self) -> StateGraph:
        """Create LangGraph workflow for remediation"""
        workflow = StateGraph(RemediationState)
        
        # Add nodes
        workflow.add_node("analyze_issue", self.analyze_issue)
        workflow.add_node("recommend_actions", self.recommend_actions)
        workflow.add_node("select_action", self.select_action)
        workflow.add_node("request_approval", self.request_approval)
        workflow.add_node("execute_action", self.execute_action)
        workflow.add_node("verify_result", self.verify_result)
        workflow.add_node("handle_error", self.handle_error)
        
        # Define workflow
        workflow.set_entry_point("analyze_issue")
        
        # Analysis -> Recommendations
        workflow.add_conditional_edges(
            "analyze_issue",
            self._check_analysis_status,
            {
                "success": "recommend_actions",
                "error": "handle_error"
            }
        )
        
        # Recommendations -> Selection
        workflow.add_edge("recommend_actions", "select_action")
        
        # Selection -> Approval or Execution
        workflow.add_conditional_edges(
            "select_action",
            self._check_approval_needed,
            {
                "needs_approval": "request_approval",
                "auto_approve": "execute_action",
                "no_action": END
            }
        )
        
        # Approval -> Execution or End
        workflow.add_conditional_edges(
            "request_approval",
            self._check_approval_status,
            {
                "approved": "execute_action",
                "rejected": END
            }
        )
        
        # Execution -> Verification
        workflow.add_conditional_edges(
            "execute_action",
            self._check_execution_status,
            {
                "success": "verify_result",
                "error": "handle_error"
            }
        )
        
        # Verification -> End
        workflow.add_edge("verify_result", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    def analyze_issue(self, state: RemediationState) -> RemediationState:
        """
        Analyze the thread issue to determine severity and impact
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with analysis
        """
        print("[1/6] Analyzing thread issue...")
        
        try:
            analysis = state["analysis_result"]
            thread = state["thread_info"]
            
            # Determine severity
            severity = AlertSeverity.INFO
            
            if thread:
                if thread.is_hung():
                    severity = AlertSeverity.HIGH
                    if thread.cpu_time > 600:  # 10 minutes
                        severity = AlertSeverity.CRITICAL
                
                if thread.is_blocked():
                    if thread.blocked_count > 10:
                        severity = AlertSeverity.HIGH
                    else:
                        severity = AlertSeverity.MEDIUM
            
            # Check for deadlocks
            if analysis.get("deadlocks") and len(analysis["deadlocks"]) > 0:
                severity = AlertSeverity.CRITICAL
            
            # Check system metrics
            if analysis.get("cpu_usage", 0) > 90:
                severity = AlertSeverity.HIGH
            
            if analysis.get("memory_usage", 0) > 90:
                severity = AlertSeverity.CRITICAL
            
            state["metadata"]["severity"] = severity.value
            state["metadata"]["analysis_complete"] = True
            
            print(f"+ Analysis complete - Severity: {severity.value.upper()}")
            
        except Exception as e:
            state["error"] = f"Analysis error: {str(e)}"
            state["metadata"]["analysis_complete"] = False
        
        return state
    
    def recommend_actions(self, state: RemediationState) -> RemediationState:
        """
        Recommend remediation actions based on analysis
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with recommended actions
        """
        print("[2/6] Recommending remediation actions...")
        
        try:
            thread = state["thread_info"]
            analysis = state["analysis_result"]
            severity = state["metadata"].get("severity", "info")
            
            actions = []
            
            # Hung thread recommendations
            if thread and thread.is_hung():
                if thread.cpu_time > 600:  # 10+ minutes
                    actions.append(RemediationAction(
                        action_type=RemediationType.KILL_THREAD.value,
                        description=f"Kill hung thread '{thread.name}' (CPU time: {thread.cpu_time:.2f}s)",
                        priority=1,
                        estimated_impact="High - Will terminate the thread immediately",
                        steps=[
                            f"Identify thread: {thread.thread_id}",
                            "Call killThread API",
                            "Verify thread termination",
                            "Monitor for side effects"
                        ],
                        risks=[
                            "May cause incomplete transactions",
                            "Could affect dependent operations",
                            "Requires monitoring after execution"
                        ]
                    ))
                else:
                    actions.append(RemediationAction(
                        action_type=RemediationType.CANCEL_OPERATION.value,
                        description=f"Cancel operation for thread '{thread.name}'",
                        priority=2,
                        estimated_impact="Medium - Will attempt graceful cancellation",
                        steps=[
                            "Identify running service",
                            "Call cancelService API",
                            "Wait for graceful shutdown",
                            "Verify cancellation"
                        ],
                        risks=[
                            "May not cancel immediately",
                            "Service may need to complete current operation"
                        ]
                    ))
            
            # Deadlock recommendations
            if analysis.get("deadlocks") and len(analysis["deadlocks"]) > 0:
                actions.append(RemediationAction(
                    action_type=RemediationType.RESTART_SERVER.value,
                    description="Restart Integration Server to resolve deadlock",
                    priority=1,
                    estimated_impact="Critical - Will restart entire server",
                    steps=[
                        "Notify all users",
                        "Drain active connections",
                        "Call shutdown API with restart flag",
                        "Wait for server restart",
                        "Verify server health"
                    ],
                    risks=[
                        "Service downtime (2-5 minutes)",
                        "All active sessions will be terminated",
                        "In-flight transactions will be lost"
                    ]
                ))
            
            # High CPU recommendations
            if analysis.get("cpu_usage", 0) > 90:
                actions.append(RemediationAction(
                    action_type=RemediationType.FORCE_GC.value,
                    description="Force garbage collection to free memory",
                    priority=3,
                    estimated_impact="Low - May temporarily pause processing",
                    steps=[
                        "Call forceGC API",
                        "Monitor memory usage",
                        "Verify GC completion"
                    ],
                    risks=[
                        "Brief pause in processing",
                        "May not resolve underlying issue"
                    ]
                ))
            
            # High memory recommendations
            if analysis.get("memory_usage", 0) > 85:
                actions.append(RemediationAction(
                    action_type=RemediationType.CLEAR_CACHE.value,
                    description="Clear server cache to free memory",
                    priority=3,
                    estimated_impact="Low - May affect performance temporarily",
                    steps=[
                        "Call clearCache API",
                        "Monitor memory usage",
                        "Verify cache cleared"
                    ],
                    risks=[
                        "Temporary performance degradation",
                        "Cache will need to rebuild"
                    ]
                ))
            
            # Thread pool recommendations
            if analysis.get("thread_pool_exhausted", False):
                actions.append(RemediationAction(
                    action_type=RemediationType.INCREASE_THREAD_POOL.value,
                    description="Increase thread pool size",
                    priority=2,
                    estimated_impact="Medium - Will increase resource usage",
                    steps=[
                        "Get current thread pool settings",
                        "Calculate new pool size",
                        "Update thread pool settings",
                        "Monitor thread usage"
                    ],
                    risks=[
                        "Increased memory usage",
                        "May mask underlying issues"
                    ]
                ))
            
            # No action needed
            if not actions:
                actions.append(RemediationAction(
                    action_type=RemediationType.NO_ACTION.value,
                    description="No immediate action required - continue monitoring",
                    priority=4,
                    estimated_impact="None",
                    steps=["Continue monitoring", "Review logs"],
                    risks=[]
                ))
            
            # Sort by priority
            actions.sort(key=lambda x: x.priority)
            
            state["recommended_actions"] = actions
            state["metadata"]["action_count"] = len(actions)
            
            print(f"+ Recommended {len(actions)} actions")
            for i, action in enumerate(actions, 1):
                print(f"   {i}. {action.description} (Priority: {action.priority})")
            
        except Exception as e:
            state["error"] = f"Recommendation error: {str(e)}"
        
        return state
    
    def select_action(self, state: RemediationState) -> RemediationState:
        """
        Select the best remediation action
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with selected action
        """
        print("[3/6] Selecting remediation action...")
        
        try:
            actions = state["recommended_actions"]
            
            if not actions:
                state["selected_action"] = RemediationType.NO_ACTION
                state["approval_required"] = False
                print("+ No action required")
                return state
            
            # Select highest priority action
            selected = actions[0]
            action_type = RemediationType(selected.action_type)
            
            state["selected_action"] = action_type
            
            # Determine if approval is needed
            if action_type in self.safe_actions or self.auto_approve:
                state["approval_required"] = False
                state["approved"] = True
                print(f"+ Selected: {selected.description} (Auto-approved)")
            else:
                state["approval_required"] = True
                state["approved"] = False
                print(f"+ Selected: {selected.description} (Requires approval)")
            
            state["metadata"]["selected_action"] = selected.to_dict()
            
        except Exception as e:
            state["error"] = f"Selection error: {str(e)}"
        
        return state
    
    def request_approval(self, state: RemediationState) -> RemediationState:
        """
        Request approval for remediation action
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with approval status
        """
        print("[4/6] Requesting approval for remediation...")
        
        try:
            action = state["metadata"]["selected_action"]
            
            print("\n" + "=" * 70)
            print("REMEDIATION APPROVAL REQUIRED")
            print("=" * 70)
            print(f"Action: {action['description']}")
            print(f"Priority: {action['priority']}")
            print(f"Impact: {action['estimated_impact']}")
            print("\nSteps:")
            for i, step in enumerate(action['steps'], 1):
                print(f"  {i}. {step}")
            print("\nRisks:")
            for risk in action['risks']:
                print(f"  ! {risk}")
            print("=" * 70)
            
            # In production, this would integrate with approval system
            # For now, we'll simulate approval based on severity
            severity = state["metadata"].get("severity", "info")
            
            if severity in ["critical", "high"]:
                # Auto-approve critical/high severity issues
                state["approved"] = True
                print("+ Auto-approved due to high severity")
            else:
                # Would normally wait for human approval
                state["approved"] = False
                print("⏳ Waiting for manual approval...")
            
        except Exception as e:
            state["error"] = f"Approval error: {str(e)}"
        
        return state
    
    def execute_action(self, state: RemediationState) -> RemediationState:
        """
        Execute the selected remediation action
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with execution result
        """
        print("[5/6] Executing remediation action...")
        
        try:
            action_type = state["selected_action"]
            thread = state["thread_info"]
            
            result = {
                "action": action_type.value,
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "details": {}
            }
            
            # Execute based on action type
            if action_type == RemediationType.KILL_THREAD:
                result["details"] = self._kill_thread(thread)
                print(f"+ Thread killed: {thread.name}")
            
            elif action_type == RemediationType.CANCEL_OPERATION:
                result["details"] = self._cancel_operation(thread)
                print(f"+ Operation cancelled: {thread.name}")
            
            elif action_type == RemediationType.RESTART_SERVER:
                result["details"] = self._restart_server()
                print("+ Server restart initiated")
            
            elif action_type == RemediationType.INCREASE_THREAD_POOL:
                result["details"] = self._increase_thread_pool()
                print("+ Thread pool increased")
            
            elif action_type == RemediationType.CLEAR_CACHE:
                result["details"] = self._clear_cache()
                print("+ Cache cleared")
            
            elif action_type == RemediationType.FORCE_GC:
                result["details"] = self._force_gc()
                print("+ Garbage collection forced")
            
            elif action_type == RemediationType.NO_ACTION:
                result["details"] = {"message": "No action taken"}
                print("+ No action required")
            
            state["execution_result"] = result
            state["metadata"]["execution_status"] = "success"
            
        except Exception as e:
            state["error"] = f"Execution error: {str(e)}"
            state["metadata"]["execution_status"] = "failed"
            state["execution_result"] = {
                "action": state["selected_action"].value if state["selected_action"] else "unknown",
                "status": "failed",
                "error": str(e)
            }
        
        return state
    
    def verify_result(self, state: RemediationState) -> RemediationState:
        """
        Verify the remediation was successful
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with verification result
        """
        print("[6/6] Verifying remediation result...")
        
        try:
            action_type = state["selected_action"]
            
            # Get current server stats
            stats_url = f"{state['server_url']}{self.api_endpoints['server_stats']}"
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
                state["metadata"]["post_action_stats"] = stats
                print("+ Verification complete - Server responding normally")
            else:
                print("! Could not verify - Server may be restarting")
            
            state["metadata"]["verification_status"] = "complete"
            
        except Exception as e:
            print(f"! Verification warning: {str(e)}")
            # Don't fail the workflow for verification errors
        
        return state
    
    def handle_error(self, state: RemediationState) -> RemediationState:
        """Handle errors in the workflow"""
        print(f"\nX Error occurred: {state['error']}")
        state["metadata"]["final_status"] = "failed"
        return state
    
    # Helper methods for executing actions
    
    def _kill_thread(self, thread: ThreadInfo) -> Dict[str, Any]:
        """Kill a specific thread"""
        url = f"{self.server_url}{self.api_endpoints['kill_thread']}"
        response = requests.post(
            url,
            json={"threadId": thread.thread_id},
            auth=self.config.get_webmethods_auth(),
            timeout=30,
            verify=False
        )
        return {"status_code": response.status_code, "response": response.text}
    
    def _cancel_operation(self, thread: ThreadInfo) -> Dict[str, Any]:
        """Cancel operation for a thread"""
        url = f"{self.server_url}{self.api_endpoints['cancel_service']}"
        response = requests.post(
            url,
            json={"threadId": thread.thread_id},
            auth=self.config.get_webmethods_auth(),
            timeout=30,
            verify=False
        )
        return {"status_code": response.status_code, "response": response.text}
    
    def _restart_server(self) -> Dict[str, Any]:
        """Restart the Integration Server"""
        url = f"{self.server_url}{self.api_endpoints['restart_server']}"
        response = requests.post(
            url,
            json={"restart": True, "timeout": 60},
            auth=self.config.get_webmethods_auth(),
            timeout=30,
            verify=False
        )
        return {"status_code": response.status_code, "response": response.text}
    
    def _increase_thread_pool(self) -> Dict[str, Any]:
        """Increase thread pool size"""
        url = f"{self.server_url}{self.api_endpoints['thread_pool']}"
        response = requests.post(
            url,
            json={"maxThreads": 200, "minThreads": 50},
            auth=self.config.get_webmethods_auth(),
            timeout=30,
            verify=False
        )
        return {"status_code": response.status_code, "response": response.text}
    
    def _clear_cache(self) -> Dict[str, Any]:
        """Clear server cache"""
        url = f"{self.server_url}{self.api_endpoints['clear_cache']}"
        response = requests.post(
            url,
            auth=self.config.get_webmethods_auth(),
            timeout=30,
            verify=False
        )
        return {"status_code": response.status_code, "response": response.text}
    
    def _force_gc(self) -> Dict[str, Any]:
        """Force garbage collection"""
        url = f"{self.server_url}{self.api_endpoints['force_gc']}"
        response = requests.post(
            url,
            auth=self.config.get_webmethods_auth(),
            timeout=30,
            verify=False
        )
        return {"status_code": response.status_code, "response": response.text}
    
    # Conditional edge functions
    
    def _check_analysis_status(self, state: RemediationState) -> str:
        """Check analysis status"""
        return "success" if state["metadata"].get("analysis_complete") else "error"
    
    def _check_approval_needed(self, state: RemediationState) -> str:
        """Check if approval is needed"""
        if state["selected_action"] == RemediationType.NO_ACTION:
            return "no_action"
        return "auto_approve" if not state["approval_required"] else "needs_approval"
    
    def _check_approval_status(self, state: RemediationState) -> str:
        """Check approval status"""
        return "approved" if state["approved"] else "rejected"
    
    def _check_execution_status(self, state: RemediationState) -> str:
        """Check execution status"""
        return "success" if state["metadata"].get("execution_status") == "success" else "error"
    
    def run(
        self,
        thread_info: Optional[ThreadInfo] = None,
        analysis_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the remediation workflow
        
        Args:
            thread_info: Optional thread information
            analysis_result: Optional analysis result
        
        Returns:
            Final workflow state as dictionary
        """
        print("=" * 70)
        print("Thread Dump Remediation Workflow - LangGraph Agent")
        print("=" * 70)
        
        # Initialize state
        initial_state: RemediationState = {
            "server_url": self.server_url,
            "auth_credentials": {
                "username": self.config.WEBMETHODS_USER,
                "password": self.config.WEBMETHODS_PASSWORD
            },
            "thread_info": thread_info,
            "analysis_result": analysis_result or {},
            "recommended_actions": [],
            "selected_action": None,
            "execution_result": {},
            "approval_required": False,
            "approved": False,
            "error": None,
            "timestamp": datetime.now(),
            "metadata": {
                "workflow_start": datetime.now().isoformat(),
                "auto_approve": self.auto_approve
            }
        }
        
        # Execute workflow
        try:
            # Add thread_id for checkpointer
            config = {"configurable": {"thread_id": "remediation_1"}}
            result = self.graph.invoke(initial_state, config)
            
            # Print summary
            print("\n" + "=" * 70)
            if result.get("error"):
                print("X Remediation Failed")
                print(f"Error: {result['error']}")
            else:
                print("+ Remediation Complete")
                if result.get("execution_result"):
                    exec_result = result["execution_result"]
                    print(f"Action: {exec_result.get('action', 'N/A')}")
                    print(f"Status: {exec_result.get('status', 'N/A')}")
            print("=" * 70)
            
            return result
        
        except Exception as e:
            print(f"\nX Workflow execution failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"error": str(e), "metadata": {"final_status": "failed"}}


def main():
    """Main entry point for remediation agent"""
    print("Thread Dump Remediation Agent - LangGraph Implementation")
    print("Team Member: Sai\n")
    
    # Example usage with sample thread
    from shared.models import ThreadInfo
    
    sample_thread = ThreadInfo(
        thread_id="0x00007f8a1c001000",
        name="HTTP Handler - Hung Thread",
        state="RUNNABLE",
        cpu_time=650.0,  # 10+ minutes - hung thread
        blocked_count=0
    )
    
    sample_analysis = {
        "cpu_usage": 85.0,
        "memory_usage": 75.0,
        "deadlocks": [],
        "thread_pool_exhausted": False
    }
    
    # Create and run remediation agent
    agent = RemediationAgent(auto_approve=True)
    result = agent.run(
        thread_info=sample_thread,
        analysis_result=sample_analysis
    )
    
    # Exit with appropriate code
    exit(0 if not result.get("error") else 1)


if __name__ == "__main__":
    main()

# Made with Bob
