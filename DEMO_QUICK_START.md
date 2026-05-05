# Demo Quick Start - Analyze Your Thread Dump

You have a thread dump file from your server and want to analyze it for the demo. Here's how:

## 📁 Step 1: Place Your Thread Dump File

Copy your thread dump file to this folder:
```
data/thread_dumps/
```

**Example:**
```
data/thread_dumps/my_server_threaddump.txt
data/thread_dumps/integration_server_dump.txt
data/thread_dumps/threaddump_20240115.txt
```

The file can have any name, but should be a `.txt` file.

---

## 🔍 Step 2: Analyze the Thread Dump

### Option A: Analyze Specific File (Recommended for Demo)

```bash
python analyze_collected_dump.py --file data/thread_dumps/YOUR_FILE_NAME.txt
```

**Example:**
```bash
python analyze_collected_dump.py --file data/thread_dumps/my_server_threaddump.txt
```

### Option B: Analyze Most Recent File

```bash
python analyze_collected_dump.py
```

This will automatically analyze the most recently added file in `data/thread_dumps/`.

---

## 📊 Step 3: View Results

### Console Output
The analysis results will be displayed in the console, showing:
- Total thread count
- Thread states (RUNNABLE, BLOCKED, WAITING, etc.)
- Hung threads (>60 seconds CPU time)
- Long-running threads (30-60 seconds)
- Blocked threads
- AI-generated recommendations

### Dashboard (Visual Analysis)

Start the dashboard to see visual charts and detailed analysis:

```bash
python -m streamlit run dashboard/app_enhanced.py --server.port 8502
```

Then open your browser to: **http://localhost:8502**

The dashboard shows:
- System overview with metrics
- Thread state distribution (pie chart)
- Hung and long-running threads
- Detailed thread information
- AI recommendations
- Alert history

---

## 🎯 Demo Workflow

### Quick Demo (5 minutes)

1. **Copy your thread dump:**
   ```bash
   # Copy your file to data/thread_dumps/
   copy "C:\path\to\your\threaddump.txt" "data\thread_dumps\"
   ```

2. **Analyze it:**
   ```bash
   python analyze_collected_dump.py
   ```

3. **Start dashboard:**
   ```bash
   python -m streamlit run dashboard/app_enhanced.py --server.port 8502
   ```

4. **Show in browser:**
   - Open http://localhost:8502
   - Navigate through different sections
   - Show thread analysis
   - Show AI recommendations

### Full Demo (10 minutes)

1. **Prepare:**
   ```bash
   # Copy thread dump
   copy "your_dump.txt" "data\thread_dumps\"
   ```

2. **Analyze:**
   ```bash
   python analyze_collected_dump.py --verbose
   ```

3. **Show console output:**
   - Point out hung threads
   - Explain thread states
   - Highlight AI recommendations

4. **Start dashboard:**
   ```bash
   python -m streamlit run dashboard/app_enhanced.py --server.port 8502
   ```

5. **Dashboard walkthrough:**
   - **System Overview:** Show metrics and health status
   - **Thread Monitor:** Show any alerts
   - **Thread Analysis:** Show hung/long-running threads
   - **Thread Details:** Drill down into specific threads
   - **Recommendations:** Show AI-generated solutions

6. **Show Slack integration (if configured):**
   - Explain how alerts are sent to Slack
   - Show alert format and metadata

---

## 📝 What Gets Analyzed

### Thread States
- **RUNNABLE** - Thread is executing
- **BLOCKED** - Waiting for monitor lock
- **WAITING** - Waiting for notification
- **TIMED_WAITING** - Waiting with timeout

### Issues Detected
- **Hung Threads** - CPU time > 60 seconds
- **Long-Running Threads** - CPU time 30-60 seconds
- **Blocked Threads** - Waiting for locks
- **Deadlocks** - Circular lock dependencies

### AI Analysis
- Root cause identification
- Performance recommendations
- Code optimization suggestions
- Configuration tuning advice

---

## 🎬 Demo Script

### Introduction (1 min)
"We have ThreadHeap Guardian, an AI-powered thread dump analysis system for webMethods Integration Server. Let me show you how it works."

### Collection (1 min)
"We've collected a thread dump from our Integration Server. The system supports multiple collection methods:
- File-based monitoring (production)
- jstack/jcmd (development)
- Manual upload (what we're doing now)"

### Analysis (2 min)
"Let's analyze this thread dump..."
```bash
python analyze_collected_dump.py
```

"As you can see, the system detected:
- X total threads
- Y hung threads (over 60 seconds)
- Z long-running threads (30-60 seconds)
- AI has generated specific recommendations"

### Dashboard (3 min)
"Now let's look at the visual dashboard..."
```bash
python -m streamlit run dashboard/app_enhanced.py --server.port 8502
```

"The dashboard provides:
1. **System Overview** - Health metrics at a glance
2. **Thread Monitor** - Real-time alerts
3. **Thread Analysis** - Detailed breakdown
4. **AI Recommendations** - Actionable insights"

### Integration (2 min)
"The system integrates with:
- **Slack** - Instant alerts for critical issues
- **MCP** - Model Context Protocol for AI agents
- **LangGraph** - Multi-agent workflows
- **Continuous Monitoring** - Automated collection and analysis"

### Conclusion (1 min)
"ThreadHeap Guardian helps you:
- Detect issues before they impact users
- Get AI-powered recommendations
- Visualize thread behavior
- Automate monitoring and alerting"

---

## 🚀 One-Command Demo

For the fastest demo setup:

```bash
# Windows
demo_analyze.bat YOUR_THREAD_DUMP.txt

# Linux/Mac
./demo_analyze.sh YOUR_THREAD_DUMP.txt
```

This will:
1. Copy your file to the right location
2. Analyze it
3. Start the dashboard
4. Open your browser automatically

---

## 📂 File Locations

After analysis, you'll find:

- **Thread Dumps:** `data/thread_dumps/*.txt`
- **Analysis Results:** `data/analysis_results/*.json`
- **Alerts:** `data/alerts/*.json`
- **Logs:** `logs/*.log`

---

## 🔧 Troubleshooting

### "No thread dumps found"
- Make sure your file is in `data/thread_dumps/`
- Check that it's a `.txt` file
- Verify the file contains thread dump data

### "Analysis failed"
- Check the file format (should be standard Java thread dump)
- Look for error messages in the console
- Try with `--verbose` flag for more details

### "Dashboard won't start"
- Make sure port 8502 is not in use
- Try a different port: `--server.port 8503`
- Check that streamlit is installed: `pip install streamlit`

---

## ✅ Ready for Demo!

1. Copy your thread dump to `data/thread_dumps/`
2. Run: `python analyze_collected_dump.py`
3. Start dashboard: `python -m streamlit run dashboard/app_enhanced.py --server.port 8502`
4. Open: http://localhost:8502

**You're all set for the demo!**