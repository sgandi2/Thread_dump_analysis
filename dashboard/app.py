"""
webMethods Thread Dump Analysis Dashboard
Real-time monitoring interface for thread dump analysis system
Author: Bhagwan
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import time
import requests

# Page configuration
st.set_page_config(
    page_title="webMethods Thread Dump Analysis",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main { padding: 0rem 1rem; }
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

# Helper functions
def load_sample_data():
    """Load sample data for demonstration"""
    return {
        'server_health': 'Healthy',
        'active_threads': 45,
        'hung_threads': 2,
        'blocked_threads': 1,
        'cpu_usage': 67.5,
        'memory_usage': 78.3,
        'gc_count': 15,
        'last_gc_time': 0.023
    }

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
    st.caption(f"Last updated: {st.session_state.last_update.strftime('%H:%M:%S')}")

# Main content
st.title("webMethods Thread Dump Analysis Dashboard")

# Load data
metrics = load_sample_data()

# Overview Panel
st.header("📊 Overview")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Server Health", metrics['server_health'], "Operational")
with col2:
    st.metric("Active Threads", metrics['active_threads'], f"{metrics['hung_threads']} hung")
with col3:
    st.metric("CPU Usage", f"{metrics['cpu_usage']:.1f}%")
with col4:
    st.metric("Memory Usage", f"{metrics['memory_usage']:.1f}%")

# ============================================================================
# AI CHAT ASSISTANT (OLLAMA)
# ============================================================================
st.markdown("---")
st.subheader("💬 AI Assistant - Ask About Thread Issues")

# Initialize chat history in session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Chat interface
with st.expander("🤖 Chat with AI Assistant (Powered by Ollama)", expanded=False):
    st.markdown("Ask questions about thread dumps, performance issues, or get recommendations.")
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_history:
            if message['role'] == 'user':
                st.markdown(f"**You:** {message['content']}")
            else:
                st.markdown(f"**AI:** {message['content']}")
    
    # Chat input
    col1, col2 = st.columns([5, 1])
    with col1:
        user_input = st.text_input("Ask a question:", key="chat_input", placeholder="e.g., Why is Thread-2 hung?")
    with col2:
        send_button = st.button("Send", type="primary")
    
    if send_button and user_input:
        # Add user message to history
        st.session_state.chat_history.append({'role': 'user', 'content': user_input})
        
        # Generate AI response using Ollama
        try:
            import requests
            
            # Show loading message
            with st.spinner('🤔 AI is thinking... (this may take 30-60 seconds)'):
                # Prepare context from current metrics
                context = f"""You are a webMethods Integration Server expert. Analyze the current system status and provide concise, actionable advice.

Current System Status:
- Server Health: {metrics['server_health']}
- Active Threads: {metrics['active_threads']}
- Hung Threads: {metrics['hung_threads']}
- CPU Usage: {metrics['cpu_usage']:.1f}%
- Memory Usage: {metrics['memory_usage']:.1f}%

User Question: {user_input}

