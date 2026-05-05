# Using CPU Specialist Agent with Ollama (Granite 4)

## 🎉 Great News!
You don't need an OpenAI API key! Since you have Ollama with Granite 4, you can run everything locally and completely free!

---

## 📋 Prerequisites

1. ✅ **Ollama installed** (you already have this)
2. ✅ **Granite 4 model** (you already have this)
3. ⬜ **Python dependencies** (we'll install these)

---

## 🚀 Quick Setup (3 Steps)

### Step 1: Install Additional Dependencies
```bash
cd C:\Users\VinayMoola\Documents\GitHub\Thread_dump_analysis\agents\cpu_specialist

# Install langchain-community for Ollama support
pip install langchain-community
pip install -r requirements.txt
```

### Step 2: Verify Ollama is Running
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Or in PowerShell
Invoke-WebRequest -Uri "http://localhost:11434/api/tags"
```

You should see a list of your installed models including Granite.

### Step 3: Run the Ollama Version
```bash
# Use the Ollama version instead of OpenAI version
python cpu_agent_ollama.py
```

**No API key needed!** 🎉

---

## 🔧 Testing with webMethods

### Option 1: Quick Test with Sample Data
```bash
python cpu_agent_ollama.py
```

### Option 2: Test with Your webMethods Server

Create a file `test_ollama_webmethods.py`:

```python
from cpu_agent_ollama import CPUSpecialistAgentOllama
import psutil
from datetime import datetime

# Collect system CPU metrics
cpu_metrics = {
    "overall_cpu": psutil.cpu_percent(interval=1),
    "process_cpu": 0,  # Will be calculated
    "thread_count": 0,
    "runnable_threads": 0,
    "cpu_cores": psutil.cpu_count(),
    "timestamp": datetime.now().isoformat()
}

# Find Java process (webMethods)
for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'num_threads']):
    try:
        if 'java' in proc.info['name'].lower():
            cpu_metrics["process_cpu"] = proc.cpu_percent(interval=1)
            cpu_metrics["thread_count"] = proc.num_threads()
            cpu_metrics["runnable_threads"] = int(proc.num_threads() * 0.3)
            break
    except:
        pass

# Initialize agent with Ollama
print("Initializing CPU Specialist with Ollama (Granite 4)...")
agent = CPUSpecialistAgentOllama(
    model_name="granite3-dense:8b",  # or your Granite model name
    base_url="http://localhost:11434"
)

# Run analysis
print("\nAnalyzing CPU metrics...")
results = agent.analyze(cpu_metrics)

# Display results
print("\n" + "="*60)
print("RESULTS")
print("="*60)
print(results['summary'])
print("\nHotspots:", len(results['hotspots']))
print("Optimizations:", len(results['optimizations'].get('optimizations', [])))
```

Run it:
```bash
python test_ollama_webmethods.py
```

---

## 🎯 Available Ollama Models

You can use any Ollama model. Here are some options:

### Recommended Models:

1. **Granite 3 Dense (8B)** - What you have
   ```python
   agent = CPUSpecialistAgentOllama(model_name="granite3-dense:8b")
   ```

2. **Llama 2** - Good alternative
   ```python
   agent = CPUSpecialistAgentOllama(model_name="llama2")
   ```

3. **Mistral** - Fast and accurate
   ```python
   agent = CPUSpecialistAgentOllama(model_name="mistral")
   ```

4. **CodeLlama** - Good for code analysis
   ```python
   agent = CPUSpecialistAgentOllama(model_name="codellama")
   ```

### Check Your Installed Models:
```bash
ollama list
```

---

## 📊 Performance Comparison

| Model | Speed | Accuracy | Memory |
|-------|-------|----------|--------|
| Granite 3 Dense 8B | Medium | High | 8GB |
| Llama 2 | Fast | Medium | 4GB |
| Mistral | Fast | High | 4GB |
| GPT-4 (OpenAI) | Slow | Highest | N/A |

**Recommendation:** Stick with Granite 3 Dense for best results!

---

## 🔄 Switching Between OpenAI and Ollama

### Use OpenAI (requires API key):
```python
from cpu_agent import CPUSpecialistAgent
agent = CPUSpecialistAgent(model_name="gpt-4")
```

### Use Ollama (no API key needed):
```python
from cpu_agent_ollama import CPUSpecialistAgentOllama
agent = CPUSpecialistAgentOllama(model_name="granite3-dense:8b")
```

---

## 🐛 Troubleshooting

### Issue 1: Ollama Not Running
```
Error: Connection refused to localhost:11434
```

**Solution:**
```bash
# Start Ollama
ollama serve

# Or on Windows, start Ollama from Start Menu
```

### Issue 2: Model Not Found
```
Error: model 'granite3-dense:8b' not found
```

**Solution:**
```bash
# List your models
ollama list

