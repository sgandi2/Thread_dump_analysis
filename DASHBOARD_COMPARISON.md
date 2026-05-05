# Dashboard Comparison - Port 8501 vs Port 8502

## Overview

Both dashboards are now running and displaying thread dump analysis data from the webMethods Integration Server.

---

## Port 8501 - Original Dashboard
**URL**: http://localhost:8501

### Features:
- ✅ Basic server statistics (Health, Active Threads, CPU, Memory)
- ✅ AI Chat Assistant (Ollama integration)
- ✅ Thread analysis table
- ✅ Thread state distribution pie chart
- ✅ Stack trace viewer
- ✅ Performance metrics charts
- ✅ Sample/mock data display

### Layout:
```
📊 Overview (4 columns)
├── Server Health
├── Active Threads (with hung count)
├── CPU Usage
└── Memory Usage

💬 AI Assistant
└── Chat interface with Ollama

🧵 Thread Analysis
├── Active threads table
├── Thread state pie chart
└── Stack trace expander

📈 Performance Metrics
└── CPU/Memory charts
```

---

## Port 8502 - Enhanced Dashboard ⭐ NEW
**URL**: http://localhost:8502

### Features:
- ✅ **Comprehensive server statistics** (Same as 8501 + more)
- ✅ **Hung/Long-Running threads priority display**
- ✅ **Summary table of all problematic threads**
- ✅ **Detailed root cause analysis for each thread**
- ✅ **AI-powered recommendations**
- ✅ **One-click remediation actions**
- ✅ **4-tab categorized thread view**
- ✅ **Real-time data from actual thread dumps**
- ✅ **Auto-refresh capability**

### Layout:
```
📊 System Overview (8 metrics in 2 rows)
Row 1:
├── Server Health (with operational status)
├── Active Threads (with hung count)
├── CPU Usage
└── Memory Usage

Row 2:
├── Hung Threads (with critical indicator)
├── Blocked Threads (with warning indicator)
├── Deadlocks (with critical indicator)
└── GC Count

🔴 Hung & Long-Running Threads (Priority Section)
├── Alert banner with count
├── Summary table (all problematic threads)
└── Detailed analysis for each thread:
    ├── Thread details (ID, State, CPU time, etc.)
    ├── Stack trace (first 10 lines)
    ├── Root cause analysis
    ├── AI recommendations
    └── Remediation button

🧵 All Threads (4-tab view)
├── 🔴 Hung/Blocked (problematic threads)
├── 🟡 Long-Running (>60s CPU time)
├── ⏸️ Waiting (waiting threads)
└── ✅ Normal (healthy threads)
```

---

## Key Differences

### 1. Server Statistics Display

**Port 8501:**
- 4 metrics in single row
- Basic display

**Port 8502:**
- 8 metrics in 2 rows
- Enhanced with delta indicators
- Color-coded status (Critical/Warning/OK)
- Includes GC count and deadlock detection

### 2. Hung/Long-Running Thread Detection

**Port 8501:**
- Shows sample/mock data
- Basic thread table
- No prioritization

**Port 8502:**
- **Priority section at top** for immediate attention
- **Summary table** showing all problematic threads at once
- Detects both:
  - Hung threads (marked by system)
  - Long-running threads (>60s CPU time)
- Color-coded status icons (🔴 🟡 ⚠️)

### 3. Thread Analysis Depth

**Port 8501:**
- Basic thread information
- Generic stack trace viewer
- No root cause analysis

**Port 8502:**
- **Detailed root cause analysis** for each thread
- **Context-aware recommendations** based on:
  - Thread status (Hung/Blocked/Long-Running)
  - CPU time threshold
  - Stack trace patterns
- **Actionable remediation steps**
- **Risk assessment** for each action

### 4. Thread Categorization

**Port 8501:**
- 3 tabs: Problematic, Waiting, Normal

**Port 8502:**
- **4 tabs** for better organization:
  - 🔴 Hung/Blocked (critical issues)
  - 🟡 Long-Running (potential issues)
  - ⏸️ Waiting (normal waiting)
  - ✅ Normal (healthy threads)

### 5. Data Source

**Port 8501:**
- Uses sample/mock data
- Static display

**Port 8502:**
- **Real-time data** from actual thread dumps
- Loads from `data/thread_dumps/jstack_dump_*.json`
- Integrates with analysis results
- Auto-refresh capability

---

## Thread Detection Criteria

### Hung Threads
- Marked as `is_hung: true` by analyzer
- Typically CPU time > 300 seconds
- State: Usually RUNNABLE or WAITING

### Long-Running Threads (New in 8502)
- CPU time > 60 seconds
- Not marked as hung yet
- **Early warning system** to catch issues before they become critical