Provide a clear, concise answer with specific recommendations."""
                
                # Call Ollama API with increased timeout
                ollama_response = requests.post(
                    'http://localhost:11434/api/generate',
                    json={
                        'model': 'llama2',
                        'prompt': context,
                        'stream': False,
                        'options': {
                            'temperature': 0.7,
                            'num_predict': 200  # Limit response length for faster replies
                        }
                    },
                    timeout=120  # Increased to 2 minutes
                )
                
                if ollama_response.status_code == 200:
                    ai_response = ollama_response.json().get('response', 'Sorry, I could not generate a response.')
                else:
                    ai_response = "⚠️ Ollama service returned an error. Please check if the model is loaded correctly."
        
        except requests.exceptions.Timeout:
            ai_response = "⏱️ Request timed out. The AI model might be loading or your system is slow. Try:\n1. Use a faster model: `ollama pull mistral`\n2. Wait a moment and try again\n3. Restart Ollama service"
        except requests.exceptions.ConnectionError:
            ai_response = "⚠️ Cannot connect to Ollama. Please start Ollama service:\n```\nollama serve\n```\nOr run: `.\setup_ollama.bat`"
        except Exception as e:
            ai_response = f"⚠️ Error: {str(e)}\n\nTo use this feature:\n1. Install Ollama: https://ollama.ai\n2. Run: `ollama pull llama2`\n3. Start: `ollama serve`"
        
        # Add AI response to history
        st.session_state.chat_history.append({'role': 'assistant', 'content': ai_response})
        
        # Rerun to update chat display
        st.rerun()
    
    # Clear chat button
    if st.button("Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()
    
    # Quick action buttons
    st.markdown("**Quick Questions:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Analyze hung threads"):
            st.session_state.chat_history.append({
                'role': 'user', 
                'content': 'Why are threads getting hung and how can I fix it?'
            })
            st.rerun()
    with col2:
        if st.button("CPU optimization tips"):
            st.session_state.chat_history.append({
                'role': 'user',
                'content': 'How can I optimize CPU usage in my application?'
            })
            st.rerun()
    with col3:
        if st.button("Memory leak detection"):
            st.session_state.chat_history.append({
                'role': 'user',
                'content': 'How do I detect and fix memory leaks?'
            })
            st.rerun()

st.markdown("---")


# ============================================================================
# SECTION 2: THREAD ANALYSIS PANEL
# ============================================================================
st.header("🧵 Thread Analysis")

# Sample thread data
thread_data = [
    {'thread_id': 'Thread-1', 'name': 'HTTP-Worker-1', 'state': 'RUNNABLE', 'cpu_time': 450.2, 'status': '✅ Normal'},
    {'thread_id': 'Thread-2', 'name': 'DB-Connection-Pool', 'state': 'WAITING', 'cpu_time': 120.5, 'status': '🔴 Hung'},
    {'thread_id': 'Thread-3', 'name': 'JMS-Listener', 'state': 'BLOCKED', 'cpu_time': 89.3, 'status': '⚠️ Blocked'},
    {'thread_id': 'Thread-4', 'name': 'Cache-Manager', 'state': 'RUNNABLE', 'cpu_time': 234.1, 'status': '✅ Normal'},
]

df_threads = pd.DataFrame(thread_data)

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Active Threads")
    st.dataframe(df_threads, use_container_width=True, hide_index=True)

with col2:
    st.subheader("Thread State Distribution")
    state_counts = df_threads['state'].value_counts()
    fig_pie = px.pie(values=state_counts.values, names=state_counts.index, 
                     title="Thread States", hole=0.4)
    st.plotly_chart(fig_pie, use_container_width=True)

# Thread details expander
with st.expander("🔍 View Thread Stack Trace"):
    selected_thread = st.selectbox("Select Thread", df_threads['thread_id'].tolist())
    st.code("""
Thread: DB-Connection-Pool (Thread-2)
State: WAITING
CPU Time: 120.5ms

