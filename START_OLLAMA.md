# Quick Start: Enable AI Chat

## Current Status
✅ Dashboard is running
✅ Ollama is installed
❌ Ollama service is not running

## To Enable AI Chat - Follow These Steps:

### Step 1: Open a NEW Terminal
- Open a **new PowerShell window** (don't close the dashboard terminal)
- Navigate to your project folder:
```powershell
cd "c:\Bhagwan Kharat\Bobathon_Team\Thread_dump_analysis"
```

### Step 2: Run ONE of these options:

**Option A: Use the Setup Script (Easiest)**
```powershell
.\setup_ollama.bat
```

**Option B: Manual Commands**
```powershell
# First time only - download the model (takes 5-10 minutes)
ollama pull llama2

# Start the service (keep this terminal open)
ollama serve
```

### Step 3: Verify Ollama is Running
You should see output like:
```
Listening on 127.0.0.1:11434
```

### Step 4: Test AI Chat
1. Go back to your browser (http://localhost:8501)
2. Refresh the page (F5)
3. Expand "🤖 Chat with AI Assistant"
4. Ask a question!

## Troubleshooting

### If you see "Ollama service is not available"
- Make sure the Ollama terminal is still open and running
- Check if you see "Listening on 127.0.0.1:11434" in the Ollama terminal
- Try refreshing the dashboard (F5)

### If "ollama" command not found
- Restart your terminal after installing Ollama
- Or add Ollama to PATH manually

### If model download is slow
- This is normal - Llama2 is ~4GB
- Wait for download to complete
- You only need to download once

## Terminal Setup Summary

You should have **2 terminals open**:

**Terminal 1: Dashboard**
```
streamlit run dashboard/app.py
Status: Keep running
```

**Terminal 2: Ollama Service**
```
ollama serve
Status: Keep running
```

## Quick Test

Once Ollama is running, try this in a third terminal:
```powershell
ollama run llama2 "Hello, are you working?"
```

If you get a response, Ollama is working correctly!

---

**Need Help?** Check OLLAMA_SETUP_GUIDE.md for detailed instructions.