"""
Dashboard Visualization Utilities
Helper functions for creating charts and graphs
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import List, Dict


def create_cpu_chart(data: List[Dict], threshold: float = 80) -> go.Figure:
    """Create CPU usage line chart with threshold"""
    df = pd.DataFrame(data)
    
    fig = px.line(df, x='timestamp', y='value',
                  title='CPU Usage Over Time',
                  labels={'value': 'CPU Usage (%)', 'timestamp': 'Time'})
    
    fig.add_hline(y=threshold, line_dash="dash", line_color="red",
                  annotation_text=f"Threshold ({threshold}%)")
    
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="CPU Usage (%)",
        hovermode='x unified'
    )
    
    return fig


def create_memory_chart(data: List[Dict], threshold: float = 85) -> go.Figure:
    """Create memory usage line chart with threshold"""
    df = pd.DataFrame(data)
    
    fig = px.line(df, x='timestamp', y='value',
                  title='Memory Usage Over Time',
                  labels={'value': 'Memory Usage (%)', 'timestamp': 'Time'})
    
    fig.add_hline(y=threshold, line_dash="dash", line_color="red",
                  annotation_text=f"Threshold ({threshold}%)")
    
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Memory Usage (%)",
        hovermode='x unified'
    )
    
    return fig


def create_thread_state_pie(threads: List[Dict]) -> go.Figure:
    """Create pie chart showing thread state distribution"""
    df = pd.DataFrame(threads)
    state_counts = df['state'].value_counts()
    
    fig = px.pie(values=state_counts.values,
                 names=state_counts.index,
                 title="Thread State Distribution",
                 hole=0.4)
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    
    return fig


def create_thread_timeline(threads: List[Dict]) -> go.Figure:
    """Create timeline showing thread execution"""
    fig = go.Figure()
    
    for i, thread in enumerate(threads):
        fig.add_trace(go.Scatter(
            x=[0, thread.get('cpu_time', 0)],
            y=[thread['name'], thread['name']],
            mode='lines+markers',
            name=thread['name'],
            line=dict(width=10),
            marker=dict(size=10)
        ))
    
    fig.update_layout(
        title="Thread Execution Timeline",
        xaxis_title="CPU Time (ms)",
        yaxis_title="Thread",
        showlegend=False,
        height=400
    )
    
    return fig


def create_gc_chart(gc_data: List[Dict]) -> go.Figure:
    """Create GC pause time chart"""
    df = pd.DataFrame(gc_data)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df['timestamp'],
        y=df['pause_time'],
        name='GC Pause Time',
        marker_color='lightblue'
    ))
    
    fig.update_layout(
        title="Garbage Collection Pause Times",
        xaxis_title="Time",
        yaxis_title="Pause Time (ms)",
        hovermode='x unified'
    )
    
    return fig


def create_alert_severity_chart(alerts: List[Dict]) -> go.Figure:
    """Create bar chart showing alert counts by severity"""
    df = pd.DataFrame(alerts)
    severity_counts = df['severity'].value_counts()
    
    colors = {
        'critical': 'red',
        'warning': 'orange',
        'info': 'blue'
    }
    
    fig = go.Figure(data=[
        go.Bar(
            x=severity_counts.index,
            y=severity_counts.values,
            marker_color=[colors.get(s, 'gray') for s in severity_counts.index]
        )
    ])
    
    fig.update_layout(
        title="Alerts by Severity",
        xaxis_title="Severity",
        yaxis_title="Count",
        showlegend=False
    )
    
    return fig


def format_thread_status(status: str) -> str:
    """Format thread status with emoji"""
    status_map = {
        'Normal': '✅ Normal',
        'Hung': '🔴 Hung',
        'Blocked': '⚠️ Blocked',
        'Deadlock': '💀 Deadlock'
    }
    return status_map.get(status, status)


def format_alert_severity(severity: str) -> str:
    """Format alert severity with emoji"""
    severity_map = {
        'critical': '🔴 Critical',
        'warning': '⚠️ Warning',
        'info': 'ℹ️ Info'
    }
    return severity_map.get(severity.lower(), severity)

# Made with Bob
