# Demo Threshold Configuration

## Overview

Alert thresholds have been reduced to trigger more alerts for demonstration purposes. This makes it easier to see the monitoring system in action without waiting for actual production issues.

## Threshold Changes

### 1. Hung Thread Threshold

**File**: [`shared/models.py`](shared/models.py:59)

**Before**:
```python
def is_hung(self, threshold: int = 300) -> bool:
    """Check if thread is hung (CPU time > threshold seconds)"""
    return self.cpu_time > threshold
```

**After**:
```python
def is_hung(self, threshold: int = 60) -> bool:
    """Check if thread is hung (CPU time > threshold seconds)"""
    return self.cpu_time > threshold
```

**Change**: Reduced from **300 seconds (5 minutes)** to **60 seconds (1 minute)**

**Impact**: 
- Threads running for more than 60 seconds will now be flagged as "hung"
- Will trigger CRITICAL alerts to Slack
- Appears in dashboard "Thread Monitor" section
- Much more sensitive for demo purposes

### 2. Long-Running Thread Threshold

**File**: [`start_monitoring.py`](start_monitoring.py:149)

**Before**:
```python
# Detect long-running threads (>60s CPU time but not marked as hung)
long_running_threads = [t for t in threads if t.cpu_time > 60 and not t.is_hung()]
```

**After**:
```python
# Detect long-running threads (>30s CPU time but not marked as hung)
long_running_threads = [t for t in threads if t.cpu_time > 30 and not t.is_hung()]
```

**Change**: Reduced from **60 seconds** to **30 seconds**

**Impact**:
- Threads running for 30-60 seconds flagged as "long-running"
- Will trigger MEDIUM severity alerts to Slack
- Provides early warning before thread becomes "hung"
- More alerts for demonstration

## Alert Severity Mapping

With the new thresholds:

| CPU Time | Classification | Severity | Alert Type |
|----------|---------------|----------|------------|
| 0-30s | Normal | - | No alert |
| 30-60s | Long-Running | 🟡 MEDIUM | Warning alert |
| 60s+ | Hung | 🔴 CRITICAL | Critical alert |

## Demo Benefits

### More Frequent Alerts
- **Before**: Needed threads running 5+ minutes to trigger alerts
- **After**: Alerts trigger after just 30-60 seconds
- **Result**: Easier to demonstrate monitoring capabilities

### Realistic Scenarios
- Normal application threads often run 30-60 seconds
- Can demonstrate alert flow without artificial delays
- Shows both warning and critical alert levels

### Dashboard Activity
- Thread Monitor section will show more alerts
- Easier to demonstrate alert acknowledgment/resolution
- Better visualization of system capabilities

## Testing the New Thresholds

### 1. Start Monitoring

```bash
python start_monitoring.py
```

The monitor will now detect:
- Threads > 30s as "long-running" (MEDIUM alert)
- Threads > 60s as "hung" (CRITICAL alert)

### 2. Expected Behavior

**First Check (0-30s)**:
```
Thread Statistics:
  Total: 45
  Runnable: 12
  Blocked: 2
  Waiting: 28
  Hung: 0
  Long-Running (>30s): 0
```

**After 30-60s**:
```
Thread Statistics:
  Total: 45
  Runnable: 12
  Blocked: 2
  Waiting: 28
  Hung: 0
  Long-Running (>30s): 3

[INFO] Found 3 long-running thread(s):
  - pool-1-thread-1 (CPU: 45.2s)
  - pool-2-thread-5 (CPU: 38.7s)
  - worker-thread-3 (CPU: 35.1s)

[ALERT] Sending notification to Slack...
🟡 WARNING: 3 Long-Running Thread(s) Detected
```

**After 60s+**:
```
Thread Statistics:
  Total: 45
  Runnable: 12
  Blocked: 2
  Waiting: 28
  Hung: 2
  Long-Running (>30s): 1

[WARNING] Found 2 hung thread(s):
  - pool-1-thread-1 (CPU: 75.3s)
  - pool-2-thread-5 (CPU: 68.9s)

[ALERT] Sending notification to Slack...
🔴 CRITICAL: 2 Hung Thread(s) Detected
```

### 3. Slack Notifications

You should see alerts in Slack like:

**Medium Severity (30-60s)**:
```
🟡 WARNING: 3 Long-Running Thread(s) Detected

Process ID: 12345
CPU Usage: 67.5%
Memory Usage: 78.3%

Long-Running Threads (>30s): 3
  • pool-1-thread-1
    State: RUNNABLE
    CPU Time: 45.20s
    Stack: com.wm.app.b2b.server.ServiceThread.run()
```

**Critical Severity (60s+)**:
```
🔴 CRITICAL: 2 Hung Thread(s) Detected

Process ID: 12345
CPU Usage: 85.2%
Memory Usage: 82.1%

Hung Threads: 2
  • pool-1-thread-1
    State: RUNNABLE
    CPU Time: 75.30s
    Blocked Count: 0
    Stack: com.wm.app.b2b.server.ServiceThread.run()
```

### 4. Dashboard Display

Open http://localhost:8502 and check:

**Thread Monitor Section**:
- Shows all alerts sent to Slack
- Displays severity with color coding
- Includes full thread details
- Action buttons for acknowledgment

**Hung & Long-Running Threads Section**:
- Real-time thread status
- CPU time for each thread
- Stack traces
- Recommendations

## Reverting to Production Thresholds

When moving to production, revert the thresholds:

### 1. Update Hung Thread Threshold

**File**: `shared/models.py` line 59

```python
def is_hung(self, threshold: int = 300) -> bool:  # Change back to 300
    """Check if thread is hung (CPU time > threshold seconds)"""
    return self.cpu_time > threshold
```

### 2. Update Long-Running Threshold

**File**: `start_monitoring.py` line 149

```python
# Change back to 60s
long_running_threads = [t for t in threads if t.cpu_time > 60 and not t.is_hung()]
```

### 3. Update Display Text

**File**: `start_monitoring.py` line 159

```python
print(f"  Long-Running (>60s): {long_running_count}")  # Change back to >60s
```

**File**: `start_monitoring.py` line 240

```python
thread_log_parts.append(f"Long-Running Threads (>60s): {long_running_count}")
```

## Production Recommendations

For production environments:

| Threshold | Recommended Value | Reasoning |
|-----------|------------------|-----------|
| Hung Thread | 300s (5 min) | Avoids false positives from legitimate long operations |
| Long-Running | 120s (2 min) | Early warning without excessive alerts |
| Monitoring Interval | 300s (5 min) | Balance between responsiveness and overhead |

## Summary

**Demo Configuration** (Current):
- ✅ Hung threads: 60 seconds
- ✅ Long-running: 30 seconds
- ✅ More frequent alerts
- ✅ Better for demonstrations

**Production Configuration** (Recommended):
- Hung threads: 300 seconds (5 minutes)
- Long-running: 120 seconds (2 minutes)
- Fewer false positives
- Appropriate for production monitoring

The demo configuration makes it much easier to showcase the monitoring system's capabilities without waiting for actual production issues or creating artificial delays.