Stack Trace:
  at java.lang.Object.wait(Native Method)
  at com.wm.app.b2b.server.ServiceThread.run(ServiceThread.java:245)
  at com.wm.app.b2b.server.db.ConnectionPool.getConnection(ConnectionPool.java:156)
  at com.wm.app.b2b.server.db.DBManager.execute(DBManager.java:89)
    """, language="text")

# ============================================================================
# SECTION 3: PERFORMANCE METRICS PANEL
# ============================================================================
st.header("📈 Performance Metrics")

col1, col2 = st.columns(2)

with col1:
    st.subheader("CPU Usage Over Time")
    # Generate sample time series data
    time_points = pd.date_range(end=datetime.now(), periods=20, freq='30S')
    cpu_data = pd.DataFrame({
        'Time': time_points,
        'CPU %': [45, 52, 48, 67, 72, 68, 75, 80, 78, 67, 65, 70, 73, 68, 65, 62, 58, 55, 60, 67]
    })
    
    fig_cpu = px.line(cpu_data, x='Time', y='CPU %', 
                      title='CPU Usage Trend',
                      labels={'CPU %': 'CPU Usage (%)'})
    fig_cpu.add_hline(y=80, line_dash="dash", line_color="red", 
                      annotation_text="Threshold (80%)")
    st.plotly_chart(fig_cpu, use_container_width=True)

with col2:
    st.subheader("Memory Usage Over Time")
    memory_data = pd.DataFrame({
        'Time': time_points,
        'Memory %': [65, 68, 70, 72, 75, 78, 76, 79, 81, 78, 77, 79, 80, 78, 76, 74, 72, 70, 73, 78]
    })
    
    fig_mem = px.line(memory_data, x='Time', y='Memory %',
                      title='Memory Usage Trend',
                      labels={'Memory %': 'Memory Usage (%)'})
    fig_mem.add_hline(y=85, line_dash="dash", line_color="red",
                      annotation_text="Threshold (85%)")
    st.plotly_chart(fig_mem, use_container_width=True)

# GC Statistics
st.subheader("🗑️ Garbage Collection Statistics")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("GC Count", metrics['gc_count'])
with col2:
    st.metric("Last GC Time", f"{metrics['last_gc_time']*1000:.1f}ms")
with col3:
    st.metric("Heap Used", "1.2 GB / 2.0 GB")
with col4:
    st.metric("Old Gen Usage", "68%")

# ============================================================================
# SECTION 4: AI INSIGHTS PANEL
# ============================================================================
st.header("🤖 AI Insights & Recommendations")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Analysis Results")
    
    # Root cause analysis
    st.markdown("**🎯 Root Cause Identified:**")
    st.info("Database connection pool exhaustion detected. Thread 'DB-Connection-Pool' has been waiting for 305 seconds.")
    
    # Recommendations
    st.markdown("**💡 Recommendations:**")
    recommendations = [
        "Increase database connection pool size from 10 to 20",
        "Implement connection timeout of 30 seconds",
        "Add connection pool monitoring and alerts",
        "Review and optimize slow database queries"
    ]
    for i, rec in enumerate(recommendations, 1):
        st.markdown(f"{i}. {rec}")
    
    # Confidence score
    st.markdown("**📊 Analysis Confidence:** 87%")
    st.progress(0.87)

with col2:
    st.subheader("Specialist Insights")
    
    with st.expander("🧠 GC Specialist"):
        st.write("✅ GC pause times are within acceptable range")
        st.write("✅ Old generation usage is stable")
        st.write("⚠️ Minor GC frequency slightly elevated")
    
    with st.expander("⚡ CPU Specialist"):
        st.write("⚠️ CPU spike correlates with DB query execution")
        st.write("💡 Consider query optimization")
        st.write("💡 Review connection pool configuration")

# ============================================================================
# SECTION 5: ALERT HISTORY PANEL
# ============================================================================
st.header("🚨 Alert History")

# Sample alert data
alert_data = [
    {
        'Timestamp': (datetime.now() - timedelta(minutes=2)).strftime('%H:%M:%S'),
        'Severity': '🔴 Critical',
        'Alert': 'Hung Thread Detected',
        'Thread': 'DB-Connection-Pool',
        'Status': 'Active'
    },
    {
        'Timestamp': (datetime.now() - timedelta(minutes=5)).strftime('%H:%M:%S'),
        'Severity': '⚠️ Warning',
        'Alert': 'High CPU Usage',
        'Thread': 'N/A',
        'Status': 'Resolved'
    },
    {
        'Timestamp': (datetime.now() - timedelta(minutes=12)).strftime('%H:%M:%S'),
        'Severity': '🔴 Critical',
        'Alert': 'Deadlock Detected',
        'Thread': 'HTTP-Worker-3',
        'Status': 'Resolved'
    },
    {
        'Timestamp': (datetime.now() - timedelta(minutes=18)).strftime('%H:%M:%S'),
        'Severity': '⚠️ Warning',
        'Alert': 'Memory Threshold Exceeded',
        'Thread': 'N/A',
        'Status': 'Resolved'
    }
]

df_alerts = pd.DataFrame(alert_data)
st.dataframe(df_alerts, use_container_width=True, hide_index=True)

# Alert statistics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Alerts (24h)", "24")
with col2:
    st.metric("Active Alerts", "1", delta="-3")
with col3:
    st.metric("Avg Resolution Time", "4.2 min")

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.caption("webMethods Thread Dump Analysis Dashboard v1.0 | Developed by Bhagwan | Last refresh: " + 
           st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S'))
st.success("✅ Dashboard initialized successfully!")

# Made with Bob
