# Ollama AI Chat Integration Setup Guide

## Overview
The dashboard now includes an AI-powered chat assistant using Ollama for answering questions about thread dumps, performance issues, and providing recommendations.

## Prerequisites
- Dashboard running successfully
- Internet connection (for initial Ollama download)

## Installation Steps

### Step 1: Install Ollama

#### Windows
1. Download Ollama from: https://ollama.ai/download
2. Run the installer
3. Ollama will be installed and start automatically

#### Linux
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

#### macOS
```bash
brew install ollama
```

### Step 2: Download AI Model

Open a new terminal and run:

```bash
# Download Llama 2 (recommended, ~4GB)
ollama pull llama2

# OR download Mistral (faster, ~4GB)
ollama pull mistral

# OR download CodeLlama (for code-specific questions, ~4GB)
ollama pull codellama
```

### Step 3: Start Ollama Service

```bash
ollama serve
```

This will start Ollama on `http://localhost:11434`

### Step 4: Verify Installation

Test Ollama is working:

```bash
ollama run llama2 "Hello, how are you?"
```

## Using the AI Chat in Dashboard

### Location
The AI Chat Assistant is located right after the "Dashboard initialized successfully!" message in the Overview section.

### Features

1. **Chat Interface**
   - Expandable chat window
   - Conversation history
   - Context-aware responses based on current metrics

2. **Quick Action Buttons**
   - "Analyze hung threads" - Get insights on thread issues
   - "CPU optimization tips" - Performance recommendations
   - "Memory leak detection" - Memory issue guidance

3. **Custom Questions**
   - Type any question about thread dumps
   - Ask about specific threads (e.g., "Why is Thread-2 hung?")
   - Request optimization strategies
   - Get troubleshooting help

### Example Questions

```
- Why are threads getting hung?
- How can I optimize CPU usage?
- What causes memory leaks in webMethods?
- Explain the current thread state
- How do I fix blocked threads?
- What are best practices for thread pool sizing?
- How to interpret GC logs?
- Why is CPU usage high?
```

## Configuration

### Change AI Model

Edit `dashboard/app.py` line ~120:

```python
'model': 'llama2',  # Change to 'mistral', 'codellama', etc.
```

### Adjust Timeout

Edit `dashboard/app.py` line ~125:

```python
timeout=30  # Increase for slower systems
```

### Custom Ollama URL

If Ollama is running on a different host/port:

```python
ollama_response = requests.post(
    'http://your-host:11434/api/generate',
    ...
)
```

## Troubleshooting

### Error: "Cannot connect to Ollama"

**Solution:**
1. Check if Ollama is running: `ollama list`
2. Start Ollama service: `ollama serve`
3. Verify port 11434 is not blocked

### Error: "Model not found"

**Solution:**
```bash
ollama pull llama2
```

### Slow Responses

**Solutions:**
1. Use a smaller model: `ollama pull mistral`
2. Increase timeout in code
3. Ensure sufficient RAM (8GB+ recommended)

### Chat Not Appearing

**Solution:**
1. Refresh the dashboard (F5)
2. Check browser console for errors
3. Verify Streamlit is running latest version

## Performance Tips

1. **Model Selection**
   - `llama2` - Best quality, slower (7B parameters)
   - `mistral` - Good balance (7B parameters)
   - `codellama` - Best for code questions (7B parameters)
   - `llama2:13b` - Higher quality, requires more RAM

2. **System Requirements**
   - Minimum: 8GB RAM
   - Recommended: 16GB RAM
   - GPU: Optional but speeds up responses

3. **Optimization**
   - Keep Ollama running in background
   - Use SSD for faster model loading
   - Close other heavy applications

## Advanced Usage

### Custom System Prompts

Modify the context in `dashboard/app.py`:

```python
context = f"""
You are a webMethods expert specializing in thread dump analysis.

Current System Status:
- Server Health: {metrics['server_health']}
- Active Threads: {metrics['active_threads']}
...

Provide concise, actionable advice.

User Question: {user_input}
"""
```

### Streaming Responses

For real-time streaming (more interactive):

```python
ollama_response = requests.post(
    'http://localhost:11434/api/generate',
    json={
        'model': 'llama2',
        'prompt': context,
        'stream': True  # Enable streaming
    },
    stream=True
)
```

### Multiple Models

Run different models for different purposes:

```python
# Use codellama for technical questions
if 'code' in user_input.lower() or 'stack trace' in user_input.lower():
    model = 'codellama'
else:
    model = 'llama2'
```

## Security Considerations

1. **Local Only**: Ollama runs locally, no data sent to external servers
2. **Network Access**: Only localhost:11434 by default
3. **Data Privacy**: All conversations stay on your machine
4. **Production**: Consider authentication if exposing dashboard externally

## Resources

- Ollama Documentation: https://ollama.ai/docs
- Model Library: https://ollama.ai/library
- GitHub: https://github.com/ollama/ollama
- Community: https://discord.gg/ollama

## Uninstallation

### Remove Ollama

**Windows:**
- Uninstall via Control Panel

**Linux/macOS:**
```bash
# Stop service
sudo systemctl stop ollama

# Remove binary
sudo rm /usr/local/bin/ollama

# Remove models (optional)
rm -rf ~/.ollama
```

## Support

For issues with:
- **Dashboard**: Contact Bhagwan (Dashboard Developer)
- **Ollama**: Visit https://github.com/ollama/ollama/issues
- **Integration**: Check DASHBOARD_IMPLEMENTATION_SUMMARY.md

---

**Version:** 1.0  
**Last Updated:** 2026-05-05  
**Feature Added By:** Bhagwan