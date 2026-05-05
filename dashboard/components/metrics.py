"""
Dashboard Metric Components
Reusable components for displaying metrics and status
"""

import streamlit as st
from typing import Dict, List, Optional


def display_server_health(metrics: Dict):
    """Display server health overview"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Server Health",
            value=metrics.get('server_health', 'Unknown'),
            delta="Operational" if metrics.get('server_health') == 'Healthy' else None
        )
    
    with col2:
        hung = metrics.get('hung_threads', 0)
        st.metric(
            label="Active Threads",
            value=metrics.get('active_threads', 0),
            delta=f"{hung} hung" if hung > 0 else "All normal",
            delta_color="inverse" if hung > 0 else "normal"
        )
    
    with col3:
        cpu = metrics.get('cpu_usage', 0)
        st.metric(
            label="CPU Usage",
            value=f"{cpu:.1f}%",
            delta=f"{cpu - 80:.1f}%" if cpu > 80 else None,
            delta_color="inverse" if cpu > 80 else "normal"
        )
    
    with col4:
        memory = metrics.get('memory_usage', 0)
        st.metric(
            label="Memory Usage",
            value=f"{memory:.1f}%",
            delta=f"{memory - 85:.1f}%" if memory > 85 else None,
            delta_color="inverse" if memory > 85 else "normal"
        )


def display_alert_card(alert: Dict):
    """Display a single alert card"""
    severity = alert.get('severity', 'info').lower()
    
    if severity == 'critical':
        st.error(f"🔴 **{alert.get('title', 'Alert')}**\n\n{alert.get('description', '')}")
    elif severity == 'warning':
        st.warning(f"⚠️ **{alert.get('title', 'Alert')}**\n\n{alert.get('description', '')}")
    else:
        st.info(f"ℹ️ **{alert.get('title', 'Alert')}**\n\n{alert.get('description', '')}")


def display_thread_card(thread: Dict):
    """Display thread information card"""
    status = thread.get('status', 'Unknown')
    
    status_emoji = {
        'Normal': '✅',
        'Hung': '🔴',
        'Blocked': '⚠️',
        'Deadlock': '💀'
    }
    
    emoji = status_emoji.get(status, '❓')
    
    with st.container():
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"**{emoji} {thread.get('name', 'Unknown')}**")
            st.caption(f"ID: {thread.get('thread_id', 'N/A')}")
        
        with col2:
            st.metric("State", thread.get('state', 'Unknown'))
        
        with col3:
            st.metric("CPU Time", f"{thread.get('cpu_time', 0):.1f}ms")


def display_recommendation_list(recommendations: List[str]):
    """Display list of recommendations"""
    st.markdown("**💡 Recommendations:**")
    
    for i, rec in enumerate(recommendations, 1):
        st.markdown(f"{i}. {rec}")


def display_gc_metrics(metrics: Dict):
    """Display GC-specific metrics"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("GC Count", metrics.get('gc_count', 0))
    
    with col2:
        gc_time = metrics.get('last_gc_time', 0) * 1000
        st.metric("Last GC Time", f"{gc_time:.1f}ms")
    
    with col3:
        st.metric("Heap Used", metrics.get('heap_used', 'N/A'))
    
    with col4:
        st.metric("Old Gen Usage", metrics.get('old_gen_usage', 'N/A'))


def display_confidence_score(confidence: float, label: str = "Analysis Confidence"):
    """Display confidence score with progress bar"""
    st.markdown(f"**📊 {label}:** {confidence*100:.0f}%")
    st.progress(confidence)


def display_status_badge(status: str) -> str:
    """Return formatted status badge"""
    status_map = {
        'active': '🔴 Active',
        'resolved': '✅ Resolved',
        'investigating': '🔍 Investigating',
        'pending': '⏳ Pending'
    }
    return status_map.get(status.lower(), status)

# Made with Bob
