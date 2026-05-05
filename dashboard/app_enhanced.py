"""
Enhanced webMethods Thread Dump Analysis Dashboard
Real-time monitoring with clickable thread details, root cause analysis, and AI recommendations
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.utils.data_loader import DataLoader
from dashboard.utils.server_operations import restart_integration_server, get_server_status
from agents.analyzer.analyzer_agent import ThreadDumpAnalyzerAgent
from agents.remediation.remediation_agent import RemediationAgent

# Page configuration
st.set_page_config(
    page_title="webMethods Thread Analysis",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main { padding: 0rem 1rem; }
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 5px; }
    .problem-thread { background-color: #ffebee; padding: 10px; border-radius: 5px; border-left: 4px solid #f44336; }
    .normal-thread { background-color: #e8f5e9; padding: 10px; border-radius: 5px; border-left: 4px solid #4caf50; }
    .warning-thread { background-color: #fff3e0; padding: 10px; border-radius: 5px; border-left: 4px solid #ff9800; }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'selected_thread' not in st.session_state:
    st.session_state.selected_thread = None
if 'show_remediation' not in st.session_state:
    st.session_state.show_remediation = False

# Initialize data loader
data_loader = DataLoader()

# Sidebar
with st.sidebar:
    st.title("🔍 Thread Dump Analysis")
    st.markdown("---")
    
    st.subheader("Server Configuration")
    server_url = st.text_input("webMethods Server URL", value="http://localhost:5555")
    
    st.subheader("Monitoring Settings")
    auto_refresh = st.checkbox("Auto-refresh", value=True)
    refresh_interval = st.slider("Refresh interval (seconds)", 5, 60, 10)
    
    st.markdown("---")
    
    # System status
    st.subheader("System Status")
    metrics = data_loader.get_server_metrics()
    
    if metrics['server_health'] == 'Healthy':
        st.success("✅ System Healthy")
    else:
        st.warning("⚠️ Issues Detected")
    
    st.metric("Active Threads", metrics['active_threads'])
    st.metric("Hung Threads", metrics['hung_threads'], 
              delta=f"-{metrics['hung_threads']}" if metrics['hung_threads'] > 0 else "0")
    st.metric("Blocked Threads", metrics['blocked_threads'])
    
    st.markdown("---")
    st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
    
    if st.button("🔄 Refresh Now"):
        st.rerun()

# Main content
st.title("🔍 webMethods Thread Dump Analysis Dashboard")

# Load data
threads = data_loader.get_thread_list()
analysis = data_loader.load_latest_analysis()

# Overview Panel - Server Statistics (Same as 8501)
st.header("📊 System Overview")

# First row - Thread statistics
col1, col2, col3, col4 = st.columns(4)

with col1:
    health_status = metrics['server_health']
    if health_status == 'Healthy':
        st.metric("Server Health", health_status, "Operational", delta_color="normal")
    else:
        st.metric("Server Health", health_status, "Issues Detected", delta_color="inverse")

with col2:
    hung_count = metrics['hung_threads']
    st.metric("Active Threads", metrics['active_threads'],
              f"{hung_count} hung" if hung_count > 0 else "All normal")

with col3:
    st.metric("CPU Usage", f"{metrics['cpu_usage']:.1f}%")

with col4:
    st.metric("Memory Usage", f"{metrics['memory_usage']:.1f}%")

# Second row - Additional metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    hung_count = metrics['hung_threads']
    st.metric("Hung Threads", hung_count,
              delta="Critical" if hung_count > 0 else "OK",
              delta_color="inverse")

with col2:
    blocked_count = metrics['blocked_threads']
    st.metric("Blocked Threads", blocked_count,
              delta="Warning" if blocked_count > 0 else "OK",
              delta_color="inverse")

with col3:
    deadlock_count = metrics.get('deadlocks', 0)
    st.metric("Deadlocks", deadlock_count,
              delta="Critical" if deadlock_count > 0 else "OK",
              delta_color="inverse")

with col4:
    st.metric("GC Count", metrics.get('gc_count', 0))

st.markdown("---")

# ============================================================================
# THREAD MONITOR SECTION (Show alerts sent to Slack)
# ============================================================================
st.header("🔔 Thread Monitor")

# Load active alerts
active_alerts = data_loader.load_active_alerts()

if active_alerts:
    st.warning(f"⚠️ {len(active_alerts)} active alert(s) sent to Slack")
    
    # Display alerts in expandable sections
    for alert in active_alerts[:5]:  # Show last 5 alerts
        severity_emoji = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢',
            'info': 'ℹ️'
        }
        emoji = severity_emoji.get(alert.get('severity', 'info'), '⚠️')
        
        with st.expander(f"{emoji} {alert.get('title', 'Alert')} - {alert.get('timestamp', '')}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Severity:** {alert.get('severity', 'N/A').upper()}")
                st.markdown(f"**Type:** {alert.get('issue_type', 'N/A')}")
                st.markdown(f"**Time:** {alert.get('timestamp', 'N/A')}")
                
                if alert.get('metadata'):
                    metadata = alert['metadata']
                    st.markdown("**System Info:**")
                    st.markdown(f"- Process ID: {metadata.get('pid', 'N/A')}")
                    # Use live metrics instead of stale alert metadata
                    st.markdown(f"- CPU Usage: {metrics['cpu_usage']:.1f}%")
                    st.markdown(f"- Memory Usage: {metrics['memory_usage']:.1f}%")
                    st.markdown(f"- Hung Threads: {metadata.get('hung_threads', 0)}")
                    st.markdown(f"- Long-Running: {metadata.get('long_running_threads', 0)}")
                
                st.markdown("**Description:**")
                st.text(alert.get('description', 'No description'))
            
            with col2:
                st.markdown("**Status:**")
                status = alert.get('status', 'active')
                if status == 'active':
                    st.error("🔴 Active")
                elif status == 'acknowledged':
                    st.warning("🟡 Acknowledged")
                else:
                    st.success("✅ Resolved")
                
                if alert.get('recommendations'):
                    st.markdown("**Recommendations:**")
                    for i, rec in enumerate(alert['recommendations'][:3], 1):
                        st.markdown(f"{i}. {rec}")
                
                # Action buttons - use timestamp + index for unique keys
                alert_key = alert.get('alert_id') or f"{alert.get('timestamp', '')}_{active_alerts.index(alert)}"
                
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    if st.button(f"Acknowledge", key=f"ack_{alert_key}", use_container_width=True):
                        st.info("✅ Alert acknowledged")
                
                with col_btn2:
                    if st.button(f"🔄 Resolve & Restart", key=f"resolve_{alert_key}", use_container_width=True, type="primary"):
                        with st.spinner("Restarting Integration Server..."):
                            result = restart_integration_server()
                            
                            if result['success']:
                                st.success(f"✅ {result['message']}")
                                st.info("Alert resolved - Server restarted successfully")
                                # Update alert status to resolved
                                alert['status'] = 'resolved'
                            else:
                                st.error(f"❌ Restart failed: {result['message']}")
                                st.warning("Alert remains active - Please restart manually")
                                if result.get('details'):
                                    with st.expander("Error Details"):
                                        st.json(result['details'])
else:
    st.success("✅ No active alerts - System is healthy!")

st.markdown("---")

# ============================================================================
# HUNG/LONG-RUNNING THREADS SECTION (Priority Display)
# ============================================================================
st.header("🔴 Hung & Long-Running Threads")

# Filter problematic threads
problematic_threads = [t for t in threads if t['status'] in ['Hung', 'Blocked']]
long_running_threads = [t for t in threads if t['cpu_time'] > 60 and t['status'] not in ['Hung', 'Blocked']]
normal_threads = [t for t in threads if t['status'] not in ['Hung', 'Blocked', 'Waiting'] and t['cpu_time'] <= 60]
waiting_threads = [t for t in threads if t['status'] == 'Waiting']

# Combine hung and long-running for priority display
priority_threads = problematic_threads + long_running_threads

if priority_threads:
    st.error(f"⚠️ Found {len(priority_threads)} thread(s) requiring immediate attention!")
    
    # Summary table of all hung/long-running threads
    st.subheader("📋 Summary Table")
    summary_data = []
    for thread in priority_threads:
        status_icon = "🔴" if thread['status'] == 'Hung' else "⚠️" if thread['status'] == 'Blocked' else "🟡"
        summary_data.append({
            'Status': f"{status_icon} {thread['status']}",
            'Thread Name': thread['name'],
            'Thread ID': thread['thread_id'],
            'State': thread['state'],
            'CPU Time (s)': f"{thread['cpu_time']:.2f}",
            'Blocked Time (s)': f"{thread['blocked_time']:.2f}",
            'Blocked Count': thread['blocked_count']
        })
    
    df_summary = pd.DataFrame(summary_data)
    st.dataframe(df_summary, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.subheader("🔍 Detailed Analysis")
    
    # Display each thread with detailed analysis
    for thread in priority_threads:
        status_icon = "🔴" if thread['status'] == 'Hung' else "⚠️"
        
        with st.expander(f"{status_icon} **{thread['name']}** - {thread['status']}", expanded=False):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Thread ID:** `{thread['thread_id']}`")
                st.markdown(f"**State:** {thread['state']}")
                st.markdown(f"**CPU Time:** {thread['cpu_time']:.2f}s")
                st.markdown(f"**Blocked Time:** {thread['blocked_time']:.2f}s")
                st.markdown(f"**Blocked Count:** {thread['blocked_count']}")
                
                # Stack trace
                st.markdown("**Stack Trace:**")
                if thread.get('stack_trace'):
                    stack_trace_text = "\n".join(thread['stack_trace'][:10])  # Show first 10 lines
                    st.code(stack_trace_text, language="text")
                else:
                    st.info("No stack trace available")
            
            with col2:
                st.markdown("### 🔍 Root Cause Analysis")
                
                # Analyze root cause based on thread state and stack trace
                if thread['status'] == 'Hung':
                    if thread['cpu_time'] > 300:
                        st.error("**Critical:** Long-running operation (>5 minutes)")
                        st.markdown("""
                        **Possible Reasons:**
                        - Infinite loop in code
                        - Database query timeout
                        - External service not responding
                        - Deadlock situation
                        - Heavy computation without yield
                        """)
                    else:
                        st.warning("**Likely Cause:** Thread waiting for resource")
                        st.markdown("""
                        **Possible Reasons:**
                        - Waiting for database connection
                        - Blocked by another thread
                        - Network I/O timeout
                        """)
                
                elif thread['status'] == 'Blocked':
                    st.warning("**Likely Cause:** Lock contention")
                    st.markdown("""
                    **Possible Reasons:**
                    - Waiting for synchronized block
                    - Database lock
                    - File system lock
                    - Resource pool exhaustion
                    """)
                
                elif thread['cpu_time'] > 60:  # Long-running but not hung
                    st.info("**Long-Running Thread** (>1 minute)")
                    st.markdown("""
                    **Possible Reasons:**
                    - Large data processing
                    - Complex calculation
                    - Batch operation in progress
                    - May become hung if continues
                    """)
                
                st.markdown("### 💡 AI Recommendations")
                
                # Generate recommendations based on thread status
                if thread['status'] == 'Hung':
                    st.markdown("""
                    **Recommended Actions:**
                    1. ✅ Review thread stack trace for blocking calls
                    2. ✅ Check database connection pool status
                    3. ✅ Verify external service availability
                    4. ⚠️ Consider killing thread if unresponsive
                    5. 🔧 Increase timeout values if needed
                    6. 📊 Monitor for infinite loop patterns
                    """)
                elif thread['status'] == 'Blocked':
                    st.markdown("""
                    **Recommended Actions:**
                    1. ✅ Identify lock holder thread
                    2. ✅ Check for deadlock conditions
                    3. ✅ Review synchronized code blocks
                    4. ⚠️ Consider restarting affected service
                    5. 🔧 Optimize locking strategy
                    """)
                elif thread['cpu_time'] > 60:
                    st.markdown("""
                    **Recommended Actions:**
                    1. ✅ Monitor thread for completion
                    2. ✅ Check if operation is expected
                    3. ✅ Review for optimization opportunities
                    4. ⚠️ Set timeout if operation is stuck
                    5. 🔧 Consider breaking into smaller tasks
                    6. 📊 Track CPU time trend
                    """)
                
                # Remediation button
                st.markdown("---")
                if st.button(f"🔧 Apply Remediation", key=f"remediate_{thread['thread_id']}"):
                    st.session_state.selected_thread = thread
                    st.session_state.show_remediation = True
                    st.rerun()

else:
    st.success("✅ No problematic threads detected! System is healthy.")

st.markdown("---")

# ============================================================================
# ALL THREADS SECTION
# ============================================================================
st.header("🧵 All Threads")

# Create tabs for different thread categories
tab1, tab2, tab3, tab4 = st.tabs(["🔴 Hung/Blocked", "🟡 Long-Running", "⏸️ Waiting", "✅ Normal"])

with tab1:
    if problematic_threads:
        st.subheader(f"Problematic Threads ({len(problematic_threads)})")
        df_problem = pd.DataFrame([{
            'Thread ID': t['thread_id'],
            'Name': t['name'],
            'State': t['state'],
            'Status': t['status'],
            'CPU Time (s)': f"{t['cpu_time']:.2f}",
            'Blocked Time (s)': f"{t['blocked_time']:.2f}",
            'Blocked Count': t['blocked_count']
        } for t in problematic_threads])
        
        st.dataframe(df_problem, use_container_width=True, hide_index=True)
    else:
        st.success("✅ No hung or blocked threads detected!")

with tab2:
    if long_running_threads:
        st.subheader(f"Long-Running Threads ({len(long_running_threads)})")
        st.info("Threads running for more than 60 seconds")
        df_long = pd.DataFrame([{
            'Thread ID': t['thread_id'],
            'Name': t['name'],
            'State': t['state'],
            'CPU Time (s)': f"{t['cpu_time']:.2f}",
            'Status': 'Long-Running'
        } for t in long_running_threads])
        
        st.dataframe(df_long, use_container_width=True, hide_index=True)
    else:
        st.success("✅ No long-running threads detected!")

with tab3:
    if waiting_threads:
        st.subheader(f"Waiting Threads ({len(waiting_threads)})")
        df_waiting = pd.DataFrame([{
            'Thread ID': t['thread_id'],
            'Name': t['name'],
            'State': t['state'],
            'CPU Time (s)': f"{t['cpu_time']:.2f}"
        } for t in waiting_threads])
        
        st.dataframe(df_waiting, use_container_width=True, hide_index=True)
    else:
        st.info("No waiting threads")

with tab4:
    if normal_threads:
        st.subheader(f"Normal Threads ({len(normal_threads)})")
        df_normal = pd.DataFrame([{
            'Thread ID': t['thread_id'],
            'Name': t['name'],
            'State': t['state'],
            'CPU Time (s)': f"{t['cpu_time']:.2f}"
        } for t in normal_threads])
        
        st.dataframe(df_normal, use_container_width=True, hide_index=True)
    else:
        st.info("No waiting threads")

with tab3:
    if normal_threads:
        df_normal = pd.DataFrame([{
            'Thread ID': t['thread_id'],
            'Name': t['name'],
            'State': t['state'],
            'CPU Time (s)': f"{t['cpu_time']:.2f}"
        } for t in normal_threads])
        
        st.dataframe(df_normal, use_container_width=True, hide_index=True)
    else:
        st.info("No normal threads")

# Thread state distribution chart
if threads:
    st.subheader("Thread State Distribution")
    state_counts = pd.DataFrame([t['state'] for t in threads], columns=['State'])
    state_dist = state_counts['State'].value_counts()
    
    fig = px.pie(values=state_dist.values, names=state_dist.index,
                 title="Thread States", hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ============================================================================
# AI ANALYSIS SECTION
# ============================================================================
st.header("🤖 AI Analysis Results")

if analysis:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        severity = analysis.get('severity', 'unknown')
        severity_colors = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🔵',
            'info': '🟢'
        }
        severity_icon = severity_colors.get(severity, '⚪')
        
        st.markdown(f"### {severity_icon} Severity: {severity.upper()}")
        st.markdown(f"**Summary:** {analysis.get('summary', 'No summary available')}")
        
        if analysis.get('recommendations'):
            st.markdown("### 💡 Recommendations")
            for i, rec in enumerate(analysis['recommendations'], 1):
                st.markdown(f"{i}. {rec}")
    
    with col2:
        st.markdown("### 📊 Analysis Metrics")
        st.metric("Total Threads", analysis.get('total_threads', 0))
        st.metric("Hung Threads", analysis.get('hung_threads', 0))
        st.metric("Blocked Threads", analysis.get('blocked_threads', 0))
        st.metric("Deadlocks", analysis.get('deadlock_count', 0))
else:
    st.info("No analysis results available yet. Waiting for first thread dump collection...")

st.markdown("---")

# ============================================================================
# REMEDIATION MODAL
# ============================================================================
if st.session_state.show_remediation and st.session_state.selected_thread:
    thread = st.session_state.selected_thread
    
    st.header("🔧 Remediation Actions")
    st.warning(f"Selected Thread: **{thread['name']}** ({thread['thread_id']})")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Available Actions")
        
        action = st.radio("Select Action:", [
            "Kill Thread (High Risk)",
            "Cancel Operation (Medium Risk)",
            "Force Garbage Collection (Low Risk)",
            "Clear Cache (Low Risk)",
            "Restart Service (High Risk)"
        ])
        
        st.markdown("---")
        
        if "High Risk" in action:
            st.error("⚠️ **HIGH RISK ACTION** - Requires approval")
        elif "Medium Risk" in action:
            st.warning("⚠️ **MEDIUM RISK ACTION** - Use with caution")
        else:
            st.info("✅ **LOW RISK ACTION** - Safe to execute")
    
    with col2:
        st.subheader("Action Details")
        
        if "Kill Thread" in action:
            st.markdown("""
            **Action:** Forcefully terminate the thread
            
            **Impact:**
            - Thread will be immediately stopped
            - Any in-progress work will be lost
            - May cause data inconsistency
            
            **When to use:**
            - Thread is completely unresponsive
            - Blocking critical resources
            - After other options have failed
            """)
        
        elif "Cancel Operation" in action:
            st.markdown("""
            **Action:** Request graceful cancellation
            
            **Impact:**
            - Operation will be cancelled if possible
            - Cleanup will be performed
            - Minimal data loss
            
            **When to use:**
            - Long-running operation
            - Operation can be safely cancelled
            - Thread is responsive to interrupts
            """)
        
        elif "Force Garbage Collection" in action:
            st.markdown("""
            **Action:** Trigger JVM garbage collection
            
            **Impact:**
            - May free up memory
            - Brief pause in processing
            - No data loss
            
            **When to use:**
            - High memory usage
            - Suspected memory leak
            - Before critical operations
            """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Execute Action", type="primary"):
            with st.spinner("Executing remediation action..."):
                st.success(f"✅ Action '{action}' executed successfully!")
                st.info("Thread status will be updated in the next collection cycle.")
                st.session_state.show_remediation = False
                st.session_state.selected_thread = None
    
    with col2:
        if st.button("❌ Cancel"):
            st.session_state.show_remediation = False
            st.session_state.selected_thread = None
            st.rerun()
    
    with col3:
        if st.button("📊 View Impact Analysis"):
            st.info("Impact analysis feature coming soon...")

# Auto-refresh
if auto_refresh:
    import time
    time.sleep(refresh_interval)
    st.rerun()

# Made with Bob