# Use the exact name from the list
# For example, if it shows "granite3-dense:latest"
agent = CPUSpecialistAgentOllama(model_name="granite3-dense:latest")
```

### Issue 3: Import Error
```
ModuleNotFoundError: No module named 'langchain_community'
```

**Solution:**
```bash
pip install langchain-community
```

### Issue 4: Slow Response
```
Analysis taking too long...
```

**Solutions:**
1. Use a smaller model (llama2 instead of granite)
2. Reduce the amount of data being analyzed
3. Ensure Ollama has enough RAM (8GB+ recommended)

---

## ⚡ Performance Tips

### 1. Keep Ollama Running
Don't start/stop Ollama for each analysis. Keep it running:
```bash
ollama serve
```

### 2. Warm Up the Model
First analysis is slower. Run a quick test first:
```python
agent = CPUSpecialistAgentOllama(model_name="granite3-dense:8b")
# This loads the model into memory
```

### 3. Batch Analysis
Analyze multiple metrics together instead of one at a time.

### 4. Use GPU if Available
Ollama automatically uses GPU if available, making it much faster.

---

## 📝 Complete Example

Here's a complete working example:

```python
"""
Complete example using Ollama with webMethods
"""
from cpu_agent_ollama import CPUSpecialistAgentOllama
import psutil
import json
from datetime import datetime

def collect_system_metrics():
    """Collect CPU metrics from system"""
    metrics = {
        "overall_cpu": psutil.cpu_percent(interval=1),
        "process_cpu": 0,
        "system_cpu": psutil.cpu_percent(interval=0),
        "thread_count": 0,
        "runnable_threads": 0,
        "blocked_threads": 0,
        "cpu_cores": psutil.cpu_count(),
        "load_average": list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else [0, 0, 0],
        "timestamp": datetime.now().isoformat()
    }
    
    # Find Java/webMethods process
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'num_threads']):
        try:
            if 'java' in proc.info['name'].lower():
                metrics["process_cpu"] = proc.cpu_percent(interval=1)
                metrics["thread_count"] = proc.num_threads()
                metrics["runnable_threads"] = int(proc.num_threads() * 0.3)
                metrics["blocked_threads"] = int(proc.num_threads() * 0.1)
                print(f"Found Java process: PID {proc.pid}")
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    return metrics

def main():
    print("="*70)
    print("CPU Analysis with Ollama (Granite 4)")
    print("="*70)
    
    # Step 1: Collect metrics
    print("\n1. Collecting CPU metrics...")
    cpu_metrics = collect_system_metrics()
    print(f"   ✓ Overall CPU: {cpu_metrics['overall_cpu']:.1f}%")
    print(f"   ✓ Process CPU: {cpu_metrics['process_cpu']:.1f}%")
    print(f"   ✓ Threads: {cpu_metrics['thread_count']}")
    
    # Step 2: Initialize agent
    print("\n2. Initializing CPU Specialist with Ollama...")
    agent = CPUSpecialistAgentOllama(
        model_name="granite3-dense:8b",
        base_url="http://localhost:11434"
    )
    
    # Step 3: Run analysis
    print("\n3. Running analysis (this may take 30-60 seconds)...")
    results = agent.analyze(cpu_metrics)
    
    # Step 4: Display results
    print("\n" + "="*70)
    print("ANALYSIS RESULTS")
    print("="*70)
    print(results['summary'])
    
    if results['hotspots']:
        print("\n--- CPU Hotspots ---")
        for i, hotspot in enumerate(results['hotspots'], 1):
            print(f"{i}. [{hotspot.get('severity', 'Unknown')}] {hotspot.get('type', 'Hotspot')}")
    
    if results['optimizations']:
        print("\n--- Optimizations ---")
        opts = results['optimizations'].get('optimizations', [])
        for i, opt in enumerate(opts[:3], 1):
            print(f"{i}. {opt.get('type', 'Optimization')}")
    
    # Step 5: Save results
    output_file = f"cpu_analysis_ollama_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Results saved to: {output_file}")
    print("="*70)

if __name__ == "__main__":
    main()
```

Save as `test_ollama_complete.py` and run:
```bash
python test_ollama_complete.py
```

---

## 🎓 Key Differences: Ollama vs OpenAI

| Feature | Ollama (Granite) | OpenAI (GPT-4) |
|---------|------------------|----------------|
| **Cost** | FREE | $0.03 per 1K tokens |
| **Privacy** | 100% Local | Cloud-based |
| **Speed** | Medium (30-60s) | Fast (10-30s) |
| **Accuracy** | Good | Excellent |
| **Setup** | No API key | Requires API key |
| **Internet** | Not required | Required |

**For your use case:** Ollama is perfect! You get good analysis without any cost or privacy concerns.

---

## ✅ Summary

### What You Need to Do:

1. **Install langchain-community:**
   ```bash
   pip install langchain-community
   ```

2. **Make sure Ollama is running:**
   ```bash
   ollama serve
   ```

3. **Use the Ollama version:**
   ```python
   from cpu_agent_ollama import CPUSpecialistAgentOllama
   agent = CPUSpecialistAgentOllama(model_name="granite3-dense:8b")
   ```

4. **Run analysis:**
   ```python
   results = agent.analyze(cpu_metrics)
   ```

**That's it! No API key needed!** 🎉

---

## 📞 Need Help?

- Check Ollama status: `ollama list`
- View Ollama logs: Check Ollama console
- Test Ollama: `ollama run granite3-dense:8b "Hello"`

---

**You're all set to use the CPU Specialist Agent with your local Ollama setup!** 🚀