### Blocked Threads
- Marked as `is_blocked: true`
- Waiting for locks or resources
- State: BLOCKED

### Waiting Threads
- State: WAITING or TIMED_WAITING
- Normal for many threads
- Not necessarily problematic

---

## Root Cause Analysis Examples

### For Hung Threads (CPU > 300s):
```
🔴 Critical: Long-running operation (>5 minutes)

Possible Reasons:
- Infinite loop in code
- Database query timeout
- External service not responding
- Deadlock situation
- Heavy computation without yield

Recommended Actions:
1. ✅ Review thread stack trace for blocking calls
2. ✅ Check database connection pool status
3. ✅ Verify external service availability
4. ⚠️ Consider killing thread if unresponsive
5. 🔧 Increase timeout values if needed
6. 📊 Monitor for infinite loop patterns
```

### For Long-Running Threads (60s < CPU < 300s):
```
🟡 Long-Running Thread (>1 minute)

Possible Reasons:
- Large data processing
- Complex calculation
- Batch operation in progress
- May become hung if continues

Recommended Actions:
1. ✅ Monitor thread for completion
2. ✅ Check if operation is expected
3. ✅ Review for optimization opportunities
4. ⚠️ Set timeout if operation is stuck
5. 🔧 Consider breaking into smaller tasks
6. 📊 Track CPU time trend
```

### For Blocked Threads:
```
⚠️ Likely Cause: Lock contention

Possible Reasons:
- Waiting for synchronized block
- Database lock
- File system lock
- Resource pool exhaustion

Recommended Actions:
1. ✅ Identify lock holder thread
2. ✅ Check for deadlock conditions
3. ✅ Review synchronized code blocks
4. ⚠️ Consider restarting affected service
5. 🔧 Optimize locking strategy
```

---

## Current System Status

### Latest Thread Dump Analysis
**Collection Time**: 18:07:49 IST  
**Total Threads**: 75

**Thread Distribution**:
- RUNNABLE: 35 (46.7%)
- WAITING: 22 (29.3%)
- Other: 18 (24.0%)

**Health Status**: ✅ HEALTHY
- Hung threads: 0
- Blocked threads: 0
- Deadlocks: 0
- Severity: INFO

**Notable Threads**:
- HTTP handlers: 4 (http-nio-8202, https-jsse-nio-8203)
- GC threads: 15 (G1 garbage collector)
- System threads: 6 (VM Thread, Monitor Deflation, etc.)

---

## Usage Recommendations

### Use Port 8501 When:
- You want to chat with AI assistant about thread issues
- You need basic overview and monitoring
- You want to see performance trend charts
- You're doing exploratory analysis

### Use Port 8502 When:
- **You need to identify hung/long-running threads immediately** ⭐
- You want detailed root cause analysis
- You need actionable remediation recommendations
- You're troubleshooting production issues
- You want real-time data from actual thread dumps
- You need comprehensive server statistics

---

## Quick Access

### Dashboard URLs:
- **Original Dashboard**: http://localhost:8501
- **Enhanced Dashboard**: http://localhost:8502 ⭐ **RECOMMENDED**

### Key Features to Try on Port 8502:
1. Check the **System Overview** section (8 metrics)
2. Look at **Hung & Long-Running Threads** section (priority display)
3. Review the **Summary Table** (all problematic threads at once)
4. Click on any thread expander for **detailed analysis**
5. Check the **4-tab view** for categorized threads
6. Try the **Remediation button** for any problematic thread

---

## Auto-Refresh

Both dashboards support auto-refresh:
- Enable in sidebar: "Auto-refresh" checkbox
- Adjust interval: 5-60 seconds
- Manual refresh: Click "🔄 Refresh Now" button

---

## Integration with Monitoring System

The enhanced dashboard (8502) integrates with:
- ✅ Thread dump collector (every 5 minutes)
- ✅ Analyzer agent (7-step workflow)
- ✅ Remediation agent (6-step workflow)
- ✅ Slack notifications (for critical issues)
- ✅ MCP server (standardized interface)

---

## Summary

**Port 8502 is the recommended dashboard** for production monitoring and troubleshooting because it:

1. **Shows hung/long-running threads prominently** at the top
2. **Provides comprehensive server statistics** (same as 8501 + more)
3. **Offers detailed root cause analysis** for each problematic thread
4. **Gives actionable AI recommendations** based on thread state
5. **Uses real-time data** from actual thread dumps
6. **Categorizes threads** into 4 clear groups for easy navigation
7. **Enables one-click remediation** with risk assessment

Both dashboards are running simultaneously, so you can use whichever fits your current needs!

---

**Generated**: 2026-05-05 18:15 IST  
**Status**: Both dashboards operational ✅